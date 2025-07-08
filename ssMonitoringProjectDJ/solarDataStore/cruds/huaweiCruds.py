# Imports for Huawei CRUD operations
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher
from solarData.models import Proyecto, GeneracionEnergiaDiaria, Inversor, GeneracionInversorDiaria, Granular, GeneracionGranularDiaria
from datetime import datetime, timezone
import logging
import json

logger = logging.getLogger('huawei_store')

def insert_huawei_generacion_sistema_dia(data):
    """
    Insert or update daily generation data fetched from Huawei into the database.
    Args:
        data (list): List of dicts as returned by fetch_huawei_generacion_sistema_dia
    """
    logger.info(f"|HuaweiStore|insert_huawei_generacion_sistema_dia| Starting system generation data insertion for {len(data)} entries")
    
    # Log the data being processed for debugging
    try:
        data_json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        # Truncate if very large (>3000 chars) to avoid log bloat
        if len(data_json_str) > 3000:
            truncated_data = data_json_str[:3000] + "... [TRUNCATED]"
            logger.info(f"|HuaweiStore|insert_huawei_generacion_sistema_dia| Data being processed (TRUNCATED): {truncated_data}")
        else:
            logger.info(f"|HuaweiStore|insert_huawei_generacion_sistema_dia| Data being processed: {data_json_str}")
    except Exception as e:
        logger.warning(f"|HuaweiStore|insert_huawei_generacion_sistema_dia| Could not serialize data for logging: {e}")
    
    successful_inserts = 0
    skipped_entries = 0
    
    for entry in data:
        station_code = entry.get('stationCode')
        pvyield = entry.get('PVYield')
        collect_time = entry.get('collectTime')
        
        if not (station_code and pvyield is not None and collect_time):
            logger.warning(f"|HuaweiStore|insert_huawei_generacion_sistema_dia| Incomplete entry skipped: {entry}")
            skipped_entries += 1
            continue  # Skip incomplete entries
            
        date_obj = datetime.fromtimestamp(collect_time / 1000, tz=timezone.utc).date()
        
        try:
            proyecto = Proyecto.objects.get(identificador_planta=station_code)
        except Proyecto.DoesNotExist:
            logger.warning(f"|HuaweiStore|insert_huawei_generacion_sistema_dia| Proyecto with identificador_planta '{station_code}' not found. Entry skipped for date {date_obj}.")
            skipped_entries += 1
            continue
            
        obj, created = GeneracionEnergiaDiaria.objects.update_or_create(
            id_proyecto=proyecto,
            fecha_generacion_dia=date_obj,
            defaults={'energia_generada_dia': pvyield}
        )
        
        if created:
            logger.info(f"|HuaweiStore|insert_huawei_generacion_sistema_dia| Created new GeneracionEnergiaDiaria for project {station_code} on {date_obj}: {pvyield} kWh")
        else:
            logger.info(f"|HuaweiStore|insert_huawei_generacion_sistema_dia| Updated GeneracionEnergiaDiaria for project {station_code} on {date_obj}: {pvyield} kWh")
        
        successful_inserts += 1
    
    logger.info(f"|HuaweiStore|insert_huawei_generacion_sistema_dia| Completed system generation data insertion: {successful_inserts} successful, {skipped_entries} skipped")

def insert_huawei_generacion_inversor_dia(data):
    """
    Insert or update daily inverter generation data fetched from Huawei into the database.
    Args:
        data (list): List of dicts as returned by fetch_huawei_generacion_inversor_dia
    """
    logger.info(f"|HuaweiStore|insert_huawei_generacion_inversor_dia| Starting inverter generation data insertion for {len(data)} entries")
    
    # Log the data being processed for debugging
    try:
        data_json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        # Truncate if very large (>3000 chars) to avoid log bloat
        if len(data_json_str) > 3000:
            truncated_data = data_json_str[:3000] + "... [TRUNCATED]"
            logger.info(f"|HuaweiStore|insert_huawei_generacion_inversor_dia| Data being processed (TRUNCATED): {truncated_data}")
        else:
            logger.info(f"|HuaweiStore|insert_huawei_generacion_inversor_dia| Data being processed: {data_json_str}")
    except Exception as e:
        logger.warning(f"|HuaweiStore|insert_huawei_generacion_inversor_dia| Could not serialize data for logging: {e}")
    
    successful_inserts = 0
    skipped_entries = 0
    
    for entry in data:
        identificador_inversor = entry.get('identificador_inversor')
        product_power = entry.get('product_power')
        collect_time = entry.get('collectTime')
        
        if not (identificador_inversor and product_power is not None and collect_time):
            logger.warning(f"|HuaweiStore|insert_huawei_generacion_inversor_dia| Incomplete entry skipped: {entry}")
            skipped_entries += 1
            continue  # Skip incomplete entries
            
        date_obj = datetime.fromtimestamp(collect_time / 1000, tz=timezone.utc).date()
        
        try:
            inversor = Inversor.objects.get(identificador_inversor=identificador_inversor)
        except Inversor.DoesNotExist:
            logger.warning(f"|HuaweiStore|insert_huawei_generacion_inversor_dia| Inversor with identificador_inversor '{identificador_inversor}' not found. Entry skipped for date {date_obj}.")
            skipped_entries += 1
            continue
            
        obj, created = GeneracionInversorDiaria.objects.update_or_create(
            id_proyecto=inversor.id_proyecto,
            id_inversor=inversor,
            fecha_generacion_inversor_dia=date_obj,
            defaults={'energia_generada_inversor_dia': product_power}
        )
        
        if created:
            logger.info(f"|HuaweiStore|insert_huawei_generacion_inversor_dia| Created new GeneracionInversorDiaria for inverter {identificador_inversor} on {date_obj}: {product_power} kWh")
        else:
            logger.info(f"|HuaweiStore|insert_huawei_generacion_inversor_dia| Updated GeneracionInversorDiaria for inverter {identificador_inversor} on {date_obj}: {product_power} kWh")
        
        successful_inserts += 1
    
    logger.info(f"|HuaweiStore|insert_huawei_generacion_inversor_dia| Completed inverter generation data insertion: {successful_inserts} successful, {skipped_entries} skipped")

def insert_huawei_generacion_granular_dia(mppt_energy_dict, fecha_generacion):
    """
    Insert or update daily MPPT (granular) generation data fetched from Huawei into the database.
    Args:
        mppt_energy_dict (dict): { 'NE=...': { 'mppt_1_cap': value, ... }, ... }
        fecha_generacion (date): date object for the day of generation
    """
    logger.info(f"|HuaweiStore|insert_huawei_generacion_granular_dia| Starting granular (MPPT) data insertion for {len(mppt_energy_dict)} inverters on {fecha_generacion}")
    
    # Log the data being processed for debugging (CRITICAL for granular data issues)
    try:
        data_json_str = json.dumps(mppt_energy_dict, ensure_ascii=False, separators=(',', ':'))
        # Truncate if very large (>3000 chars) to avoid log bloat
        if len(data_json_str) > 3000:
            truncated_data = data_json_str[:3000] + "... [TRUNCATED]"
            logger.info(f"|HuaweiStore|insert_huawei_generacion_granular_dia| MPPT data being processed (TRUNCATED): {truncated_data}")
        else:
            logger.info(f"|HuaweiStore|insert_huawei_generacion_granular_dia| MPPT data being processed: {data_json_str}")
    except Exception as e:
        logger.warning(f"|HuaweiStore|insert_huawei_generacion_granular_dia| Could not serialize MPPT data for logging: {e}")
    
    successful_inserts = 0
    skipped_entries = 0
    created_granulars = 0
    
    for serial, mppts in mppt_energy_dict.items():
        try:
            inversor = Inversor.objects.get(identificador_inversor=serial)
        except Inversor.DoesNotExist:
            logger.warning(f"|HuaweiStore|insert_huawei_generacion_granular_dia| Inversor with identificador_inversor '{serial}' not found. Entry skipped for date {fecha_generacion}.")
            skipped_entries += 1
            continue
            
        proyecto = inversor.id_proyecto
        
        for mppt_key, energia in mppts.items():
            # Extract mppt number from key (e.g., 'mppt_1_cap' -> 1)
            try:
                mppt_number = int(mppt_key.split('_')[1])
            except (IndexError, ValueError):
                logger.warning(f"|HuaweiStore|insert_huawei_generacion_granular_dia| Could not extract MPPT number from key '{mppt_key}' for inverter {serial}. Skipping.")
                skipped_entries += 1
                continue
                
            serial_granular = f"{serial}-{mppt_number}"  # e.g., 'NE=35759038-1'
            
            granular, created_granular = Granular.objects.get_or_create(
                id_proyecto=proyecto,
                id_inversor=inversor,
                serial_granular=serial_granular,
                defaults={"tipo_granular": "MPPT"}
            )
            
            if created_granular:
                logger.info(f"|HuaweiStore|insert_huawei_generacion_granular_dia| Created new Granular: {serial_granular} for inverter {serial}")
                created_granulars += 1
                
            obj, created = GeneracionGranularDiaria.objects.update_or_create(
                id_proyecto=proyecto,
                id_inversor=inversor,
                id_granular=granular,
                fecha_generacion_granular_dia=fecha_generacion,
                defaults={"energia_generada_granular_dia": energia}
            )
            
            if created:
                logger.info(f"|HuaweiStore|insert_huawei_generacion_granular_dia| Created new GeneracionGranularDiaria for {serial_granular} on {fecha_generacion}: {energia} kWh")
            else:
                logger.info(f"|HuaweiStore|insert_huawei_generacion_granular_dia| Updated GeneracionGranularDiaria for {serial_granular} on {fecha_generacion}: {energia} kWh")
            
            successful_inserts += 1
    
    logger.info(f"|HuaweiStore|insert_huawei_generacion_granular_dia| Completed granular data insertion: {successful_inserts} successful, {skipped_entries} skipped, {created_granulars} new Granular objects created")
