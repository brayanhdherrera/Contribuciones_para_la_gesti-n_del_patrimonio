import csv
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncMonth
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.http import JsonResponse
from .models import Contribucion, Contribuyente
from .forms import ContribucionForm, BusquedaForm, ContribuyenteForm


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'contribuciones/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        contribuciones = Contribucion.objects.all()
        contribuyentes = Contribuyente.objects.all()

        # ── KPI principales ──
        ctx['total_contribuciones']  = contribuciones.count()
        ctx['total_contribuyentes']  = contribuyentes.count()
        ctx['monto_total']           = contribuciones.aggregate(t=Sum('monto_cup'))['t'] or 0
        ctx['promedio_monto']        = contribuciones.aggregate(p=Sum('monto_cup'))['p'] or 0
        if ctx['total_contribuciones']:
            ctx['promedio_monto'] = round(ctx['promedio_monto'] / ctx['total_contribuciones'], 2)

        # ── Por tipo de cuenta ──
        ctx['por_tipo_cuenta'] = (
            contribuciones.values('tipo_cuenta')
            .annotate(total=Count('id'), monto=Sum('monto_cup'))
            .order_by('-total')
        )

        # ── Últimas contribuciones ──
        ctx['ultimas_contribuciones'] = contribuciones.select_related('registrado_por').order_by('-fecha_registro')[:10]

        # ── Contribuciones por mes (últimos 12) ──
        ctx['por_mes'] = (
            contribuciones.annotate(mes=TruncMonth('fecha_registro'))
            .values('mes')
            .annotate(total=Count('id'), monto=Sum('monto_cup'))
            .order_by('-mes')[:12]
        )

        # ── Por año ──
        ctx['por_anio'] = (
            contribuciones.values('periodo_anio')
            .annotate(total=Count('id'), monto=Sum('monto_cup'))
            .order_by('-periodo_anio')
        )

        return ctx


class BusquedaMixin:
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['busqueda_form'] = BusquedaForm(self.request.GET or None)
        return ctx


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
                Q(nombre__icontains=q)                   |
                Q(numero_identidad__icontains=q)        |
                Q(numero_afiliado__icontains=q) |
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


class ContribucionDetailView(LoginRequiredMixin, DetailView):
    model               = Contribucion
    template_name       = 'contribuciones/contribucion_detail.html'
    context_object_name = 'contribucion'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        c   = self.object
        nombre_label = 'Nombre de la Entidad' if c.tipo_cuenta == 'fiscal' else 'Nombre del Contribuyente'
        ctx['campos'] = [
            (nombre_label,                 c.nombre or '—'),
            ('Obligación de Pago',         c.obligacion_pago),
            ('Número de Identidad',         c.numero_identidad),
            ('Número de Afiliado', c.numero_afiliado),
            ('Código ZPC',                  c.codigo_zpc),
            ('Período',                     c.periodo_display),
            ('Monto en CUP',                f'{c.monto_cup} CUP'),
            ('Tipo de Cuenta',              c.get_tipo_cuenta_display()),
            ('Registrado por',              c.registrado_por or '—'),
            ('Fecha de Registro',           c.fecha_registro.strftime('%d/%m/%Y %H:%M')),
            ('Última Modificación',         c.fecha_modificacion.strftime('%d/%m/%Y %H:%M')),
        ]
        return ctx


class ContribucionCreateView(LoginRequiredMixin, CreateView):
    model         = Contribucion
    form_class    = ContribucionForm
    template_name = 'contribuciones/contribucion_form.html'
    success_url   = reverse_lazy('contribuciones:lista')

    def form_valid(self, form):
        form.instance.registrado_por = self.request.user

        ci = form.cleaned_data.get('numero_identidad', '')
        nombre = form.cleaned_data.get('nombre', '')
        if not Contribuyente.objects.filter(carnet_identidad=ci).exists():
            Contribuyente.objects.create(
                nombre=nombre,
                carnet_identidad=ci,
                numero_contribuyente=form.cleaned_data.get('numero_afiliado', ''),
                codigo_zpc=form.cleaned_data.get('codigo_zpc', ''),
                tipo_cuenta=form.cleaned_data.get('tipo_cuenta', 'natural'),
            )

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


@login_required
def exportar_csv(request):
    qs = Contribucion.objects.select_related('registrado_por').order_by('-fecha_registro')
    q           = request.GET.get('q', '').strip()
    tipo_cuenta = request.GET.get('tipo_cuenta', '').strip()
    anio        = request.GET.get('anio', '').strip()

    if q:
        qs = qs.filter(
            Q(nombre__icontains=q)                   |
            Q(numero_identidad__icontains=q)        |
            Q(numero_afiliado__icontains=q) |
            Q(codigo_zpc__icontains=q)               |
            Q(obligacion_pago__icontains=q)
        )
    if tipo_cuenta:
        qs = qs.filter(tipo_cuenta=tipo_cuenta)
    if anio and anio.isdigit():
        qs = qs.filter(periodo_anio=int(anio))

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="contribuciones.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Nombre/Entidad', 'Obligación de Pago', 'N° Identidad', 'N° Afiliado',
        'Código ZPC', 'Período', 'Monto CUP', 'Tipo de Cuenta',
        'Registrado por', 'Fecha de Registro',
    ])
    for c in qs:
        writer.writerow([
            c.pk,
            c.nombre,
            c.obligacion_pago,
            c.numero_identidad,
            c.numero_afiliado,
            c.codigo_zpc,
            c.periodo_display,
            c.monto_cup,
            c.get_tipo_cuenta_display(),
            c.registrado_por.username if c.registrado_por else '',
            c.fecha_registro.strftime('%d/%m/%Y %H:%M'),
        ])
    return response


# ── Autocomplete Contribuyente ──────────────────────────────────────────────────

@login_required
def buscar_contribuyente(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse([], safe=False)

    contribuyentes = Contribuyente.objects.filter(
        Q(carnet_identidad__icontains=q) | Q(numero_contribuyente__icontains=q)
    )[:10]

    data = [{
        'nombre': c.nombre,
        'carnet_identidad': c.carnet_identidad,
        'numero_contribuyente': c.numero_contribuyente,
        'codigo_zpc': c.codigo_zpc,
        'tipo_cuenta': c.tipo_cuenta,
    } for c in contribuyentes]

    return JsonResponse(data, safe=False)


# ── CRUD Contribuyentes ────────────────────────────────────────────────────────

class ContribuyenteListView(LoginRequiredMixin, ListView):
    model              = Contribuyente
    template_name      = 'contribuciones/contribuyente_list.html'
    context_object_name = 'contribuyentes'
    paginate_by        = 15

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(carnet_identidad__icontains=q) |
                Q(numero_contribuyente__icontains=q) |
                Q(codigo_zpc__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['total'] = self.get_queryset().count()
        return ctx


class ContribuyenteDetailView(LoginRequiredMixin, DetailView):
    model               = Contribuyente
    template_name       = 'contribuciones/contribuyente_detail.html'
    context_object_name = 'contribuyente'


class ContribuyenteCreateView(LoginRequiredMixin, CreateView):
    model         = Contribuyente
    form_class    = ContribuyenteForm
    template_name = 'contribuciones/contribuyente_form.html'
    success_url   = reverse_lazy('contribuciones:contribuyente_lista')

    def form_valid(self, form):
        messages.success(self.request, '✔ Contribuyente registrado exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, '✖ Por favor corrija los errores en el formulario.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nuevo Contribuyente'
        ctx['accion'] = 'Registrar'
        return ctx


class ContribuyenteUpdateView(LoginRequiredMixin, UpdateView):
    model         = Contribuyente
    form_class    = ContribuyenteForm
    template_name = 'contribuciones/contribuyente_form.html'
    success_url   = reverse_lazy('contribuciones:contribuyente_lista')

    def form_valid(self, form):
        messages.success(
            self.request,
            f'✔ Contribuyente #{self.object.pk} actualizado exitosamente.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, '✖ Por favor corrija los errores en el formulario.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Editar Contribuyente #{self.object.pk}'
        ctx['accion'] = 'Guardar cambios'
        return ctx


class ContribuyenteDeleteView(LoginRequiredMixin, DeleteView):
    model               = Contribuyente
    template_name       = 'contribuciones/contribuyente_confirm_delete.html'
    context_object_name = 'contribuyente'
    success_url         = reverse_lazy('contribuciones:contribuyente_lista')

    def form_valid(self, form):
        messages.success(
            self.request,
            f'✔ Contribuyente #{self.object.pk} eliminado correctamente.'
        )
        return super().form_valid(form)
