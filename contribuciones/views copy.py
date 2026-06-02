"""
Vistas CRUD + exportación CSV para Contribuciones.

Incluye:
- ContribucionListView   : listado paginado con búsqueda y filtros
- ContribucionDetailView : detalle
- ContribucionCreateView : formulario de creación
- ContribucionUpdateView : formulario de edición
- ContribucionDeleteView : confirmación y eliminación
- exportar_csv           : descarga como CSV (requiere login)
"""

import csv
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from .models import Contribucion
from .forms import ContribucionForm, BusquedaForm


# ── Mixin reutilizable: contexto de búsqueda ──────────────────────────────────

class BusquedaMixin:
    """Inyecta el formulario de búsqueda en el contexto."""
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['busqueda_form'] = BusquedaForm(self.request.GET or None)
        return ctx


# ── Listado ────────────────────────────────────────────────────────────────────

class ContribucionListView(LoginRequiredMixin, BusquedaMixin, ListView):
    model              = Contribucion
    template_name      = 'contribuciones/contribucion_list.html'
    context_object_name = 'contribuciones'
    paginate_by        = 15

    def get_queryset(self):
        qs = super().get_queryset().select_related('registrado_por')

        q           = self.request.GET.get('q', '').strip()
        tipo_cuenta = self.request.GET.get('tipo_cuenta', '').strip()
        anio        = self.request.GET.get('anio', '').strip()

        if q:
            qs = qs.filter(
                Q(numero_identidad__icontains=q)        |
                Q(numero_contribuyente_ofa__icontains=q) |
                Q(codigo_zpc__icontains=q)               |
                Q(obligacion_pago__icontains=q)
            )
        if tipo_cuenta:
            qs = qs.filter(tipo_cuenta=tipo_cuenta)
        if anio and anio.isdigit():
            qs = qs.filter(periodo_anio=int(anio))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['total'] = self.get_queryset().count()
        ctx['q']     = self.request.GET.get('q', '')
        return ctx


# ── Detalle ────────────────────────────────────────────────────────────────────

class ContribucionDetailView(LoginRequiredMixin, DetailView):
    model               = Contribucion
    template_name       = 'contribuciones/contribucion_detail.html'
    context_object_name = 'contribucion'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        c   = self.object
        ctx['campos'] = [
            ('Obligación de Pago',         c.obligacion_pago),
            ('Número de Identidad',         c.numero_identidad),
            ('Número de Contribuyente OFA', c.numero_contribuyente_ofa),
            ('Código ZPC',                  c.codigo_zpc),
            ('Período',                     c.periodo_display),
            ('Monto en CUP',                f'{c.monto_cup} CUP'),
            ('Tipo de Cuenta',              c.get_tipo_cuenta_display()),
            ('Registrado por',              c.registrado_por or '—'),
            ('Fecha de Registro',           c.fecha_registro.strftime('%d/%m/%Y %H:%M')),
            ('Última Modificación',         c.fecha_modificacion.strftime('%d/%m/%Y %H:%M')),
        ]
        return ctx


# ── Creación ───────────────────────────────────────────────────────────────────

class ContribucionCreateView(LoginRequiredMixin, CreateView):
    model         = Contribucion
    form_class    = ContribucionForm
    template_name = 'contribuciones/contribucion_form.html'
    success_url   = reverse_lazy('contribuciones:lista')

    def form_valid(self, form):
        form.instance.registrado_por = self.request.user
        messages.success(self.request, '✔ Contribución registrada exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, '✖ Por favor corrija los errores en el formulario.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nueva Contribución'
        ctx['accion'] = 'Registrar'
        return ctx


# ── Edición ────────────────────────────────────────────────────────────────────

class ContribucionUpdateView(LoginRequiredMixin, UpdateView):
    model         = Contribucion
    form_class    = ContribucionForm
    template_name = 'contribuciones/contribucion_form.html'
    success_url   = reverse_lazy('contribuciones:lista')

    def form_valid(self, form):
        messages.success(
            self.request,
            f'✔ Contribución #{self.object.pk} actualizada exitosamente.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, '✖ Por favor corrija los errores en el formulario.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Editar Contribución #{self.object.pk}'
        ctx['accion'] = 'Guardar cambios'
        return ctx


# ── Eliminación ────────────────────────────────────────────────────────────────

class ContribucionDeleteView(LoginRequiredMixin, DeleteView):
    model               = Contribucion
    template_name       = 'contribuciones/contribucion_confirm_delete.html'
    context_object_name = 'contribucion'
    success_url         = reverse_lazy('contribuciones:lista')

    def form_valid(self, form):
        messages.success(
            self.request,
            f'✔ Contribución #{self.object.pk} eliminada correctamente.'
        )
        return super().form_valid(form)


# ── Exportación CSV ────────────────────────────────────────────────────────────

@login_required
def agregar_contribuyente(request):
    if request.method == 'POST':
        form = ContribuyenteForm(request.POST)
        if form.is_valid():
            contribuyente = form.save()
            messages.success(
                request,
                f'Contribuyente {contribuyente.carnet_identidad} registrado correctamente.'
            )
            return redirect('contribuyente:agregar')
        else:
            messages.error(request, 'Corrija los errores marcados en el formulario.')
    else:
        form = ContribuyenteForm()

    return render(request, 'contribuyente/form_contribuyente.html', {'form': form})

def exportar_csv(request):
    """
    Descarga todas las contribuciones (o el filtro activo) como archivo CSV.
    Aplica los mismos filtros que la vista de listado.
    """
    qs = Contribucion.objects.select_related('registrado_por').order_by('-fecha_registro')

    q           = request.GET.get('q', '').strip()
    tipo_cuenta = request.GET.get('tipo_cuenta', '').strip()
    anio        = request.GET.get('anio', '').strip()

    if q:
        qs = qs.filter(
            Q(numero_identidad__icontains=q)        |
            Q(numero_contribuyente_ofa__icontains=q) |
            Q(codigo_zpc__icontains=q)               |
            Q(obligacion_pago__icontains=q)
        )
    if tipo_cuenta:
        qs = qs.filter(tipo_cuenta=tipo_cuenta)
    if anio and anio.isdigit():
        qs = qs.filter(periodo_anio=int(anio))

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="contribuciones.csv"'
    response.write('\ufeff')   # BOM para compatibilidad con Excel

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Obligación de Pago', 'N° Identidad', 'N° Contribuyente OFA',
        'Código ZPC', 'Período', 'Monto CUP', 'Tipo de Cuenta',
        'Registrado por', 'Fecha de Registro',
    ])
    for c in qs:
        writer.writerow([
            c.pk,
            c.obligacion_pago,
            c.numero_identidad,
            c.numero_contribuyente_ofa,
            c.codigo_zpc,
            c.periodo_display,
            c.monto_cup,
            c.get_tipo_cuenta_display(),
            c.registrado_por.username if c.registrado_por else '',
            c.fecha_registro.strftime('%d/%m/%Y %H:%M'),
        ])

    return response
