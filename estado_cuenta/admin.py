from django.contrib import admin
from .models import ArchivoImportado, MovimientoEstadoCuenta


@admin.register(ArchivoImportado)
class ArchivoImportadoAdmin(admin.ModelAdmin):
    list_display = ('nombre_original', 'fecha_subida', 'total_movimientos')
    list_filter = ('fecha_subida',)
    search_fields = ('nombre_original',)
    date_hierarchy = 'fecha_subida'
    readonly_fields = ('fecha_subida',)


@admin.register(MovimientoEstadoCuenta)
class MovimientoEstadoCuentaAdmin(admin.ModelAdmin):
    list_display = ('nit', 'producto', 'referencia', 'principal', 'impuesto_total', 'sucursal', 'archivo_original')
    list_filter = ('producto', 'tipo_impuesto')
    search_fields = ('nit', 'referencia', 'persona_fiscal')
    date_hierarchy = 'producto'
