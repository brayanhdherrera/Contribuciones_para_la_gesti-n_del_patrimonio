from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone
from unfold.admin import ModelAdmin

User = get_user_model()

# ── Catálogos / Choices ────────────────────────────────────────────────────────

MESES = [
    (1,  'Enero'),   (2,  'Febrero'), (3,  'Marzo'),
    (4,  'Abril'),   (5,  'Mayo'),    (6,  'Junio'),
    (7,  'Julio'),   (8,  'Agosto'),  (9,  'Septiembre'),
    (10, 'Octubre'), (11, 'Noviembre'),(12, 'Diciembre'),
]

TIPOS_CUENTA = [
    ('corriente', 'Cuenta Corriente'),
    ('fiscal',    'Cuenta Fiscal'),
]

# ── Validadores ────────────────────────────────────────────────────────────────

solo_numeros = RegexValidator(
    regex=r'^\d+$',
    message='Este campo solo admite dígitos numéricos.'
)

validar_codigo_zpc = RegexValidator(
    regex=r'^[A-Z0-9\-]{3,20}$',
    message='Código ZPC inválido. Use letras mayúsculas, números y guione s (3–20 caracteres).'
)


# ── Modelo principal ───────────────────────────────────────────────────────────

class Contribucion(models.Model):
    """Registro de una contribución al patrimonio."""

    # Datos del contribuyente
    carnet_identidad = models.CharField(
        'Carnet de Identidad',
        max_length=11,
        unique=True,
        validators=[
            RegexValidator(r'^\d{11}$', 'Debe tener exactamente 11 dígitos numéricos.')
        ],
    )
    numero_contribuyente = models.CharField(
        'Número de Contribuyente',
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(r'^\d+$', 'Solo se permiten dígitos numéricos.')
        ],
    )
    codigo_zpc = models.CharField(
        'Código ZPC',
        max_length=20,
        validators=[
            RegexValidator(
                r'^[A-Z0-9\-]{3,20}$',
                'Formato inválido. Use mayúsculas, números y guiones (3–20 caracteres).'
            )
        ],
    )

    # Período de aporte
    periodo_aporte = models.DateField(
        'Período de Aporte',
        help_text='Seleccione el mes y año del aporte (día = 1).',
    )
    periodo_anio = models.PositiveSmallIntegerField(
        'Año del Período',
        validators=[MinValueValidator(2000)],
        help_text='Año del período de aporte. Ej: 2024',
    )

    # Monto_en_CUP
    monto_pagar = models.DecimalField(
        'Monto a Pagar (CUP)',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01, 'El monto debe ser mayor a cero.')],
    )

    # Tipo de cuenta
    tipo_cuenta = models.CharField(
        'Tipo de Cuenta a Operar',
        max_length=20,
        choices=TIPOS_CUENTA,
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name        = 'Contribución'
        verbose_name_plural = 'Contribuciones'
        ordering            = ['-fecha_registro']
        indexes = [
            models.Index(fields=['numero_identidad'],        name='idx_contribucion_identidad'),
            models.Index(fields=['numero_contribuyente_ofa'], name='idx_contribucion_ofa'),
            models.Index(fields=['periodo_anio', 'periodo_mes'], name='idx_contribucion_periodo'),
            models.Index(fields=['tipo_cuenta'],             name='idx_contribucion_cuenta'),
        ]

    def __str__(self):
        return (
            f"#{self.pk} | OFA: {self.numero_contribuyente_ofa} | "
            f"{self.get_periodo_mes_display()} {self.periodo_anio} | "
            f"CUP {self.monto_cup}"
        )

    @property
    def periodo_display(self):
        """Período formateado: 'Enero 2024'."""
        return f"{self.get_periodo_mes_display()} {self.periodo_anio}"
    