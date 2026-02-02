import requests
import logging
import os
from datetime import datetime, timedelta, date
from solarData.models import Proyecto, Inversor, MarcasInversores, Granular

logger = logging.getLogger('hoymiles_newsystem')

class HoymilesRegister:
    """
    Hoymiles API registration and project management class.
    Handles station and inverter registration for new Hoymiles projects.
    """
    
    # API Configuration
    base_url = "https://wapi.hoymiles.com"
    timeout = 30
    
    def __init__(self):
        """Initialize HoymilesRegister instance."""
        self.api_key = os.getenv('HOYMILES_API_KEY')
        
        if not self.api_key:
            raise ValueError("HOYMILES_API_KEY environment variable is required")
        
        logger.info("|HoymilesRegister|__init__| Hoymiles register initialized")

    def hoymiles_register_new_project(self, station_code):
        """
        Register a new Hoymiles project and inverters.
        
        Args:
            station_code (str): The station code to register.
        """
        logger.info(f"|HoymilesRegister|hoymiles_register_new_project| Starting registration for station_code: {station_code}")
        
        # Step 1: Get devices from station
        devices_data = self.get_devices_by_station(station_code)
        
        # Step 2: Create the project (Proyecto)
        proyecto = self.create_proyecto(station_code)
        
        # Step 3: Create inverters (DTU devices)
        inversores = self.create_inversores(proyecto, devices_data)
        
        # Step 4: Create granular objects for each inverter
        self.create_granular_for_inversores(proyecto, inversores)
        
        logger.info(f"|HoymilesRegister|hoymiles_register_new_project| Registration completed for station {station_code}: {len(inversores)} inverters processed")
        return proyecto, inversores
    
    def get_devices_by_station(self, station_code):
        """
        Get devices for a specific station from Hoymiles API.
        
        Args:
            station_code (str): The station code
            
        Returns:
            dict: API response data containing device information
        """
        logger.info(f"|HoymilesRegister|get_devices_by_station| Fetching devices for station: {station_code}")
        
        endpoint = f"v0/zhgf-core/oapi/0/findDevsByStation?key={self.api_key}"
        url = f"{self.base_url}/{endpoint}"
        
        # Convert station_code to int as required by API
        try:
            station_id = int(station_code)
        except ValueError:
            logger.error(f"|HoymilesRegister|get_devices_by_station| Invalid station_code '{station_code}' - must be convertible to int")
            raise ValueError(f"Station code '{station_code}' must be a valid integer")
        
        body = {"id": station_id}
        
        try:
            logger.info(f"|HoymilesRegister|get_devices_by_station| Making POST request to {url}")
            response = requests.post(url, json=body, timeout=self.timeout)
            response.raise_for_status()
            
            api_response = response.json()
            logger.info(f"|HoymilesRegister|get_devices_by_station| API response received for station {station_code}")
            
            # Check API status
            if api_response.get("status") != "0":
                error_msg = api_response.get("message", "Unknown error")
                logger.error(f"|HoymilesRegister|get_devices_by_station| API error for station {station_code}: {error_msg}")
                raise RuntimeError(f"Hoymiles API error: {error_msg}")
            
            data = api_response.get("data", {})
            logger.info(f"|HoymilesRegister|get_devices_by_station| Successfully fetched devices for station {station_code}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"|HoymilesRegister|get_devices_by_station| HTTP request failed for station {station_code}: {e}")
            raise RuntimeError(f"Failed to fetch devices for station {station_code}: {e}")
        except Exception as e:
            logger.error(f"|HoymilesRegister|get_devices_by_station| Unexpected error for station {station_code}: {e}")
            raise
    
    def create_proyecto(self, station_code):
        """
        Create a new Proyecto object for Hoymiles station.
        
        Args:
            station_code (str): The station code
            
        Returns:
            Proyecto: The created Proyecto instance
        """
        logger.info(f"|HoymilesRegister|create_proyecto| Creating new proyecto for station: {station_code}")
        
        # Get Hoymiles brand from MarcasInversores
        try:
            hoymiles_brand = MarcasInversores.objects.get(marca='Hoymiles')
            logger.info(f"|HoymilesRegister|create_proyecto| Found Hoymiles brand: {hoymiles_brand.marca}")
        except MarcasInversores.DoesNotExist:
            logger.error(f"|HoymilesRegister|create_proyecto| Hoymiles brand not found in MarcasInversores")
            raise ValueError("Hoymiles brand not found in database. Please add 'Hoymiles' to MarcasInversores first.")
        
        # Check if proyecto already exists
        if Proyecto.objects.filter(identificador_planta=station_code).exists():
            logger.error(f"|HoymilesRegister|create_proyecto| Proyecto with station_code {station_code} already exists")
            raise ValueError(f"Proyecto with identificador_planta='{station_code}' already exists. Cannot create duplicate.")
        
        # Create new proyecto (with minimal required fields)
        try:
            from datetime import date
            proyecto = Proyecto.objects.create(
                identificador_planta=station_code,
                dealname=f"Hoymiles Station {station_code}",  # Default name
                marca_inversor=hoymiles_brand,
                fecha_entrada_en_operacion=date.today(),  # Required field - default to today
                energia_prometida_mes=0,  # Set default values
                energia_minima_mes=0,     # Set default values
            )
            logger.info(f"|HoymilesRegister|create_proyecto| Created new Proyecto: {proyecto.dealname} ({station_code})")
            
        except Exception as e:
            logger.error(f"|HoymilesRegister|create_proyecto| Failed to create proyecto for {station_code}: {e}")
            raise RuntimeError(f"Failed to create proyecto for station {station_code}: {e}")
        
        logger.info(f"|HoymilesRegister|create_proyecto| Proyecto creation completed for station {station_code}")
        return proyecto
    
    def create_inversores(self, proyecto, devices_data):
        """
        Create Inversor objects for microinverters (create only).
        
        Args:
            proyecto (Proyecto): The proyecto instance
            devices_data (dict): Device data from API response
            
        Returns:
            list: List of created Inversor instances
        """
        logger.info(f"|HoymilesRegister|create_inversores| Creating inversores for proyecto: {proyecto.identificador_planta}")
        
        inversores = []
        micro_datas = devices_data.get('micro_datas', [])
        
        if not micro_datas:
            logger.warning(f"|HoymilesRegister|create_inversores| No microinverter devices found for proyecto {proyecto.identificador_planta}")
            return inversores
        
        created_count = 0
        skipped_count = 0
        
        for micro_device in micro_datas:
            mi_sn = micro_device.get('mi_sn')
            
            if not mi_sn:
                logger.warning(f"|HoymilesRegister|create_inversores| Microinverter device missing 'mi_sn': {micro_device}")
                continue
            
            try:
                # Check if inversor already exists
                if Inversor.objects.filter(identificador_inversor=mi_sn, id_proyecto=proyecto).exists():
                    logger.info(f"|HoymilesRegister|create_inversores| Inversor {mi_sn} already exists, skipping creation")
                    skipped_count += 1
                    continue
                
                # Create new inversor for microinverter
                inversor = Inversor.objects.create(
                    identificador_inversor=mi_sn,
                    id_proyecto=proyecto
                )
                
                logger.info(f"|HoymilesRegister|create_inversores| Created new Inversor: {mi_sn}")
                created_count += 1
                inversores.append(inversor)
                
            except Exception as e:
                logger.error(f"|HoymilesRegister|create_inversores| Failed to create inversor {mi_sn}: {e}")
                continue
        
        logger.info(f"|HoymilesRegister|create_inversores| Completed inversor creation: {created_count} created, {skipped_count} skipped")
        return inversores
    
    def create_granular_for_inversores(self, proyecto, inversores):
        """
        Create granular objects for all inverters by fetching microinverter data.
        
        Args:
            proyecto (Proyecto): The proyecto instance
            inversores (list): List of Inversor instances
        """
        logger.info(f"|HoymilesRegister|create_granular_for_inversores| Creating granular objects for {len(inversores)} inversores")
        
        # Get yesterday's date for API call
        yesterday = datetime.now() - timedelta(days=1)
        target_date = yesterday.strftime('%Y-%m-%d')
        
        total_granular_created = 0
        
        for inversor in inversores:
            try:
                # Fetch microinverter data for this DTU
                mi_data = self.get_microinverter_data(proyecto.identificador_planta, inversor.identificador_inversor, target_date)
                
                # Create granular objects based on the number of ports found
                granular_created = self.create_granular_objects(proyecto, inversor, mi_data)
                total_granular_created += granular_created
                
            except Exception as e:
                logger.error(f"|HoymilesRegister|create_granular_for_inversores| Failed to create granular for inversor {inversor.identificador_inversor}: {e}")
                continue
        
        logger.info(f"|HoymilesRegister|create_granular_for_inversores| Completed granular creation: {total_granular_created} total granular objects created")
    
    def get_microinverter_data(self, plant_id, inverter_id, target_date):
        """
        Get microinverter data for a specific inverter and date.
        
        Args:
            plant_id (str): The plant/station ID
            inverter_id (str): The inverter/DTU serial number
            target_date (str): Date in YYYY-MM-DD format
            
        Returns:
            list: Microinverter data from API
        """
        logger.info(f"|HoymilesRegister|get_microinverter_data| Fetching MI data for plant {plant_id}, inverter {inverter_id}, date {target_date}")
        
        endpoint = f"v2/query/{plant_id}/{inverter_id}/mi_data_day?key={self.api_key}"
        url = f"{self.base_url}/{endpoint}"
        
        body = {"date": target_date}
        
        try:
            logger.info(f"|HoymilesRegister|get_microinverter_data| Making POST request to {url}")
            response = requests.post(url, json=body, timeout=self.timeout)
            response.raise_for_status()
            
            api_response = response.json()
            
            # Check API status
            if api_response.get("status") != "0":
                error_msg = api_response.get("message", "Unknown error")
                logger.error(f"|HoymilesRegister|get_microinverter_data| API error for inverter {inverter_id}: {error_msg}")
                raise RuntimeError(f"Hoymiles API error: {error_msg}")
            
            data = api_response.get("data", [])
            logger.info(f"|HoymilesRegister|get_microinverter_data| Successfully fetched {len(data)} time entries for inverter {inverter_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"|HoymilesRegister|get_microinverter_data| HTTP request failed for inverter {inverter_id}: {e}")
            raise RuntimeError(f"Failed to fetch microinverter data for {inverter_id}: {e}")
        except Exception as e:
            logger.error(f"|HoymilesRegister|get_microinverter_data| Unexpected error for inverter {inverter_id}: {e}")
            raise
    
    def create_granular_objects(self, proyecto, inversor, mi_data):
        """
        Create Granular objects based on the number of ports found in microinverter data.
        
        Args:
            proyecto (Proyecto): The proyecto instance
            inversor (Inversor): The inversor instance
            mi_data (list): Microinverter data from API
            
        Returns:
            int: Number of granular objects created
        """
        logger.info(f"|HoymilesRegister|create_granular_objects| Creating granular objects for inversor {inversor.identificador_inversor}")
        
        # Find the maximum number of ports by examining all data entries
        max_ports = 0
        for entry in mi_data:
            dc_data = entry.get('dc', [])
            if dc_data:
                ports_in_entry = max([dc_port.get('port', 0) for dc_port in dc_data])
                max_ports = max(max_ports, ports_in_entry)
        
        if max_ports == 0:
            logger.warning(f"|HoymilesRegister|create_granular_objects| No ports found in microinverter data for {inversor.identificador_inversor}")
            return 0
        
        logger.info(f"|HoymilesRegister|create_granular_objects| Found {max_ports} ports for inversor {inversor.identificador_inversor}")
        
        created_count = 0
        
        # Create granular objects for each port (following Huawei pattern: serial-port_number)
        for port_number in range(1, max_ports + 1):
            serial_granular = f"{inversor.identificador_inversor}-{port_number}"
            
            try:
                # Check if granular already exists
                if Granular.objects.filter(
                    id_proyecto=proyecto,
                    id_inversor=inversor,
                    serial_granular=serial_granular
                ).exists():
                    logger.info(f"|HoymilesRegister|create_granular_objects| Granular {serial_granular} already exists, skipping")
                    continue
                
                # Create new granular object
                granular = Granular.objects.create(
                    id_proyecto=proyecto,
                    id_inversor=inversor,
                    serial_granular=serial_granular,
                    tipo_granular="MPPT"  # Following Huawei pattern
                )
                
                logger.info(f"|HoymilesRegister|create_granular_objects| Created new Granular: {serial_granular}")
                created_count += 1
                
            except Exception as e:
                logger.error(f"|HoymilesRegister|create_granular_objects| Failed to create granular {serial_granular}: {e}")
                continue
        
        logger.info(f"|HoymilesRegister|create_granular_objects| Created {created_count} granular objects for inversor {inversor.identificador_inversor}")
        return created_count


# Simple function interface for easy usage
def register_hoymiles_project(station_code):
    """
    Simple function to register a new Hoymiles project.
    
    Usage:
        from solarDataNewSystem.register.hoymilesRegister import register_hoymiles_project
        register_hoymiles_project('5561680')
    
    Args:
        station_code (str): The station code to register
        
    Returns:
        tuple: (Proyecto instance, list of Inversor instances)
    """
    logger.info(f"|register_hoymiles_project| Starting registration for station: {station_code}")
    
    register = HoymilesRegister()
    try:
        proyecto, inversores = register.hoymiles_register_new_project(station_code)
        logger.info(f"|register_hoymiles_project| Successfully registered station {station_code}: {len(inversores)} inverters created")
        return proyecto, inversores
    except Exception as e:
        logger.error(f"|register_hoymiles_project| Failed to register station {station_code}: {e}")
        raise


# ============================================================================
# AUTO-REGISTRATION FUNCTIONS
# ============================================================================

def get_hoymiles_plants():
    """
    Fetch all Hoymiles plants from the API with pagination.
    Uses the 'next' field for pagination until all plants are retrieved.
    
    Returns:
        list: List of plant dicts with keys: id, station_name, equipe_capacitor, etc.
    
    Raises:
        RuntimeError: If API request fails or returns error
    """
    logger.info("|HoymilesNewSystem|get_hoymiles_plants| Starting to fetch all Hoymiles plants")
    
    # Get API key from environment
    api_key = os.getenv('HOYMILES_API_KEY')
    if not api_key:
        raise ValueError("HOYMILES_API_KEY environment variable is required")
    
    all_plants = []
    next_cursor = 0
    base_url = "https://wapi.hoymiles.com"
    endpoint = f"v0/zhgf-core/oapi/0/findMyStations?key={api_key}"
    url = f"{base_url}/{endpoint}"
    
    while True:
        body = {"next": next_cursor}
        logger.info(f"|HoymilesNewSystem|get_hoymiles_plants| Fetching plants with next={next_cursor}")
        
        try:
            response = requests.post(url, json=body, timeout=30)
            response.raise_for_status()
            api_response = response.json()
            
            # Check API response status
            if api_response.get("status") != "0":
                error_msg = api_response.get("message", "Unknown error from Hoymiles API")
                logger.error(f"|HoymilesNewSystem|get_hoymiles_plants| Hoymiles API error: {error_msg}")
                raise RuntimeError(f"Hoymiles API error: {error_msg}")
            
            # Extract stations from response
            data = api_response.get("data", {})
            stations = data.get("stations", [])
            
            # Add stations to our list
            all_plants.extend([
                {
                    "id": str(s["id"]),  # Convert to string for consistency
                    "station_name": s.get("station_name", ""),
                    "equipe_capacitor": s.get("equipe_capacitor")
                }
                for s in stations
            ])
            
            logger.info(f"|HoymilesNewSystem|get_hoymiles_plants| Fetched {len(stations)} plants. Total so far: {len(all_plants)}")
            
            # Check if there are more plants to fetch
            next_cursor = data.get("next")
            if not next_cursor or len(stations) == 0:
                logger.info(f"|HoymilesNewSystem|get_hoymiles_plants| No more plants to fetch (next={next_cursor}, stations={len(stations)})")
                break
                
        except requests.RequestException as e:
            logger.error(f"|HoymilesNewSystem|get_hoymiles_plants| API request failed at next={next_cursor}: {e}")
            raise RuntimeError(f"Hoymiles API request failed: {e}") from e
        except Exception as e:
            logger.error(f"|HoymilesNewSystem|get_hoymiles_plants| Unexpected error at next={next_cursor}: {e}")
            raise
    
    logger.info(f"|HoymilesNewSystem|get_hoymiles_plants| Successfully fetched {len(all_plants)} Hoymiles plants")
    return all_plants

def compare_plants_with_database(hoymiles_plants):
    """
    Compare Hoymiles plants from API with existing projects in database.
    
    Args:
        hoymiles_plants (list): List of plant dicts from get_hoymiles_plants()
    
    Returns:
        list: List of new plants not found in database
    """
    logger.info(f"|HoymilesNewSystem|compare_plants_with_database| Comparing {len(hoymiles_plants)} Hoymiles plants with database")
    
    # Get existing Hoymiles project IDs from database (marca_inversor_id=3)
    existing_project_ids = set(
        Proyecto.objects.filter(marca_inversor_id=3).values_list('identificador_planta', flat=True)
    )
    
    logger.info(f"|HoymilesNewSystem|compare_plants_with_database| Found {len(existing_project_ids)} existing Hoymiles projects in database")
    
    # Find plants not in database
    new_plants = []
    for plant in hoymiles_plants:
        if plant['id'] not in existing_project_ids:
            new_plants.append(plant)
            logger.info(f"|HoymilesNewSystem|compare_plants_with_database| Found new plant: {plant['station_name']} (ID: {plant['id']})")
    
    logger.info(f"|HoymilesNewSystem|compare_plants_with_database| Found {len(new_plants)} new plants not in database")
    return new_plants

def create_new_hoymiles_projects(new_plants):
    """
    Create Proyecto entries for new Hoymiles plants.
    
    Args:
        new_plants (list): List of new plant dicts from compare_plants_with_database()
    
    Returns:
        list: List of created Proyecto instances
    
    Raises:
        RuntimeError: If Hoymiles brand (id=3) not found in database
    """
    logger.info(f"|HoymilesNewSystem|create_new_hoymiles_projects| Starting to create {len(new_plants)} new Hoymiles projects")
    
    # Get Hoymiles brand (MarcasInversores id=3)
    try:
        marca_hoymiles = MarcasInversores.objects.get(id=3)
        logger.info(f"|HoymilesNewSystem|create_new_hoymiles_projects| Found Hoymiles brand: {marca_hoymiles.marca}")
    except MarcasInversores.DoesNotExist:
        logger.error("|HoymilesNewSystem|create_new_hoymiles_projects| MarcasInversores with id=3 (Hoymiles) not found in database")
        raise RuntimeError("Hoymiles brand (id=3) not found in database. Please create MarcasInversores with id=3")
    
    created_projects = []
    
    for plant in new_plants:
        plant_id = plant['id']
        plant_name = plant['station_name']
        capacity = plant.get('equipe_capacitor')
        
        try:
            proyecto, created = Proyecto.objects.get_or_create(
                identificador_planta=plant_id,
                defaults={
                    'dealname': plant_name or f"Hoymiles Plant {plant_id}",
                    'fecha_entrada_en_operacion': date.today(),
                    'marca_inversor': marca_hoymiles,
                    'restriccion_de_autoconsumo': False,
                    'capacidad_instalada_ac': capacity if capacity is not None else None,
                    'energia_prometida_mes': None,
                    'energia_minima_mes': None,
                    # id_ciudad will use default from model (1125)
                }
            )
            
            if created:
                created_projects.append(proyecto)
                logger.info(f"|HoymilesNewSystem|create_new_hoymiles_projects| Created new Proyecto: {proyecto.dealname} (ID: {plant_id})")
            else:
                logger.warning(f"|HoymilesNewSystem|create_new_hoymiles_projects| Project already exists: {proyecto.dealname} (ID: {plant_id})")
                
        except Exception as e:
            logger.error(f"|HoymilesNewSystem|create_new_hoymiles_projects| Error creating project {plant_id}: {e}")
            # Continue processing other projects
    
    logger.info(f"|HoymilesNewSystem|create_new_hoymiles_projects| Completed creation of {len(created_projects)} new Hoymiles projects")
    return created_projects

def auto_register_hoymiles_systems():
    """
    Complete auto-registration workflow for Hoymiles systems:
    1. Fetches all Hoymiles plants from the API.
    2. Compares them with existing projects in the database.
    3. Creates new Proyecto entries for missing plants.
    
    Returns:
        dict: A summary of the registration process including:
            - 'total_hoymiles_plants': Total plants found in Hoymiles API
            - 'new_plants_found': Number of new plants not in database
            - 'projects_created': List of newly created Proyecto instances
            - 'errors': List of errors encountered during the process
    """
    logger.info("|HoymilesNewSystem|auto_register_hoymiles_systems| Starting complete Hoymiles auto-registration workflow")
    
    results = {
        'total_hoymiles_plants': 0,
        'new_plants_found': 0,
        'projects_created': [],
        'errors': []
    }
    
    try:
        # 1. Fetch all Hoymiles plants
        hoymiles_plants = get_hoymiles_plants()
        results['total_hoymiles_plants'] = len(hoymiles_plants)
        
        # 2. Compare with database to find new plants
        new_plants = compare_plants_with_database(hoymiles_plants)
        results['new_plants_found'] = len(new_plants)
        
        # 3. Create new Proyecto entries for missing plants
        if new_plants:
            created_projects = create_new_hoymiles_projects(new_plants)
            results['projects_created'] = created_projects
            logger.info(f"|HoymilesNewSystem|auto_register_hoymiles_systems| Created {len(created_projects)} new Hoymiles projects")
        else:
            logger.info("|HoymilesNewSystem|auto_register_hoymiles_systems| No new Hoymiles projects to create")
            
    except Exception as e:
        error_msg = f"Overall error during Hoymiles auto-registration: {e}"
        logger.error(f"|HoymilesNewSystem|auto_register_hoymiles_systems| {error_msg}")
        results['errors'].append(error_msg)
    
    logger.info("|HoymilesNewSystem|auto_register_hoymiles_systems| Hoymiles auto-registration workflow completed")
    return results