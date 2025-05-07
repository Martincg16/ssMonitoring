# Imports for Huawei CRUD operations
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher
from solarData.models import Proyecto, GeneracionEnergiaDiaria, Inversor, GeneracionInversorDiaria, Granular, GeneracionGranularDiaria
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

def insert_huawei_generacion_sistema_dia(data):
    """
    Insert or update daily generation data fetched from Huawei into the database.
    Args:
        data (list): List of dicts as returned by fetch_huawei_generacion_sistema_dia
    """
    for entry in data:
        station_code = entry.get('stationCode')
        pvyield = entry.get('PVYield')
        collect_time = entry.get('collectTime')
        if not (station_code and pvyield is not None and collect_time):
            continue  # Skip incomplete entries
        date_obj = datetime.fromtimestamp(collect_time / 1000, tz=timezone.utc).date()
        try:
            proyecto = Proyecto.objects.get(identificador_planta=station_code)
        except Proyecto.DoesNotExist:
            logger.warning(f"Proyecto with identificador_planta '{station_code}' not found. Entry skipped for date {date_obj}.")
            continue
        obj, created = GeneracionEnergiaDiaria.objects.update_or_create(
            id_proyecto=proyecto,
            fecha_generacion_dia=date_obj,
            defaults={'energia_generada_dia': pvyield}
        )

def insert_huawei_generacion_inversor_dia(data):
    """
    Insert or update daily inverter generation data fetched from Huawei into the database.
    Args:
        data (list): List of dicts as returned by fetch_huawei_generacion_inversor_dia
    """
    for entry in data:
        identificador_inversor = entry.get('identificador_inversor')
        product_power = entry.get('product_power')
        collect_time = entry.get('collectTime')
        if not (identificador_inversor and product_power is not None and collect_time):
            continue  # Skip incomplete entries
        date_obj = datetime.fromtimestamp(collect_time / 1000, tz=timezone.utc).date()
        try:
            inversor = Inversor.objects.get(identificador_inversor=identificador_inversor)
        except Inversor.DoesNotExist:
            logger.warning(f"Inversor with identificador_inversor '{identificador_inversor}' not found. Entry skipped for date {date_obj}.")
            continue
        obj, created = GeneracionInversorDiaria.objects.update_or_create(
            id_proyecto=inversor.id_proyecto,
            id_inversor=inversor,
            fecha_generacion_inversor_dia=date_obj,
            defaults={'energia_generada_inversor_dia': product_power}
        )

def insert_huawei_generacion_granular_dia(mppt_energy_dict, fecha_generacion):
    """
    Insert or update daily MPPT (granular) generation data fetched from Huawei into the database.
    Args:
        mppt_energy_dict (dict): { 'NE=...': { 'mppt_1_cap': value, ... }, ... }
        fecha_generacion (date): date object for the day of generation
    """
    for serial, mppts in mppt_energy_dict.items():
        try:
            inversor = Inversor.objects.get(identificador_inversor=serial)
        except Inversor.DoesNotExist:
            print(f"[WARN] Inversor with identificador_inversor '{serial}' not found. Entry skipped for date {fecha_generacion}.")
            logger.warning(f"Inversor with identificador_inversor '{serial}' not found. Entry skipped for date {fecha_generacion}.")
            continue
        proyecto = inversor.id_proyecto
        for mppt_key, energia in mppts.items():
            # Extract mppt number from key (e.g., 'mppt_1_cap' -> 1)
            try:
                mppt_number = int(mppt_key.split('_')[1])
            except (IndexError, ValueError):
                print(f"[WARN] Could not extract MPPT number from key '{mppt_key}' for inverter {serial}. Skipping.")
                logger.warning(f"Could not extract MPPT number from key '{mppt_key}' for inverter {serial}. Skipping.")
                continue
            serial_granular = f"{serial}-{mppt_number}"  # e.g., 'NE=35759038-1'
            granular, created_granular = Granular.objects.get_or_create(
                id_proyecto=proyecto,
                id_inversor=inversor,
                serial_granular=serial_granular,
                defaults={"tipo_granular": "MPPT"}
            )
            if created_granular:
                print(f"[INFO] Created new Granular: {serial_granular} for inverter {serial}.")
            obj, created = GeneracionGranularDiaria.objects.update_or_create(
                id_proyecto=proyecto,
                id_inversor=inversor,
                id_granular=granular,
                fecha_generacion_granular_dia=fecha_generacion,
                defaults={"energia_generada_granular_dia": energia}
            )
