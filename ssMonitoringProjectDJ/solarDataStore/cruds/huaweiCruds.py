# Imports for Huawei CRUD operations
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher
from solarData.models import Proyecto, GeneracionEnergiaDiaria, Inversor, GeneracionInversorDiaria
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
