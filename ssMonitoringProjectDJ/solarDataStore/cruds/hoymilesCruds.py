# Imports for Hoymiles CRUD operations
from solarData.models import Proyecto, GeneracionEnergiaDiaria, Inversor, GeneracionInversorDiaria, Granular, GeneracionGranularDiaria
from datetime import datetime, timezone
import logging
import json

logger = logging.getLogger('hoymiles_store')

def insert_hoymiles_generacion_sistema_dia(data):
    """
    Insert or update daily generation data fetched from Hoymiles into the database.
    Args:
        data (list): List of dicts as returned by fetch_hoymiles_generacion_sistema_dia
                    Expected format: [{'stationCode': 'station_id', 'collectTime': '2025-06-05', 'PVYield': 17.0}, ...]
    """
    logger.info(f"|HoymilesStore|insert_hoymiles_generacion_sistema_dia| Starting system generation data insertion for {len(data)} entries")
    
    # Log the data being processed for debugging
    try:
        data_json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        # Truncate if very large (>3000 chars) to avoid log bloat
        if len(data_json_str) > 3000:
            truncated_data = data_json_str[:3000] + "... [TRUNCATED]"
            logger.info(f"|HoymilesStore|insert_hoymiles_generacion_sistema_dia| Data being processed (TRUNCATED): {truncated_data}")
        else:
            logger.info(f"|HoymilesStore|insert_hoymiles_generacion_sistema_dia| Data being processed: {data_json_str}")
    except Exception as e:
        logger.warning(f"|HoymilesStore|insert_hoymiles_generacion_sistema_dia| Could not serialize data for logging: {e}")
    
    successful_inserts = 0
    skipped_entries = 0
    
    for entry in data:
        station_code = entry.get('stationCode')
        pvyield = entry.get('PVYield')
        collect_time = entry.get('collectTime')
        
        if not (station_code and pvyield is not None and collect_time):
            logger.warning(f"|HoymilesStore|insert_hoymiles_generacion_sistema_dia| Incomplete entry skipped: {entry}")
            skipped_entries += 1
            continue
        
        # Parse date string (YYYY-MM-DD format) to date object
        try:
            date_obj = datetime.strptime(collect_time, '%Y-%m-%d').date()
        except ValueError as e:
            logger.warning(f"|HoymilesStore|insert_hoymiles_generacion_sistema_dia| Invalid date format '{collect_time}' in entry: {entry}. Error: {e}")
            skipped_entries += 1
            continue
        
        try:
            proyecto = Proyecto.objects.get(identificador_planta=station_code)
        except Proyecto.DoesNotExist:
            logger.warning(f"|HoymilesStore|insert_hoymiles_generacion_sistema_dia| Proyecto with identificador_planta '{station_code}' not found. Entry skipped for date {date_obj}.")
            skipped_entries += 1
            continue
        
        # Update or create the generation record
        obj, created = GeneracionEnergiaDiaria.objects.update_or_create(
            id_proyecto=proyecto,
            fecha_generacion_dia=date_obj,
            defaults={'energia_generada_dia': pvyield}
        )
        
        if created:
            logger.info(f"|HoymilesStore|insert_hoymiles_generacion_sistema_dia| Created new GeneracionEnergiaDiaria for project {station_code} on {date_obj}: {pvyield} kWh")
        else:
            logger.info(f"|HoymilesStore|insert_hoymiles_generacion_sistema_dia| Updated GeneracionEnergiaDiaria for project {station_code} on {date_obj}: {pvyield} kWh")
        
        successful_inserts += 1
    
    logger.info(f"|HoymilesStore|insert_hoymiles_generacion_sistema_dia| Completed system generation data insertion: {successful_inserts} successful, {skipped_entries} skipped")


def insert_hoymiles_generacion_inversor_granular_dia(data, fecha_generacion):
    """
    Insert or update inverter and granular generation data fetched from Hoymiles into the database.
    Args:
        data (dict): Dictionary as returned by fetch_hoymiles_generacion_inversor_granular_dia
                    Expected format: {
                        'stationCode': 'station_id', 
                        'inverter_sn': 'serial_number',
                        'collectTime': '2025-06-05', 
                        'PVYield': 17.0,
                        'channel1': 2.5, 'channel2': 2.6, 'channel3': 2.7, 'channel4': 2.8
                    }
        fecha_generacion (str): Date in YYYY-MM-DD format
    """
    logger.info(f"|HoymilesStore|insert_hoymiles_generacion_inversor_granular_dia| Starting inverter and granular data insertion for date {fecha_generacion}")
    
    # Log the data being processed for debugging
    try:
        data_json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        logger.info(f"|HoymilesStore|insert_hoymiles_generacion_inversor_granular_dia| Data being processed: {data_json_str}")
    except Exception as e:
        logger.warning(f"|HoymilesStore|insert_hoymiles_generacion_inversor_granular_dia| Could not serialize data for logging: {e}")
    
    # Parse date string to date object
    try:
        date_obj = datetime.strptime(fecha_generacion, '%Y-%m-%d').date()
    except ValueError as e:
        logger.error(f"|HoymilesStore|insert_hoymiles_generacion_inversor_granular_dia| Invalid date format '{fecha_generacion}'. Error: {e}")
        return
    
    station_code = data.get('stationCode')
    inverter_sn = data.get('inverter_sn')
    pvyield = data.get('PVYield')
    
    if not station_code or not inverter_sn:
        logger.warning(f"|HoymilesStore|insert_hoymiles_generacion_inversor_granular_dia| Missing stationCode or inverter_sn in data: {data}")
        return
    
    # Get the inverter object
    try:
        inversor = Inversor.objects.get(identificador_inversor=inverter_sn)
    except Inversor.DoesNotExist:
        logger.warning(f"|HoymilesStore|insert_hoymiles_generacion_inversor_granular_dia| Inversor with identificador_inversor '{inverter_sn}' not found.")
        return
    
    proyecto = inversor.id_proyecto
    
    # Insert inverter generation data
    if pvyield is not None:
        try:
            obj, created = GeneracionInversorDiaria.objects.update_or_create(
                id_proyecto=proyecto,
                id_inversor=inversor,
                fecha_generacion_inversor_dia=date_obj,
                defaults={'energia_generada_inversor_dia': pvyield}
            )
            
            if created:
                logger.info(f"|HoymilesStore|insert_hoymiles_generacion_inversor_granular_dia| Created new GeneracionInversorDiaria for {inverter_sn} on {date_obj}: {pvyield} kWh")
            else:
                logger.info(f"|HoymilesStore|insert_hoymiles_generacion_inversor_granular_dia| Updated GeneracionInversorDiaria for {inverter_sn} on {date_obj}: {pvyield} kWh")
        except Exception as e:
            logger.error(f"|HoymilesStore|insert_hoymiles_generacion_inversor_granular_dia| Error inserting inverter data: {e}")
    
    # Insert granular data for each channel (following Huawei pattern)
    successful_inserts = 0
    skipped_entries = 0
    created_granulars = 0
    
    for channel_num in range(1, 5):  # Channels 1-4
        channel_key = f'channel{channel_num}'
        channel_energy = data.get(channel_key)
        
        if channel_energy is not None:
            try:
                # Create serial_granular following Huawei pattern: inverter_sn-channel_num
                serial_granular = f"{inverter_sn}-{channel_num}"  # e.g., 'HWI123456-1'
                
                granular, created_granular = Granular.objects.get_or_create(
                    id_proyecto=proyecto,
                    id_inversor=inversor,
                    serial_granular=serial_granular,
                    defaults={"tipo_granular": "MPPT"}
                )
                
                if created_granular:
                    logger.info(f"|HoymilesStore|insert_hoymiles_generacion_inversor_granular_dia| Created new Granular: {serial_granular} for inverter {inverter_sn}")
                    created_granulars += 1
                
                # Insert/update the generation data
                obj, created = GeneracionGranularDiaria.objects.update_or_create(
                    id_proyecto=proyecto,
                    id_inversor=inversor,
                    id_granular=granular,
                    fecha_generacion_granular_dia=date_obj,
                    defaults={"energia_generada_granular_dia": channel_energy}
                )
                
                if created:
                    logger.info(f"|HoymilesStore|insert_hoymiles_generacion_inversor_granular_dia| Created new GeneracionGranularDiaria for {serial_granular} on {date_obj}: {channel_energy} kWh")
                else:
                    logger.info(f"|HoymilesStore|insert_hoymiles_generacion_inversor_granular_dia| Updated GeneracionGranularDiaria for {serial_granular} on {date_obj}: {channel_energy} kWh")
                
                successful_inserts += 1
                
            except Exception as e:
                logger.error(f"|HoymilesStore|insert_hoymiles_generacion_inversor_granular_dia| Error processing channel {channel_num}: {e}")
                skipped_entries += 1
        else:
            logger.debug(f"|HoymilesStore|insert_hoymiles_generacion_inversor_granular_dia| Channel {channel_num} has no data (None)")
            skipped_entries += 1
    
    logger.info(f"|HoymilesStore|insert_hoymiles_generacion_inversor_granular_dia| Completed granular data insertion: {successful_inserts} successful, {skipped_entries} skipped, {created_granulars} new Granular objects created")
