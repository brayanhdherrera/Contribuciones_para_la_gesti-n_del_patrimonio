"""
Admin para Contribucion.
Incluye:
  - list_display, search_fields, list_filter configurados.
  - Fieldsets por secciones lógicas.
  - Acción personalizada: exportar selección a CSV.
  - readonly_fields en campos de auditoría.
"""

import csv
from django.contrib import admin
from django.http import HttpResponse
from .models import Contribucion


def exportar_seleccion_csv(modeladmin, request, queryset):
    """Acción de admin: exporta los registros seleccionados como CSV."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="contribuciones_seleccion.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Obligación de Pago', 'N° Identidad', 'N° OFA',
        'Código ZPC', 'Período', 'Monto CUP', 'Tipo de Cuenta',
        'Registrado por', 'Fecha Registro',
    ])
    for c in queryset.select_related('registrado_por'):
        writer.writerow([
            c.pk, c.obligacion_pago, c.numero_identidad,
            c.numero_contribuyente_ofa, c.codigo_zpc,
            c.periodo_display, c.monto_cup,
            c.get_tipo_cuenta_display(),
            c.registrado_por.username if c.registrado_por else '',
            c.fecha_registro.strftime('%d/%m/%Y %H:%M'),
        ])
    return response

exportar_seleccion_csv.short_description = '📥 Exportar selección a CSV'


@admin.register(Contribucion)
class ContribucionAdmin(admin.ModelAdmin):

    # ── Listado ────────────────────────────────────────────────────────────────
    list_display = (
        'id', 'numero_contribuyente_ofa', 'numero_identidad',
        'obligacion_pago', 'codigo_zpc', 'periodo_label',
        'monto_cup', 'tipo_cuenta_label', 'registrado_por', 'fecha_registro',
    )
    list_display_links = ('id', 'numero_contribuyente_ofa')
    list_per_page      = 25

    # ── Búsqueda ───────────────────────────────────────────────────────────────
    search_fields = (
        'numero_identidad', 'numero_contribuyente_ofa',
        'codigo_zpc', 'obligacion_pago',
    )

    # ── Filtros laterales ──────────────────────────────────────────────────────
    list_filter = ('tipo_cuenta', 'periodo_mes', 'periodo_anio', 'fecha_registro')

    # ── Orden ──────────────────────────────────────────────────────────────────
    ordering = ('-fecha_registro',)

    # ── Campos de solo lectura ─────────────────────────────────────────────────
    readonly_fields = ('registrado_por', 'fecha_registro', 'fecha_modificacion')

    # ── Fieldsets ─────────────────────────────────────────────────────────────
    fieldsets = (
        ('Datos del Contribuyente', {
            'fields': (
                'obligacion_pago',
                'numero_identidad',
                'numero_contribuyente_ofa',
                'codigo_zpc',
            ),
        }),
        ('Período y Monto', {
            'fields': ('periodo_mes', 'periodo_anio', 'monto_cup', 'tipo_cuenta'),
        }),
        ('Auditoría', {
            'classes': ('collapse',),
            'fields': ('registrado_por', 'fecha_registro', 'fecha_modificacion'),
        }),
    )

    # ── Acciones personalizadas ────────────────────────────────────────────────
    actions = [exportar_seleccion_csv]

    # ── Columnas calculadas ────────────────────────────────────────────────────
    def periodo_label(self, obj):
        return obj.periodo_display
    periodo_label.short_description = 'Período'
    periodo_label.admin_order_field = 'periodo_anio'

    def tipo_cuenta_label(self, obj):
        return obj.get_tipo_cuenta_display()
    tipo_cuenta_label.short_description = 'Tipo de Cuenta'
    tipo_cuenta_label.admin_order_field = 'tipo_cuenta'
