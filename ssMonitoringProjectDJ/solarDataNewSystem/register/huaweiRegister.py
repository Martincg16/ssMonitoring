import requests
from solarData.models import Proyecto, Inversor, MarcasInversores
from datetime import date
import logging

logger = logging.getLogger('huawei_newsystem')

def get_huawei_systems(token):
    """
    Fetches all Huawei plant/station codes and names from the Huawei API.
    Handles pagination automatically.
    
    Args:
        token (str): Authentication token for Huawei API (XSRF-TOKEN).
    
    Returns:
        list: List of dicts with 'plantCode' and 'plantName' for each station.
              Example: [{'plantCode': 'NE=35123000', 'plantName': 'SFV EDS CARACAS'}, ...]
    """
    logger.info("|HuaweiNewSystem|get_huawei_systems| Starting to fetch all Huawei systems")
    
    url = "https://la5.fusionsolar.huawei.com/thirdData/stations"
    headers = {
        "XSRF-TOKEN": token,
        "Content-Type": "application/json"
    }
    
    all_stations = []
    page_no = 1
    
    while True:
        body = {"pageNo": page_no}
        
        logger.info(f"|HuaweiNewSystem|get_huawei_systems| Fetching page {page_no}")
        
        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            api_response = response.json()
            
            if not api_response.get("success"):
                logger.error(f"|HuaweiNewSystem|get_huawei_systems| API returned success=false: {api_response.get('message')}")
                raise RuntimeError(f"Huawei API error: {api_response.get('message')}")
            
            data = api_response.get("data", {})
            plant_list = data.get("list", [])
            page_count = data.get("pageCount", 1)
            
            logger.info(f"|HuaweiNewSystem|get_huawei_systems| Page {page_no}/{page_count}: Found {len(plant_list)} stations")
            
            # Extract plantCode and plantName from each station
            for plant in plant_list:
                station_info = {
                    "plantCode": plant.get("plantCode"),
                    "plantName": plant.get("plantName")
                }
                all_stations.append(station_info)
            
            # Check if we've reached the last page
            if page_no >= page_count:
                logger.info(f"|HuaweiNewSystem|get_huawei_systems| Completed fetching all pages. Total stations: {len(all_stations)}")
                break
            
            page_no += 1
            
        except requests.RequestException as e:
            logger.error(f"|HuaweiNewSystem|get_huawei_systems| API request failed on page {page_no}: {e}")
            raise
    
    return all_stations

def compare_stations_with_database(huawei_stations):
    """
    Compares Huawei stations with existing Proyectos in the database.
    Returns only the stations that exist in Huawei but NOT in the database.
    
    Args:
        huawei_stations (list): List of dicts from get_huawei_systems()
                               Format: [{'plantCode': 'NE=...', 'plantName': '...'}, ...]
    
    Returns:
        list: List of dicts with only the NEW stations (not in database)
              Format: [{'plantCode': 'NE=...', 'plantName': '...'}, ...]
    """
    logger.info(f"|HuaweiNewSystem|compare_stations_with_database| Starting comparison of {len(huawei_stations)} Huawei stations with database")
    
    # Get all existing plant codes from the database
    existing_plant_codes = set(
        Proyecto.objects.filter(
            identificador_planta__isnull=False
        ).values_list('identificador_planta', flat=True)
    )
    
    logger.info(f"|HuaweiNewSystem|compare_stations_with_database| Found {len(existing_plant_codes)} existing projects in database")
    
    # Filter out stations that already exist in the database
    new_stations = []
    for station in huawei_stations:
        plant_code = station.get('plantCode')
        if plant_code and plant_code not in existing_plant_codes:
            new_stations.append(station)
            logger.info(f"|HuaweiNewSystem|compare_stations_with_database| New station found: {plant_code} - {station.get('plantName')}")
        else:
            logger.debug(f"|HuaweiNewSystem|compare_stations_with_database| Station already exists: {plant_code}")
    
    logger.info(f"|HuaweiNewSystem|compare_stations_with_database| Comparison complete: {len(new_stations)} new stations found")
    
    return new_stations

def create_new_huawei_projects(new_stations):
    """
    Creates Proyecto records for new Huawei stations.
    
    Args:
        new_stations (list): List of dicts from compare_stations_with_database()
                            Format: [{'plantCode': 'NE=...', 'plantName': '...'}, ...]
    
    Returns:
        dict: Summary with 'created' (list of created Proyectos) and 'errors' (list of errors)
    """
    logger.info(f"|HuaweiNewSystem|create_new_huawei_projects| Starting to create {len(new_stations)} new projects")
    
    # Get Huawei brand (MarcasInversores id=3)
    try:
        marca_huawei = MarcasInversores.objects.get(id=3)
        logger.info(f"|HuaweiNewSystem|create_new_huawei_projects| Found Huawei brand: {marca_huawei.marca}")
    except MarcasInversores.DoesNotExist:
        logger.error("|HuaweiNewSystem|create_new_huawei_projects| MarcasInversores with id=3 (Huawei) not found in database")
        raise RuntimeError("Huawei brand (id=3) not found in database. Please create MarcasInversores with id=3")
    
    created_projects = []
    errors = []
    
    for station in new_stations:
        plant_code = station.get('plantCode')
        plant_name = station.get('plantName')
        
        if not plant_code or not plant_name:
            error_msg = f"Missing plantCode or plantName in station data: {station}"
            logger.warning(f"|HuaweiNewSystem|create_new_huawei_projects| {error_msg}")
            errors.append(error_msg)
            continue
        
        try:
            # Create new Proyecto
            proyecto = Proyecto.objects.create(
                dealname=plant_name,
                identificador_planta=plant_code,
                fecha_entrada_en_operacion=date.today(),
                marca_inversor=marca_huawei,
                restriccion_de_autoconsumo=True,
                # id_ciudad will use default from model (1125)
                # capacidad_instalada_ac, capacidad_instalada_dc: NULL
                # energia_prometida_mes, energia_minima_mes: NULL
            )
            
            created_projects.append(proyecto)
            logger.info(f"|HuaweiNewSystem|create_new_huawei_projects| Created Proyecto: {plant_name} ({plant_code}) with ID: {proyecto.id}")
            
        except Exception as e:
            error_msg = f"Failed to create project for {plant_code} ({plant_name}): {e}"
            logger.error(f"|HuaweiNewSystem|create_new_huawei_projects| {error_msg}")
            errors.append(error_msg)
    
    logger.info(f"|HuaweiNewSystem|create_new_huawei_projects| Completed: {len(created_projects)} projects created, {len(errors)} errors")
    
    return {
        'created': created_projects,
        'errors': errors
    }

def register_huawei_inverters(token, station_code):
    """
    Fetches device list from Huawei API for a given station_code, filters for devTypeId 1 or 38,
    and registers them as Inversor objects (linked to Proyecto with identificador_planta == station_code).

    Args:
        token (str): Authentication token for Huawei API (XSRF-TOKEN).
        station_code (str): The station code (e.g., 'NE=35123000').
    
    Returns:
        list: List of Inversor instances created/updated
    """
    logger.info(f"|HuaweiNewSystem|register_huawei_inverters| Starting registration for station_code: {station_code}")
    
    # --- 1. Register inverters from API ---
    url = "https://la5.fusionsolar.huawei.com/thirdData/getDevList"
    headers = {
        "XSRF-TOKEN": token,
        "Content-Type": "application/json",
    }
    body = {"stationCodes": station_code}
    
    logger.info(f"|HuaweiNewSystem|register_huawei_inverters| Making API call to {url} for station {station_code}")
    
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        api_response = response.json()
        logger.info(f"|HuaweiNewSystem|register_huawei_inverters| Successfully fetched device list for station {station_code}")
    except requests.RequestException as e:
        logger.error(f"|HuaweiNewSystem|register_huawei_inverters| API request failed for station {station_code}: {e}")
        raise

    try:
        proyecto = Proyecto.objects.get(identificador_planta=station_code)
        logger.info(f"|HuaweiNewSystem|register_huawei_inverters| Found existing Proyecto for station {station_code}: {proyecto.dealname}")
    except Proyecto.DoesNotExist:
        logger.error(f"|HuaweiNewSystem|register_huawei_inverters| No Proyecto found with identificador_planta='{station_code}'")
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
                logger.info(f"|HuaweiNewSystem|register_huawei_inverters| Created new Inversor: {dev['devDn']} (devTypeId: {dev['devTypeId']})")
                created_count += 1
            else:
                logger.info(f"|HuaweiNewSystem|register_huawei_inverters| Updated existing Inversor: {dev['devDn']} (devTypeId: {dev['devTypeId']})")
                updated_count += 1
                
            inverters.append(inversor)
            dev_dns.append(dev["devDn"])  # This is the devDn (string) required by the history API
            dev_type_id = str(dev["devTypeId"])  # All should be the same for the project

    if not dev_dns or not dev_type_id:
        logger.warning(f"|HuaweiNewSystem|register_huawei_inverters| No inverters with devTypeId 1 or 38 found for station {station_code}")
        raise ValueError("No inverters with devTypeId 1 or 38 found for this project.")

    logger.info(f"|HuaweiNewSystem|register_huawei_inverters| Registration completed for station {station_code}: {created_count} created, {updated_count} updated, {len(inverters)} total inverters")
    return inverters

def auto_register_huawei_systems(token):
    """
    Complete auto-registration workflow for Huawei systems:
    1. Fetches all Huawei stations from API
    2. Compares with database to find new stations
    3. Creates Proyecto records for new stations
    4. Registers inverters for each new project
    
    Args:
        token (str): Authentication token for Huawei API (XSRF-TOKEN).
    
    Returns:
        dict: Summary with:
            - 'total_huawei_stations': Total stations in Huawei
            - 'new_stations_found': Number of new stations
            - 'projects_created': List of created Proyecto objects
            - 'inverters_registered': Dict mapping plant_code to list of Inversor objects
            - 'errors': List of error messages
    """
    logger.info("|HuaweiNewSystem|auto_register_huawei_systems| Starting auto-registration workflow")
    
    summary = {
        'total_huawei_stations': 0,
        'new_stations_found': 0,
        'projects_created': [],
        'inverters_registered': {},
        'errors': []
    }
    
    try:
        # Step 1: Fetch all Huawei stations
        logger.info("|HuaweiNewSystem|auto_register_huawei_systems| Step 1: Fetching all Huawei stations")
        huawei_stations = get_huawei_systems(token)
        summary['total_huawei_stations'] = len(huawei_stations)
        logger.info(f"|HuaweiNewSystem|auto_register_huawei_systems| Found {len(huawei_stations)} total Huawei stations")
        
        # Step 2: Compare with database
        logger.info("|HuaweiNewSystem|auto_register_huawei_systems| Step 2: Comparing with database")
        new_stations = compare_stations_with_database(huawei_stations)
        summary['new_stations_found'] = len(new_stations)
        logger.info(f"|HuaweiNewSystem|auto_register_huawei_systems| Found {len(new_stations)} new stations to register")
        
        if not new_stations:
            logger.info("|HuaweiNewSystem|auto_register_huawei_systems| No new stations found. Auto-registration complete.")
            return summary
        
        # Step 3: Create new projects
        logger.info("|HuaweiNewSystem|auto_register_huawei_systems| Step 3: Creating new projects")
        project_results = create_new_huawei_projects(new_stations)
        summary['projects_created'] = project_results['created']
        summary['errors'].extend(project_results['errors'])
        logger.info(f"|HuaweiNewSystem|auto_register_huawei_systems| Created {len(project_results['created'])} new projects")
        
        # Step 4: Register inverters for each new project
        logger.info("|HuaweiNewSystem|auto_register_huawei_systems| Step 4: Registering inverters for new projects")
        for proyecto in project_results['created']:
            try:
                logger.info(f"|HuaweiNewSystem|auto_register_huawei_systems| Registering inverters for {proyecto.identificador_planta}")
                inverters = register_huawei_inverters(token, proyecto.identificador_planta)
                summary['inverters_registered'][proyecto.identificador_planta] = inverters
                logger.info(f"|HuaweiNewSystem|auto_register_huawei_systems| Registered {len(inverters)} inverters for {proyecto.identificador_planta}")
            except Exception as e:
                error_msg = f"Failed to register inverters for {proyecto.identificador_planta}: {e}"
                logger.error(f"|HuaweiNewSystem|auto_register_huawei_systems| {error_msg}")
                summary['errors'].append(error_msg)
        
        logger.info(f"|HuaweiNewSystem|auto_register_huawei_systems| Auto-registration complete: {len(summary['projects_created'])} projects created, {len(summary['inverters_registered'])} projects with inverters registered, {len(summary['errors'])} errors")
        
    except Exception as e:
        error_msg = f"Auto-registration workflow failed: {e}"
        logger.error(f"|HuaweiNewSystem|auto_register_huawei_systems| {error_msg}")
        summary['errors'].append(error_msg)
        raise
    
    return summary