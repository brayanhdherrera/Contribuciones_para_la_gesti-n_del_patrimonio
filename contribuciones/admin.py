from django.contrib import admin
from django.http import HttpResponse
from .models import Contribucion, Contribuyente
import csv

def exportar_seleccion_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="contribuciones.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'CI', 'N° Afiliado', 'Código ZPC',
        'Período', 'Monto CUP', 'Tipo de Cuenta', 'Fecha Registro',
    ])
    for c in queryset:
        writer.writerow([
            c.pk, c.numero_identidad, c.numero_afiliado,
            c.codigo_zpc, c.periodo_display, c.monto_cup,
            c.get_tipo_cuenta_display(),
            c.fecha_registro.strftime('%d/%m/%Y %H:%M'),
        ])
    return response
exportar_seleccion_csv.short_description = '📥 Exportar selección a CSV'


@admin.register(Contribucion)
class ContribucionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'numero_afiliado', 'numero_identidad',
        'codigo_zpc', 'periodo_label',
        'monto_cup', 'tipo_cuenta_label', 'fecha_registro',
    )
    list_display_links = ('id', 'numero_afiliado')
    list_per_page      = 25
    search_fields = (
        'numero_identidad', 'numero_afiliado',
        'codigo_zpc',
    )
    list_filter = ('tipo_cuenta', 'periodo_mes', 'periodo_anio', 'fecha_registro')
    ordering = ('-fecha_registro',)
    readonly_fields = ('fecha_registro',)

    fieldsets = (
        ('Datos de la Contribución', {
            'fields': (
                'numero_identidad',
                'numero_afiliado',
                'codigo_zpc',
                'obligacion_pago',
            ),
        }),
        ('Período y Monto', {
            'fields': ('periodo_mes', 'periodo_anio', 'monto_cup', 'tipo_cuenta'),
        }),
        ('Auditoría', {
            'classes': ('collapse',),
            'fields': ('fecha_registro',),
        }),
    )

    actions = [exportar_seleccion_csv]

    def periodo_label(self, obj):
        return obj.periodo_display
    periodo_label.short_description = 'Período'
    periodo_label.admin_order_field = 'periodo_anio'

    def tipo_cuenta_label(self, obj):
        return obj.get_tipo_cuenta_display()
    tipo_cuenta_label.short_description = 'Tipo de Cuenta'
    tipo_cuenta_label.admin_order_field = 'tipo_cuenta'


@admin.register(Contribuyente)
class ContribuyenteAdmin(admin.ModelAdmin):
    list_display = ('id', 'carnet_identidad', 'numero_contribuyente', 'codigo_zpc', 'tipo_cuenta', 'fecha_registro')
    list_display_links = ('id', 'numero_contribuyente')
    list_per_page = 25
    search_fields = ('carnet_identidad', 'numero_contribuyente', 'codigo_zpc')
    list_filter = ('tipo_cuenta', 'fecha_registro')
    ordering = ('-fecha_registro',)
    readonly_fields = ('fecha_registro', 'fecha_modificacion')

    fieldsets = (
        ('Datos', {
            'fields': ('carnet_identidad', 'numero_contribuyente', 'codigo_zpc', 'tipo_cuenta'),
        }),
        ('Auditoría', {
            'classes': ('collapse',),
            'fields': ('fecha_registro', 'fecha_modificacion'),
        }),
    )
