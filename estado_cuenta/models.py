from django.db import models


class ArchivoImportado(models.Model):
    archivo = models.FileField(
        'Archivo',
        upload_to='estados_cuenta/',
    )
    nombre_original = models.CharField(
        'Nombre original',
        max_length=255,
    )
    fecha_subida = models.DateTimeField(
        'Fecha de subida',
        auto_now_add=True,
    )
    total_movimientos = models.PositiveIntegerField(
        'Total de movimientos',
        default=0,
    )

    class Meta:
        verbose_name = 'Archivo importado'
        verbose_name_plural = 'Archivos importados'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.nombre_original} ({self.fecha_subida:%d/%m/%Y})"

    def filename(self):
        return self.nombre_original


class MovimientoEstadoCuenta(models.Model):
    archivo_origen = models.ForeignKey(
        ArchivoImportado,
        on_delete=models.CASCADE,
        verbose_name='Archivo de origen',
        related_name='movimientos',
        blank=True,
        null=True,
    )
    nit = models.CharField('NIT', max_length=20)
    producto = models.DateField('Producto')
    prox_hacienda = models.DateField('Próx. Hacienda')
    tipo = models.IntegerField('Tipo', default=0)
    referencia = models.CharField('Referencia', max_length=255)
    impuesto_inicial = models.DecimalField('Impuesto Inicial', max_digits=14, decimal_places=2, default=0)
    principal = models.DecimalField('Principal', max_digits=14, decimal_places=2, default=0)
    recargo = models.DecimalField('Recargo', max_digits=14, decimal_places=2, default=0)
    tipo_impuesto = models.IntegerField('Tipo de Impuesto', default=10)
    impuesto_total = models.DecimalField('Impuesto Total', max_digits=14, decimal_places=2, default=0)
    persona_fiscal = models.CharField('Persona Fiscal', max_length=255)
    sucursal = models.CharField('Sucursal', max_length=50)
    ejecutado_por = models.CharField('Ejecutado por', max_length=255)
    autorizado_por = models.CharField('Autorizado por', max_length=255)
    archivo_original = models.CharField('Archivo de origen', max_length=255, blank=True, default='')
    fecha_importacion = models.DateTimeField('Fecha de importación', auto_now_add=True)

    class Meta:
        verbose_name = 'Declaración de Estado de Cuenta'
        verbose_name_plural = 'Declaraciones de Estado de Cuenta'
        ordering = ['-producto', 'nit']

    def __str__(self):
        return f"{self.nit} | {self.producto} | {self.referencia[:50]}"
