# Imports for Huawei CRUD operations
from solarData.models import Proyecto, GeneracionEnergiaDiaria, Inversor, GeneracionInversorDiaria, Granular, GeneracionGranularDiaria
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

def insert_solis_generacion_sistema_dia(data):
    """
    Insert or update daily generation data fetched from Solis into the database.
    Args:
        data (list): List of dicts as returned by fetch_solis_generacion_sistema_dia
                    Expected format: [{'id': '1298491919449989596', 'collectTime': '2025-06-05', 'PVYield': 17.0}, ...]
    """
    for entry in data:
        station_id = entry.get('id')
        pvyield = entry.get('PVYield')
        collect_time = entry.get('collectTime')
        
        if not (station_id and pvyield is not None and collect_time):
            logger.warning(f"Incomplete entry skipped: {entry}")
            continue  # Skip incomplete entries
        
        # Parse date string (YYYY-MM-DD format) to date object
        try:
            date_obj = datetime.strptime(collect_time, '%Y-%m-%d').date()
        except ValueError as e:
            logger.warning(f"Invalid date format '{collect_time}' in entry: {entry}. Error: {e}")
            continue
        
        # Find the project by station ID
        try:
            proyecto = Proyecto.objects.get(identificador_planta=station_id)
        except Proyecto.DoesNotExist:
            logger.warning(f"Proyecto with identificador_planta '{station_id}' not found. Entry skipped for date {date_obj}.")
            continue
        
        # Insert or update the daily generation record
        obj, created = GeneracionEnergiaDiaria.objects.update_or_create(
            id_proyecto=proyecto,
            fecha_generacion_dia=date_obj,
            defaults={'energia_generada_dia': pvyield}
        )
        
        if created:
            logger.info(f"Created new GeneracionEnergiaDiaria for project {station_id} on {date_obj}: {pvyield} kWh")
        else:
            logger.info(f"Updated GeneracionEnergiaDiaria for project {station_id} on {date_obj}: {pvyield} kWh")

