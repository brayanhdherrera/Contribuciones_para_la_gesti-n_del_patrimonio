import csv
import io
import json
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.views.generic import ListView, DeleteView, TemplateView
from pdfminer.high_level import extract_text as pdf_extract_text
from .models import ArchivoImportado, MovimientoEstadoCuenta
from .forms import ImportarEstadoCuentaForm, ConfirmarImportacionForm


# ── Helpers ───────────────────────────────────────────────────────────────

def _limpiar_num(texto):
    if texto is None:
        return None
    s = str(texto).strip()
    if not s:
        return None
    s = s.replace('$', '').replace(' ', '').replace(',', '')
    return s


def _parse_decimal(val):
    if val is None:
        return Decimal('0')
    if isinstance(val, Decimal):
        return val
    if isinstance(val, (int, float)):
        return Decimal(str(val))
    try:
        return Decimal(_limpiar_num(val))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0')


def _parse_fecha(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    s = str(val).strip()
    if not s:
        return None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y', '%m/%d/%Y',
                 '%Y%m%d', '%d.%m.%Y', '%Y.%m.%d'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    try:
        parts = re.split(r'[/\-.]', s)
        if len(parts) == 3:
            if len(parts[2]) == 4:
                return date(int(parts[2]), int(parts[1]), int(parts[0]))
            if len(parts[0]) == 4:
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None


def _detectar_y_decodificar(raw):
    for bom, enc in [(b'\xff\xfe', 'utf-16-le'), (b'\xfe\xff', 'utf-16-be'),
                     (b'\xef\xbb\xbf', 'utf-8-sig')]:
        if raw.startswith(bom):
            return raw.decode(enc)
    m = re.search(rb'<\?xml\s+.*?encoding=[\'"]([^\'"]+)[\'"]', raw[:200])
    if m:
        enc = m.group(1).decode().lower().replace('-', '')
        enc_map = {'windows1252': 'cp1252', 'latin1': 'latin-1', 'iso88591': 'latin-1'}
        enc = enc_map.get(enc, enc)
        try:
            return raw.decode(enc)
        except (LookupError, ValueError, UnicodeDecodeError):
            pass
    for enc in ('utf-8', 'cp1252', 'latin-1'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', errors='replace')


# ── Mapas de etiquetas ────────────────────────────────────────────────────

XML_FIELD_MAP = {
    'nit': 'nit',
    'n.i.t': 'nit',
    'n.i.t.': 'nit',
    'producto': 'producto',
    'periodo': 'producto',
    'proxhacienda': 'prox_hacienda',
    'prox_hacienda': 'prox_hacienda',
    'próxima_hacienda': 'prox_hacienda',
    'proximo_hacienda': 'prox_hacienda',
    'vencimiento': 'prox_hacienda',
    'tipo': 'tipo',
    'referencia': 'referencia',
    'ref': 'referencia',
    'descripcion': 'referencia',
    'impuestoinicial': 'impuesto_inicial',
    'impuesto_inicial': 'impuesto_inicial',
    'base_imponible': 'impuesto_inicial',
    'principal': 'principal',
    'recargo': 'recargo',
    'tipoimpuesto': 'tipo_impuesto',
    'tipo_impuesto': 'tipo_impuesto',
    'impuestototal': 'impuesto_total',
    'impuesto_total': 'impuesto_total',
    'total_impuesto': 'impuesto_total',
    'personafiscal': 'persona_fiscal',
    'persona_fiscal': 'persona_fiscal',
    'sucursal': 'sucursal',
    'suc': 'sucursal',
    'ejecutadopor': 'ejecutado_por',
    'ejecutado_por': 'ejecutado_por',
    'ejecutado': 'ejecutado_por',
    'autorizadopor': 'autorizado_por',
    'autorizado_por': 'autorizado_por',
    'autorizado': 'autorizado_por',
}


def _mapear_tag_xml(tag):
    tag_clean = tag.lower().replace('_', '').replace('-', '').replace(' ', '').replace('.', '')
    return XML_FIELD_MAP.get(tag_clean, tag_clean)


def _encontrar_filas_xml(element):
    candidates = []
    for child in element:
        if len(child) > 0:
            children_tags = [c.tag.lower() for c in child]
            if any('nit' in t or 'product' in t or 'refer' in t for t in children_tags):
                candidates.append(child)
    if not candidates:
        for child in element:
            candidates.extend(_encontrar_filas_xml(child))
    return candidates


# ── Vistas ────────────────────────────────────────────────────────────────

class EstadoCuentaListView(LoginRequiredMixin, ListView):
    model = MovimientoEstadoCuenta
    template_name = 'estado_cuenta/estadocuenta_list.html'
    context_object_name = 'movimientos'
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                models.Q(nit__icontains=q) |
                models.Q(referencia__icontains=q) |
                models.Q(persona_fiscal__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = super().get_queryset()
        ctx['total'] = qs.count()
        ctx['total_principal'] = qs.aggregate(t=models.Sum('principal'))['t'] or 0
        ctx['total_impuesto'] = qs.aggregate(t=models.Sum('impuesto_total'))['t'] or 0
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class ImportarEstadoCuentaView(LoginRequiredMixin, TemplateView):
    template_name = 'estado_cuenta/estadocuenta_import.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = ImportarEstadoCuentaForm()
        ctx['confirmar_form'] = ConfirmarImportacionForm()
        return ctx

    def post(self, request, *args, **kwargs):
        if 'confirmar' in request.POST:
            return self._confirmar_importacion(request)
        return self._subir_y_previsualizar(request)

    # ── Paso 1: Subir y previsualizar ─────────────────────────────────────

    def _subir_y_previsualizar(self, request):
        form = ImportarEstadoCuentaForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {
                'form': form,
                'confirmar_form': ConfirmarImportacionForm(),
            })

        archivo = request.FILES['archivo']
        filename = archivo.name
        ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''

        if ext not in ('xml', 'pdf', 'txt', 'csv'):
            messages.error(request, '✖ Formato no soportado. Solo XML, PDF y TXT/CSV.')
            return render(request, self.template_name, {
                'form': form,
                'confirmar_form': ConfirmarImportacionForm(),
            })

        try:
            if ext == 'xml':
                datos = self._extraer_xml(archivo)
            elif ext == 'pdf':
                datos = self._extraer_pdf(archivo)
            else:
                datos = self._extraer_txt(archivo)
        except ValueError as e:
            messages.error(request, f'✖ {e}')
            return render(request, self.template_name, {
                'form': form,
                'confirmar_form': ConfirmarImportacionForm(),
            })

        if not datos:
            messages.warning(request, '⚠ No se encontraron datos válidos en el archivo.')
            return render(request, self.template_name, {
                'form': form,
                'confirmar_form': ConfirmarImportacionForm(),
            })

        archivo.seek(0)
        archivo_obj = ArchivoImportado.objects.create(
            archivo=archivo,
            nombre_original=filename,
            total_movimientos=0,
        )

        datos_json = json.dumps(datos, default=str)
        confirmar_form = ConfirmarImportacionForm(initial={
            'datos': datos_json,
            'nombre_archivo': filename,
            'archivo_id': archivo_obj.pk,
        })

        total_principal = sum(float(_parse_decimal(d.get('principal', 0))) for d in datos)
        total_impuesto = sum(float(_parse_decimal(d.get('impuesto_total', 0))) for d in datos)

        return render(request, self.template_name, {
            'form': ImportarEstadoCuentaForm(),
            'confirmar_form': confirmar_form,
            'datos': datos,
            'filename': filename,
            'total_datos': len(datos),
            'total_principal': total_principal,
            'total_impuesto': total_impuesto,
            'show_preview': True,
        })

    # ── Paso 2: Confirmar importación ─────────────────────────────────────

    def _confirmar_importacion(self, request):
        form = ConfirmarImportacionForm(request.POST)
        if not form.is_valid():
            messages.error(request, '✖ Error al confirmar la importación.')
            return redirect('estado_cuenta:importar')

        datos = form.cleaned_data['datos']
        filename = form.cleaned_data['nombre_archivo']
        archivo_id = form.cleaned_data['archivo_id']

        try:
            archivo_obj = ArchivoImportado.objects.get(pk=archivo_id)
        except ArchivoImportado.DoesNotExist:
            messages.error(request, '✖ El archivo original no se encuentra.')
            return redirect('estado_cuenta:importar')

        creados = errores = 0
        for fila in datos:
            try:
                producto = _parse_fecha(fila.get('producto'))
                prox_hacienda = _parse_fecha(fila.get('prox_hacienda'))
                nit = str(fila.get('nit', '') or '').strip()
                if not producto or not nit:
                    errores += 1
                    continue

                MovimientoEstadoCuenta.objects.create(
                    archivo_origen=archivo_obj,
                    nit=nit[:20],
                    producto=producto,
                    prox_hacienda=prox_hacienda or producto,
                    tipo=int(_parse_decimal(fila.get('tipo', 0))),
                    referencia=str(fila.get('referencia', '') or '')[:255],
                    impuesto_inicial=_parse_decimal(fila.get('impuesto_inicial')),
                    principal=_parse_decimal(fila.get('principal')),
                    recargo=_parse_decimal(fila.get('recargo')),
                    tipo_impuesto=int(_parse_decimal(fila.get('tipo_impuesto', 10))),
                    impuesto_total=_parse_decimal(fila.get('impuesto_total')),
                    persona_fiscal=str(fila.get('persona_fiscal', '') or '')[:255],
                    sucursal=str(fila.get('sucursal', '') or '')[:50],
                    ejecutado_por=str(fila.get('ejecutado_por', '') or '')[:255],
                    autorizado_por=str(fila.get('autorizado_por', '') or '')[:255],
                    archivo_original=filename,
                )
                creados += 1
            except Exception:
                errores += 1

        archivo_obj.total_movimientos = creados
        archivo_obj.save()

        msg = f'✔ Importación completada: {creados} declaraciones guardadas.'
        if errores:
            msg += f' {errores} filas omitidas por errores.'
        messages.success(request, msg)
        return redirect('estado_cuenta:lista')

    # ── Extracción XML ─────────────────────────────────────────────────────

    def _extraer_xml(self, archivo):
        raw = archivo.read()
        content = _detectar_y_decodificar(raw)

        parser = ET.XMLParser()
        try:
            root = ET.fromstring(raw, parser)
        except ET.ParseError:
            try:
                root = ET.fromstring(content, parser)
            except ET.ParseError as e:
                if 'entity' in str(e).lower():
                    content = re.sub(r'&[a-zA-Z]+;', '', content)
                    root = ET.fromstring(content, parser)
                else:
                    raise ValueError(f'Error al parsear XML: {e}')

        rows = _encontrar_filas_xml(root)
        if not rows:
            raise ValueError(
                'No se detectaron registros en el XML. '
                'Se requieren etiquetas como NIT, Producto, Referencia, etc.'
            )

        datos = []
        for row_elem in rows:
            row_raw = {}
            for child in row_elem:
                tag = child.tag.lower()
                text = (child.text or '').strip()
                if not text:
                    continue
                campo = _mapear_tag_xml(tag)
                if campo not in row_raw:
                    row_raw[campo] = text

            producto = _parse_fecha(row_raw.get('producto'))
            nit = (row_raw.get('nit') or '').strip()
            if not producto or not nit:
                continue

            datos.append({
                'nit': nit[:20],
                'producto': producto.strftime('%d/%m/%Y'),
                'prox_hacienda': _parse_fecha(row_raw.get('prox_hacienda')).strftime('%d/%m/%Y') if _parse_fecha(row_raw.get('prox_hacienda')) else '',
                'tipo': int(_parse_decimal(row_raw.get('tipo', 0))),
                'referencia': (row_raw.get('referencia') or '')[:255],
                'impuesto_inicial': float(_parse_decimal(row_raw.get('impuesto_inicial'))),
                'principal': float(_parse_decimal(row_raw.get('principal'))),
                'recargo': float(_parse_decimal(row_raw.get('recargo'))),
                'tipo_impuesto': int(_parse_decimal(row_raw.get('tipo_impuesto', 10))),
                'impuesto_total': float(_parse_decimal(row_raw.get('impuesto_total'))),
                'persona_fiscal': (row_raw.get('persona_fiscal') or '')[:255],
                'sucursal': (row_raw.get('sucursal') or '')[:50],
                'ejecutado_por': (row_raw.get('ejecutado_por') or '')[:255],
                'autorizado_por': (row_raw.get('autorizado_por') or '')[:255],
            })
        return datos

    # ── Extracción PDF ─────────────────────────────────────────────────────

    def _extraer_pdf(self, archivo):
        text = pdf_extract_text(archivo)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        return self._extraer_pdf_por_etiquetas(lines)

    def _extraer_pdf_por_etiquetas(self, lines):
        etiquetas = {
            'nit': ['nit', 'n.i.t'],
            'producto': ['producto', 'periodo'],
            'prox_hacienda': ['próx.hacienda', 'prox.hacienda', 'próxima hacienda',
                              'proximo vencimiento', 'vencimiento'],
            'tipo': ['tipo'],
            'referencia': ['referencia', 'ref', 'descripción'],
            'impuesto_inicial': ['impuesto inicial', 'base imponible', 'impuesto'],
            'principal': ['principal'],
            'recargo': ['recargo'],
            'tipo_impuesto': ['tipo de impuesto', 'tipo impuesto'],
            'impuesto_total': ['impuesto total', 'total impuesto'],
            'persona_fiscal': ['persona fiscal', 'persona'],
            'sucursal': ['sucursal', 'suc'],
            'ejecutado_por': ['ejecutado por', 'ejecutado'],
            'autorizado_por': ['autorizado por', 'autorizado'],
        }

        registros = [{}]
        for line in lines:
            line_lower = line.lower()
            matched = False
            for campo, keywords in etiquetas.items():
                for kw in keywords:
                    if kw in line_lower:
                        valor = line.split(':', 1)[-1].strip() if ':' in line else line
                        registros[-1][campo] = valor
                        matched = True
                        break
                if matched:
                    break

        datos = []
        for rec in registros:
            producto = _parse_fecha(rec.get('producto'))
            nit = (rec.get('nit') or '').strip()
            if not producto or not nit:
                continue
            datos.append({
                'nit': nit[:20],
                'producto': producto.strftime('%d/%m/%Y'),
                'prox_hacienda': _parse_fecha(rec.get('prox_hacienda')).strftime('%d/%m/%Y') if _parse_fecha(rec.get('prox_hacienda')) else '',
                'tipo': int(_parse_decimal(rec.get('tipo', 0))),
                'referencia': (rec.get('referencia') or '')[:255],
                'impuesto_inicial': float(_parse_decimal(rec.get('impuesto_inicial'))),
                'principal': float(_parse_decimal(rec.get('principal'))),
                'recargo': float(_parse_decimal(rec.get('recargo'))),
                'tipo_impuesto': int(_parse_decimal(rec.get('tipo_impuesto', 10))),
                'impuesto_total': float(_parse_decimal(rec.get('impuesto_total'))),
                'persona_fiscal': (rec.get('persona_fiscal') or '')[:255],
                'sucursal': (rec.get('sucursal') or '')[:50],
                'ejecutado_por': (rec.get('ejecutado_por') or '')[:255],
                'autorizado_por': (rec.get('autorizado_por') or '')[:255],
            })
        return datos

    # ── Extracción TXT / CSV ──────────────────────────────────────────────

    def _extraer_txt(self, archivo):
        raw = archivo.read()
        content = _detectar_y_decodificar(raw)
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        if not lines:
            raise ValueError('El archivo TXT/CSV está vacío.')

        separador = self._detectar_separador(lines[0])
        reader = csv.DictReader(io.StringIO(content), delimiter=separador)
        if not reader.fieldnames:
            raise ValueError('No se pudo detectar la cabecera en el archivo TXT/CSV.')

        columnas = {c.lower().replace(' ', '_').replace('-', '_').replace('.', ''): c
                    for c in reader.fieldnames}

        datos = []
        for row in reader:
            row_data = {}
            for campo_normalizado, col_orig in columnas.items():
                campo = _mapear_tag_xml(campo_normalizado)
                val = (row.get(col_orig) or '').strip()
                if val:
                    row_data[campo] = val

            producto = _parse_fecha(row_data.get('producto'))
            nit = (row_data.get('nit') or '').strip()
            if not producto or not nit:
                continue

            datos.append({
                'nit': nit[:20],
                'producto': producto.strftime('%d/%m/%Y'),
                'prox_hacienda': _parse_fecha(row_data.get('prox_hacienda')).strftime('%d/%m/%Y') if _parse_fecha(row_data.get('prox_hacienda')) else '',
                'tipo': int(_parse_decimal(row_data.get('tipo', 0))),
                'referencia': (row_data.get('referencia') or '')[:255],
                'impuesto_inicial': float(_parse_decimal(row_data.get('impuesto_inicial'))),
                'principal': float(_parse_decimal(row_data.get('principal'))),
                'recargo': float(_parse_decimal(row_data.get('recargo'))),
                'tipo_impuesto': int(_parse_decimal(row_data.get('tipo_impuesto', 10))),
                'impuesto_total': float(_parse_decimal(row_data.get('impuesto_total'))),
                'persona_fiscal': (row_data.get('persona_fiscal') or '')[:255],
                'sucursal': (row_data.get('sucursal') or '')[:50],
                'ejecutado_por': (row_data.get('ejecutado_por') or '')[:255],
                'autorizado_por': (row_data.get('autorizado_por') or '')[:255],
            })
        return datos

    def _detectar_separador(self, header):
        for sep in ('|', '\t', ';', ','):
            if sep in header:
                return sep
        return ','


class EliminarMovimientoView(LoginRequiredMixin, DeleteView):
    model = MovimientoEstadoCuenta
    template_name = 'estado_cuenta/estadocuenta_confirm_delete.html'
    context_object_name = 'movimiento'
    success_url = reverse_lazy('estado_cuenta:lista')

    def form_valid(self, form):
        messages.success(
            self.request,
            f'✔ Declaración {self.object.nit} / {self.object.producto} eliminada correctamente.'
        )
        return super().form_valid(form)


@login_required
def eliminar_todos_movimientos(request):
    if request.method == 'POST':
        count = MovimientoEstadoCuenta.objects.count()
        MovimientoEstadoCuenta.objects.all().delete()
        messages.success(request, f'✔ {count} declaraciones eliminadas completamente.')
    return redirect('estado_cuenta:lista')
