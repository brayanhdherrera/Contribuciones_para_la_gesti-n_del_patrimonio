"""
Modelo Contribucion — núcleo del sistema.

Decisiones de diseño:
  - FK al usuario de Django para trazabilidad completa (quién registró).
  - DecimalField para monto (nunca FloatField en valores monetarios).
  - choices en periodo_mes y tipo_cuenta para integridad de dominio.
  - Índices en campos de búsqueda frecuente (identidad, OFA, período).
  - auto_now en fecha_modificacion para auditoría automática.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone

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
    message='Código ZPC inválido. Use letras mayúsculas, números y guiones (3–20 caracteres).'
)


# ── Modelo principal ───────────────────────────────────────────────────────────

class Contribucion(models.Model):
    """Registro de una contribución al patrimonio."""

    # Datos del contribuyente
    obligacion_pago = models.CharField(
        'Obligación de Pago',
        max_length=100,
        help_text='Descripción o código de la obligación de pago.',
    )
    numero_identidad = models.CharField(
        'Número de Identidad',
        max_length=11,
        validators=[solo_numeros],
        help_text='CI cubano: exactamente 11 dígitos.',
    )
    numero_contribuyente_ofa = models.CharField(
        'Número de Contribuyente OFA',
        max_length=50,
        validators=[solo_numeros],
        help_text='Número asignado por la Oficina de la Administración Fiscal.',
    )
    codigo_zpc = models.CharField(
        'Código ZPC',
        max_length=20,
        validators=[validar_codigo_zpc],
        help_text='Zona de Planificación y Control. Ej: ZPC-001',
    )

    # Período de aporte
    periodo_mes = models.PositiveSmallIntegerField(
        'Mes del Período',
        choices=MESES,
    )
    periodo_anio = models.PositiveSmallIntegerField(
        'Año del Período',
        validators=[MinValueValidator(2000)],
        help_text='Año del período de aporte. Ej: 2024',
    )

    # Monto
    monto_cup = models.DecimalField(
        'Monto en CUP',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Monto en pesos cubanos. Ej: 1500.00',
    )

    # Tipo de cuenta
    tipo_cuenta = models.CharField(
        'Tipo de Cuenta a Operar',
        max_length=20,
        choices=TIPOS_CUENTA,
    )

    # Auditoría
    registrado_por = models.ForeignKey(
        User,
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
