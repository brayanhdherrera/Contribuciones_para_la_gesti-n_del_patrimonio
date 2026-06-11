from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone
from django.conf import settings

User = get_user_model()

MESES = [
    (1,  'Enero'),   (2,  'Febrero'), (3,  'Marzo'),
    (4,  'Abril'),   (5,  'Mayo'),    (6,  'Junio'),
    (7,  'Julio'),   (8,  'Agosto'),  (9,  'Septiembre'),
    (10, 'Octubre'), (11, 'Noviembre'),(12, 'Diciembre'),
]

TIPO_CUENTA = [
    ('natural', 'Natural'),
    ('fiscal',  'Fiscal'),
]

OBLIGACION_PAGO_CHOICES = [
    ('contribucion', 'Contribución'),
    ('donacion', 'Donación'),
]


solo_numeros = RegexValidator(
    regex=r'^\d+$',
    message='Este campo solo admite dígitos numéricos.'
)

validar_codigo_zpc = RegexValidator(
    regex=r'^[A-Z0-9\-]{3,20}$',
    message='Código ZPC inválido. Use letras mayúsculas, números y guiones (3–20 caracteres).'
)


class Contribuyente(models.Model):
    nombre = models.CharField(
        'Nombre del Contribuyente',
        max_length=255,
        blank=True,
        default='',
        help_text='Nombre completo (persona natural) o nombre de la entidad (cuenta fiscal).',
    )
    carnet_identidad = models.CharField(
        'Carnet de Identidad',
        max_length=11,
        unique=True,
        validators=[RegexValidator(r'^\d{11}$', 'Debe tener exactamente 11 dígitos numéricos.')],
    )
    numero_contribuyente = models.CharField(
        'Número de Contribuyente',
        max_length=20,
        unique=True,
        validators=[solo_numeros],
    )
    codigo_zpc = models.CharField(
        'Código ZPC',
        max_length=20,
        validators=[validar_codigo_zpc],
    )
    tipo_cuenta = models.CharField(
        'Tipo de Cuenta',
        max_length=10,
        choices=[('natural', 'Natural'), ('fiscal', 'Fiscal')],
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Contribuyente'
        verbose_name_plural = 'Contribuyentes'
        ordering            = ['-fecha_registro']

    def __str__(self):
        return f"{self.numero_contribuyente} - {self.nombre or self.carnet_identidad}"


class Contribucion(models.Model):
    nombre = models.CharField(
        'Nombre del Contribuyente',
        max_length=255,
        blank=True,
        default='',
        help_text='Nombre completo (persona natural) o nombre de la entidad (cuenta fiscal).',
    )
    obligacion_pago = models.CharField(
        'Obligación de Pago',
        max_length=100,
        choices=OBLIGACION_PAGO_CHOICES,
    )
    numero_identidad = models.CharField(
        'Número de Identidad',
        max_length=11,
        validators=[solo_numeros],
        help_text='CI cubano: exactamente 11 dígitos.',
    )
    numero_afiliado = models.CharField(
        'Número de Afiliado',
        max_length=10,
        help_text='Máximo 10 caracteres. Puede incluir números, letras y caracteres especiales.',
    )
    codigo_zpc = models.CharField(
        'Código ZPC',
        max_length=20,
        validators=[validar_codigo_zpc],
        help_text='Zona de Planificación y Control. Ej: ZPC-001',
    )
    periodo_mes = models.PositiveSmallIntegerField(
        'Mes del Período',
        choices=MESES,
    )
    periodo_anio = models.PositiveSmallIntegerField(
        'Año del Período',
        validators=[MinValueValidator(2000)],
        help_text='Año del período de aporte. Ej: 2024',
    )
    monto_cup = models.DecimalField(
        'Monto en CUP',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Monto en pesos cubanos. Ej: 1500.00',
    )
    tipo_cuenta = models.CharField(
        'Tipo de Cuenta a Operar',
        max_length=20,
        choices=TIPO_CUENTA,
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contribuciones',
        verbose_name='Registrado por',
    )
    fecha_registro = models.DateTimeField(
        'Fecha de Registro',
        default=timezone.now,
        editable=False,
    )
    fecha_modificacion = models.DateTimeField(
        'Última Modificación',
        auto_now=True,
    )

    class Meta:
        verbose_name        = 'Contribución'
        verbose_name_plural = 'Contribuciones'
        ordering            = ['-fecha_registro']
        indexes = [
            models.Index(fields=['numero_identidad'],         name='idx_contribucion_identidad'),
            models.Index(fields=['numero_afiliado'], name='idx_contribucion_afiliado'),
            models.Index(fields=['periodo_anio', 'periodo_mes'], name='idx_contribucion_periodo'),
            models.Index(fields=['tipo_cuenta'],              name='idx_contribucion_cuenta'),
        ]

    def __str__(self):
        return (
            f"#{self.pk} | {self.nombre or self.numero_afiliado} | "
            f"{self.get_periodo_mes_display()} {self.periodo_anio} | "
            f"CUP {self.monto_cup}"
        )

    @property
    def periodo_display(self):
        return f"{self.get_periodo_mes_display()} {self.periodo_anio}"
