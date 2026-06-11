from django.db import migrations, models


def migrar_tipo_cuenta(apps, schema_editor):
    Contribucion = apps.get_model('contribuciones', 'Contribucion')
    map_old_to_new = {
        'corriente': 'natural',
        'ahorro': 'natural',
        'especial': 'natural',
    }
    for old_val, new_val in map_old_to_new.items():
        Contribucion.objects.filter(tipo_cuenta=old_val).update(tipo_cuenta=new_val)


class Migration(migrations.Migration):

    dependencies = [
        ('contribuciones', '0004_rename_numero_contribuyente_ofa_contribucion_numero_afiliado'),
    ]

    operations = [
        migrations.RunPython(migrar_tipo_cuenta, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='contribucion',
            name='tipo_cuenta',
            field=models.CharField(choices=[('natural', 'Natural'), ('fiscal', 'Fiscal')], max_length=20, verbose_name='Tipo de Cuenta a Operar'),
        ),
    ]
