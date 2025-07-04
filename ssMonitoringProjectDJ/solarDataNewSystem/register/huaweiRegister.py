import requests
from solarData.models import Proyecto, Inversor
import logging

logger = logging.getLogger('huawei_newsystem')

def register_and_fetch_huawei_history(token, station_code):
    """
    1. Fetches device list from Huawei API for a given station_code, filters for devTypeId 1 or 38,
       and registers them as Inversor objects (linked to Proyecto with identificador_planta == station_code).
    2. Fetches historical KPI data for all registered inverters for the given time range.

    Args:
        token (str): Authentication token for Huawei API (XSRF-TOKEN).
        station_code (str): The station code (e.g., 'NE=35123000').
        start_time (int): Start time in UNIX ms
        end_time (int): End time in UNIX ms
    Returns:
        Tuple: (list of Inversor instances created/updated, history KPI API response)
    """
    logger.info(f"|HuaweiNewSystem|register_and_fetch_huawei_history| Starting registration for station_code: {station_code}")
    
    # --- 1. Register inverters from API ---
    url = "https://la5.fusionsolar.huawei.com/thirdData/getDevList"
    headers = {
        "XSRF-TOKEN": token,
        "Content-Type": "application/json",
    }
    body = {"stationCodes": station_code}
    
    logger.info(f"|HuaweiNewSystem|register_and_fetch_huawei_history| Making API call to {url} for station {station_code}")
    
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        api_response = response.json()
        logger.info(f"|HuaweiNewSystem|register_and_fetch_huawei_history| Successfully fetched device list for station {station_code}")
    except requests.RequestException as e:
        logger.error(f"|HuaweiNewSystem|register_and_fetch_huawei_history| API request failed for station {station_code}: {e}")
        raise

    try:
        proyecto = Proyecto.objects.get(identificador_planta=station_code)
        logger.info(f"|HuaweiNewSystem|register_and_fetch_huawei_history| Found existing Proyecto for station {station_code}: {proyecto.dealname}")
    except Proyecto.DoesNotExist:
        logger.error(f"|HuaweiNewSystem|register_and_fetch_huawei_history| No Proyecto found with identificador_planta='{station_code}'")
        raise ValueError(f"No Proyecto found with identificador_planta='{station_code}'")

    inverters = []
    dev_dns = []  # This will be the devDn ("NE=...") for each inverter
    dev_type_id = None
    created_count = 0
    updated_count = 0
    
    for dev in api_response.get("data", []):
        # devTypeId: "1" or "38" (string or int)
        if str(dev.get("devTypeId")) in ("1", "38"):
            inversor, created = Inversor.objects.update_or_create(
                identificador_inversor=dev["devDn"],  # devDn is for display and API
                id_proyecto=proyecto,
                defaults={
                    "huawei_devTypeId": str(dev["devTypeId"]),
                }
            )
            
            if created:
                logger.info(f"|HuaweiNewSystem|register_and_fetch_huawei_history| Created new Inversor: {dev['devDn']} (devTypeId: {dev['devTypeId']})")
                created_count += 1
            else:
                logger.info(f"|HuaweiNewSystem|register_and_fetch_huawei_history| Updated existing Inversor: {dev['devDn']} (devTypeId: {dev['devTypeId']})")
                updated_count += 1
                
            inverters.append(inversor)
            dev_dns.append(dev["devDn"])  # This is the devDn (string) required by the history API
            dev_type_id = str(dev["devTypeId"])  # All should be the same for the project

    if not dev_dns or not dev_type_id:
        logger.warning(f"|HuaweiNewSystem|register_and_fetch_huawei_history| No inverters with devTypeId 1 or 38 found for station {station_code}")
        raise ValueError("No inverters with devTypeId 1 or 38 found for this project.")

    logger.info(f"|HuaweiNewSystem|register_and_fetch_huawei_history| Registration completed for station {station_code}: {created_count} created, {updated_count} updated, {len(inverters)} total inverters")
    return inverters
