from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contribuciones', '0003_alter_contribucion_obligacion_pago'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contribucion',
            old_name='numero_contribuyente_ofa',
            new_name='numero_afiliado',
        ),
        migrations.AlterField(
            model_name='contribucion',
            name='numero_afiliado',
            field=models.CharField(
                help_text='Máximo 10 caracteres. Puede incluir números, letras y caracteres especiales.',
                max_length=10,
                verbose_name='Número de Afiliado',
            ),
        ),
        migrations.RemoveIndex(
            model_name='contribucion',
            name='idx_contribucion_ofa',
        ),
        migrations.AddIndex(
            model_name='contribucion',
            index=models.Index(fields=['numero_afiliado'], name='idx_contribucion_afiliado'),
        ),
    ]
