from django.conf import settings
import django.core.validators
import django.utils.timezone
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contribucion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID')),
                ('obligacion_pago', models.CharField(
                    help_text='Descripción o código de la obligación de pago.',
                    max_length=100, verbose_name='Obligación de Pago')),
                ('numero_identidad', models.CharField(
                    help_text='CI cubano: exactamente 11 dígitos.',
                    max_length=11,
                    validators=[django.core.validators.RegexValidator(
                        message='Este campo solo admite dígitos numéricos.',
                        regex='^\\d+$')],
                    verbose_name='Número de Identidad')),
                ('numero_contribuyente_ofa', models.CharField(
                    help_text='Número asignado por la Oficina de la Administración Fiscal.',
                    max_length=50,
                    validators=[django.core.validators.RegexValidator(
                        message='Este campo solo admite dígitos numéricos.',
                        regex='^\\d+$')],
                    verbose_name='Número de Contribuyente OFA')),
                ('codigo_zpc', models.CharField(
                    help_text='Zona de Planificación y Control. Ej: ZPC-001',
                    max_length=20,
                    validators=[django.core.validators.RegexValidator(
                        message='Código ZPC inválido. Use letras mayúsculas, números y guiones (3–20 caracteres).',
                        regex='^[A-Z0-9\\-]{3,20}$')],
                    verbose_name='Código ZPC')),
                ('periodo_mes', models.PositiveSmallIntegerField(
                    choices=[(1,'Enero'),(2,'Febrero'),(3,'Marzo'),(4,'Abril'),
                             (5,'Mayo'),(6,'Junio'),(7,'Julio'),(8,'Agosto'),
                             (9,'Septiembre'),(10,'Octubre'),(11,'Noviembre'),(12,'Diciembre')],
                    verbose_name='Mes del Período')),
                ('periodo_anio', models.PositiveSmallIntegerField(
                    help_text='Año del período de aporte. Ej: 2024',
                    validators=[django.core.validators.MinValueValidator(2000)],
                    verbose_name='Año del Período')),
                ('monto_cup', models.DecimalField(
                    decimal_places=2, max_digits=12,
                    help_text='Monto en pesos cubanos. Ej: 1500.00',
                    validators=[django.core.validators.MinValueValidator(0.01)],
                    verbose_name='Monto en CUP')),
                ('tipo_cuenta', models.CharField(
                    choices=[('corriente','Cuenta Corriente'),('ahorro','Cuenta de Ahorro'),
                             ('fiscal','Cuenta Fiscal'),('especial','Cuenta Especial')],
                    max_length=20, verbose_name='Tipo de Cuenta a Operar')),
                ('registrado_por', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='contribuciones',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Registrado por')),
                ('fecha_registro', models.DateTimeField(
                    default=django.utils.timezone.now,
                    editable=False, verbose_name='Fecha de Registro')),
                ('fecha_modificacion', models.DateTimeField(
                    auto_now=True, verbose_name='Última Modificación')),
            ],
            options={
                'verbose_name': 'Contribución',
                'verbose_name_plural': 'Contribuciones',
                'ordering': ['-fecha_registro'],
            },
        ),
        migrations.AddIndex(
            model_name='contribucion',
            index=models.Index(fields=['numero_identidad'],
                               name='idx_contribucion_identidad'),
        ),
        migrations.AddIndex(
            model_name='contribucion',
            index=models.Index(fields=['numero_contribuyente_ofa'],
                               name='idx_contribucion_ofa'),
        ),
        migrations.AddIndex(
            model_name='contribucion',
            index=models.Index(fields=['periodo_anio', 'periodo_mes'],
                               name='idx_contribucion_periodo'),
        ),
        migrations.AddIndex(
            model_name='contribucion',
            index=models.Index(fields=['tipo_cuenta'],
                               name='idx_contribucion_cuenta'),
        ),
    ]
