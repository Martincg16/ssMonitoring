from django.db import migrations

HITOS = [
    # (codigo, nombre, fase, secuencia, tiene_fecha_reportada)
    # --- Fase 1 ---
    ('inicio_de_proyecto',       'Inicio de Proyecto',          1, 1,  False),
    ('radicado_or',              'Radicado OR',                 1, 2,  True),
    ('expedicion_de_polizas',    'Expedición de Pólizas',       1, 3,  False),
    ('aprobacion_or',            'Aprobación del OR',           1, 4,  True),
    ('recepcion_anticipo_1',     'Recepción Anticipo 1',        1, 5,  False),
    ('compra_de_equipos',        'Compra de Equipos',           1, 6,  False),
    # --- Fase 2 ---
    ('recepcion_equipos_en_sitio', 'Recepción de Equipos en Sitio', 2, 7, False),
    ('inicio_de_instalacion',    'Inicio de Instalación',       2, 8,  True),
    ('fin_de_instalacion',       'Fin de Instalación',          2, 9,  True),
    # --- Fase 3 ---
    ('certificacion_retie',      'Certificación RETIE',         3, 10, True),
    ('visita_or',                'Visita del OR',               3, 11, False),
    ('cambio_de_medidor',        'Cambio de Medidor',           3, 12, False),
    ('finalizacion_de_proyecto', 'Finalización de Proyecto',    3, 13, False),
]


def seed_tipo_hito(apps, schema_editor):
    TipoHito = apps.get_model('ops', 'TipoHito')
    for codigo, nombre, fase, secuencia, tiene_fecha_reportada in HITOS:
        TipoHito.objects.get_or_create(
            codigo=codigo,
            defaults={
                'nombre': nombre,
                'fase': fase,
                'secuencia': secuencia,
                'tiene_fecha_reportada': tiene_fecha_reportada,
            }
        )


def unseed_tipo_hito(apps, schema_editor):
    TipoHito = apps.get_model('ops', 'TipoHito')
    TipoHito.objects.filter(codigo__in=[h[0] for h in HITOS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ops', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_tipo_hito, unseed_tipo_hito),
    ]
