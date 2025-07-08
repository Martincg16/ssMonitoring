# Imports for Solis CRUD operations
from solarData.models import Proyecto, GeneracionEnergiaDiaria, Inversor, GeneracionInversorDiaria, Granular, GeneracionGranularDiaria
from datetime import datetime, timezone
import logging
import json

logger = logging.getLogger('solis_store')

def insert_solis_generacion_sistema_dia(data):
    """
    Insert or update daily generation data fetched from Solis into the database.
    Args:
        data (list): List of dicts as returned by fetch_solis_generacion_sistema_dia
                    Expected format: [{'id': '1298491919449989596', 'collectTime': '2025-06-05', 'PVYield': 17.0}, ...]
    """
    logger.info(f"|SolisStore|insert_solis_generacion_sistema_dia| Starting system generation data insertion for {len(data)} entries")
    
    # Log the data being processed for debugging
    try:
        data_json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        # Truncate if very large (>3000 chars) to avoid log bloat
        if len(data_json_str) > 3000:
            truncated_data = data_json_str[:3000] + "... [TRUNCATED]"
            logger.info(f"|SolisStore|insert_solis_generacion_sistema_dia| Data being processed (TRUNCATED): {truncated_data}")
        else:
            logger.info(f"|SolisStore|insert_solis_generacion_sistema_dia| Data being processed: {data_json_str}")
    except Exception as e:
        logger.warning(f"|SolisStore|insert_solis_generacion_sistema_dia| Could not serialize data for logging: {e}")
    
    successful_inserts = 0
    skipped_entries = 0
    
    for entry in data:
        station_id = entry.get('id')
        pvyield = entry.get('PVYield')
        collect_time = entry.get('collectTime')
        
        if not (station_id and pvyield is not None and collect_time):
            logger.warning(f"|SolisStore|insert_solis_generacion_sistema_dia| Incomplete entry skipped: {entry}")
            skipped_entries += 1
            continue  # Skip incomplete entries
        
        # Parse date string (YYYY-MM-DD format) to date object
        try:
            date_obj = datetime.strptime(collect_time, '%Y-%m-%d').date()
        except ValueError as e:
            logger.warning(f"|SolisStore|insert_solis_generacion_sistema_dia| Invalid date format '{collect_time}' in entry: {entry}. Error: {e}")
            skipped_entries += 1
            continue
        
        # Find the project by station ID
        try:
            proyecto = Proyecto.objects.get(identificador_planta=station_id)
        except Proyecto.DoesNotExist:
            logger.warning(f"|SolisStore|insert_solis_generacion_sistema_dia| Proyecto with identificador_planta '{station_id}' not found. Entry skipped for date {date_obj}.")
            skipped_entries += 1
            continue
        
        # Insert or update the daily generation record
        obj, created = GeneracionEnergiaDiaria.objects.update_or_create(
            id_proyecto=proyecto,
            fecha_generacion_dia=date_obj,
            defaults={'energia_generada_dia': pvyield}
        )
        
        if created:
            logger.info(f"|SolisStore|insert_solis_generacion_sistema_dia| Created new GeneracionEnergiaDiaria for project {station_id} on {date_obj}: {pvyield} kWh")
        else:
            logger.info(f"|SolisStore|insert_solis_generacion_sistema_dia| Updated GeneracionEnergiaDiaria for project {station_id} on {date_obj}: {pvyield} kWh")
        
        successful_inserts += 1
    
    logger.info(f"|SolisStore|insert_solis_generacion_sistema_dia| Completed system generation data insertion: {successful_inserts} successful, {skipped_entries} skipped")


def insert_solis_generacion_inversor_dia(data):
    """
    Insert or update daily inverter generation data fetched from Solis into the database.
    Args:
        data (dict): Dict as returned by fetch_solis_generacion_un_inversor_dia
                    Expected format: {'identificador_inversor': '1308675217948062296', 'collectTime': '18-06-2025', 'PVYield': 22.6}
    """
    logger.info(f"|SolisStore|insert_solis_generacion_inversor_dia| Starting inverter generation data insertion")
    
    # Log the data being processed for debugging
    try:
        data_json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        logger.info(f"|SolisStore|insert_solis_generacion_inversor_dia| Data being processed: {data_json_str}")
    except Exception as e:
        logger.warning(f"|SolisStore|insert_solis_generacion_inversor_dia| Could not serialize data for logging: {e}")
        logger.info(f"|SolisStore|insert_solis_generacion_inversor_dia| Data being processed (fallback): {data}")
    
    identificador_inversor = data.get('identificador_inversor')
    pvyield = data.get('PVYield')
    collect_time = data.get('collectTime')
    
    if not (identificador_inversor and pvyield is not None and collect_time):
        logger.warning(f"|SolisStore|insert_solis_generacion_inversor_dia| Incomplete entry skipped: {data}")
        return  # Skip incomplete entry
    
    # Parse date string (DD-MM-YYYY format) to date object
    try:
        date_obj = datetime.strptime(collect_time, '%d-%m-%Y').date()
    except ValueError as e:
        logger.warning(f"|SolisStore|insert_solis_generacion_inversor_dia| Invalid date format '{collect_time}' in entry: {data}. Error: {e}")
        return
    
    # Find the inverter by identificador_inversor
    try:
        inversor = Inversor.objects.get(identificador_inversor=identificador_inversor)
    except Inversor.DoesNotExist:
        logger.warning(f"|SolisStore|insert_solis_generacion_inversor_dia| Inversor with identificador_inversor '{identificador_inversor}' not found. Entry skipped for date {date_obj}.")
        return
    
    # Insert or update the daily inverter generation record
    obj, created = GeneracionInversorDiaria.objects.update_or_create(
        id_proyecto=inversor.id_proyecto,
        id_inversor=inversor,
        fecha_generacion_inversor_dia=date_obj,
        defaults={'energia_generada_inversor_dia': pvyield}
    )
    
    if created:
        logger.info(f"|SolisStore|insert_solis_generacion_inversor_dia| Created new GeneracionInversorDiaria for inverter {identificador_inversor} on {date_obj}: {pvyield} kWh")
    else:
        logger.info(f"|SolisStore|insert_solis_generacion_inversor_dia| Updated GeneracionInversorDiaria for inverter {identificador_inversor} on {date_obj}: {pvyield} kWh")
    
    logger.info(f"|SolisStore|insert_solis_generacion_inversor_dia| Successfully completed inverter generation data insertion for {identificador_inversor}")

