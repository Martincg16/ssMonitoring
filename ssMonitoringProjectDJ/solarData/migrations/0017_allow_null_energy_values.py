from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('solarData', '0016_alter_proyecto_id_ciudad'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generacionenergiadiaria',
            name='energia_generada_dia',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True, verbose_name='energía generada en el día'),
        ),
        migrations.AlterField(
            model_name='generacioninversordiaria',
            name='energia_generada_inversor_dia',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True, verbose_name='energía por inversor generada en el día'),
        ),
        migrations.AlterField(
            model_name='generaciongranulardiaria',
            name='energia_generada_granular_dia',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True, verbose_name='energía por mppt generada en el día'),
        ),
    ]
