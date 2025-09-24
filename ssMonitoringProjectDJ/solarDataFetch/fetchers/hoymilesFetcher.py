"""
Hoymiles API Fetcher
Handles data collection from Hoymiles solar inverters
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from requests.exceptions import HTTPError, Timeout, RequestException
from json.decoder import JSONDecodeError

# Set up logger
logger = logging.getLogger('hoymiles_fetcher')

class HoymilesFetcher:
    """
    Fetcher class for Hoymiles solar inverter data.
    Handles authentication and data retrieval from Hoymiles API.
    """
    
    def __init__(self):
        """Initialize the Hoymiles fetcher with base configuration."""
        self.base_url = "https://wapi.hoymiles.com"
        self.timeout = 30
        self.api_key = "1.1DCEhvmllSRNl69JJGLFG8OvHpUXXjhjZ"
        
        logger.info("|HoymilesFetcher|__init__| Hoymiles fetcher initialized")
    
    def _make_request(self, endpoint, method='GET', data=None, headers=None):
        """
        Make HTTP request to Hoymiles API with error handling.
        
        Args:
            endpoint (str): API endpoint
            method (str): HTTP method (GET, POST, etc.)
            data (dict): Request payload
            headers (dict): Request headers
            
        Returns:
            dict: API response
            
        Raises:
            RuntimeError: If request fails
        """
        # Add the API key parameter to the URL
        separator = "&" if "?" in endpoint else "?"
        url = f"{self.base_url}/{endpoint}{separator}key={self.api_key}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=data, headers=headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except HTTPError as e:
            logger.error(f"|HoymilesFetcher|_make_request| HTTP error: {e}")
            raise RuntimeError(f"HTTP error: {e}")
        except Timeout as e:
            logger.error(f"|HoymilesFetcher|_make_request| Request timeout: {e}")
            raise RuntimeError(f"Request timeout: {e}")
        except JSONDecodeError as e:
            logger.error(f"|HoymilesFetcher|_make_request| JSON decode error: {e}")
            raise RuntimeError(f"Invalid JSON response: {e}")
        except RequestException as e:
            logger.error(f"|HoymilesFetcher|_make_request| Request error: {e}")
            raise RuntimeError(f"Request error: {e}")

    def fetch_hoymiles_generacion_sistema_dia(self, station_id, target_date):
        """
        Fetch daily energy generation data for a specific Hoymiles station.
        
        Args:
            station_id (str): The station ID
            target_date (str): Target date in YYYY-MM-DD format
            
        Returns:
            list: List of dictionaries containing daily energy data
            
        Raises:
            RuntimeError: If there's an HTTP error, JSON decode error, or API returns error status
        """
        logger.info(f"|HoymilesFetcher|fetch_hoymiles_generacion_sistema_dia| Starting fetch for station {station_id}, date {target_date}")
        
        endpoint = "v0/zhgf-core/oapi/0/findStation30dayEnergy"
        body = {
            "endDate": target_date,
            "stationId": station_id
        }
        
        try:
            response_data = self._make_request(endpoint, method='POST', data=body)
            
            # Check API response status
            if response_data.get("status") != "0":
                error_msg = response_data.get("message", "Unknown error from Hoymiles API")
                raise RuntimeError(f"Hoymiles API error: {error_msg}")
            
            data = response_data.get("data", [])
            
            # Parse data to match our expected format - only return data for the target date
            parsed_data = []
            for entry in data:
                if entry.get("report_date") == target_date:
                    parsed_entry = {
                        "stationCode": station_id,
                        "collectTime": entry.get("report_date"),
                        "PVYield": entry.get("total_energy")/1000
                    }
                    parsed_data.append(parsed_entry)
                    break
            
            logger.info(f"|HoymilesFetcher|fetch_hoymiles_generacion_sistema_dia| Successfully fetched {len(parsed_data)} entries for station {station_id}")
            
            # Print formatted JSON for debugging
            print("Parsed JSON response:")
            print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"|HoymilesFetcher|fetch_hoymiles_generacion_sistema_dia| Error fetching data for station {station_id}: {e}")
            raise

    def fetch_hoymiles_generacion_inversor_granular_dia(self, plant_id, inverter_sn, target_date):
        """
        Fetch inverter and granular energy data for a specific Hoymiles inverter.
        
        Args:
            plant_id (str): The plant/station ID
            inverter_sn (str): The inverter serial number
            target_date (str): Target date in YYYY-MM-DD format
            
        Returns:
            dict: Raw API response containing inverter and granular data
            
        Raises:
            RuntimeError: If there's an HTTP error, JSON decode error, or API returns error status
        """
        logger.info(f"|HoymilesFetcher|fetch_hoymiles_generacion_inversor_granular_dia| Starting fetch for plant {plant_id}, inverter {inverter_sn}, date {target_date}")
        
        # Note: This endpoint has a different URL structure, so we build it manually
        url = f"{self.base_url}/v2/query/{plant_id}/{inverter_sn}/mi_data_day?key={self.api_key}"
        body = {"date": target_date}
        
        try:
            response = requests.post(url, json=body, timeout=self.timeout)
            response.raise_for_status()
            response_data = response.json()
            
            # Check API response status
            if response_data.get("status") != "0":
                error_msg = response_data.get("message", "Unknown error from Hoymiles API")
                raise RuntimeError(f"Hoymiles API error: {error_msg}")
            
            data = response_data.get("data", [])
            
            # Get channel energies from the last available entry (largest time)
            channel_energies = {"channel1": None, "channel2": None, "channel3": None, "channel4": None}
            
            if data:
                # Find the entry with the largest time (last available)
                last_entry = max(data, key=lambda x: x.get("time", "00:00"))
                dc_data = last_entry.get("dc", [])
                
                # Extract "tp" values for each port and convert from W to kW
                for dc_entry in dc_data:
                    port = dc_entry.get("port")
                    tp_value = dc_entry.get("tp")
                    
                    # Convert from W to kW by dividing by 1000
                    tp_value_kw = tp_value / 1000.0 if tp_value is not None else None
                    
                    if port == 1:
                        channel_energies["channel1"] = tp_value_kw
                    elif port == 2:
                        channel_energies["channel2"] = tp_value_kw
                    elif port == 3:
                        channel_energies["channel3"] = tp_value_kw
                    elif port == 4:
                        channel_energies["channel4"] = tp_value_kw
            
            # Calculate microinverter total energy as sum of all 4 channels
            total_microinverter_energy = 0.0
            for channel_key in ["channel1", "channel2", "channel3", "channel4"]:
                channel_value = channel_energies[channel_key]
                if channel_value is not None:
                    total_microinverter_energy += channel_value
            
            # Build the return structure
            parsed_data = {
                "stationCode": plant_id,
                "inverter_sn": inverter_sn,
                "collectTime": target_date,
                "PVYield": total_microinverter_energy,
                "channel1": channel_energies["channel1"],
                "channel2": channel_energies["channel2"],
                "channel3": channel_energies["channel3"],
                "channel4": channel_energies["channel4"]
            }
            
            logger.info(f"|HoymilesFetcher|fetch_hoymiles_generacion_inversor_granular_dia| Successfully processed {len(data)} time entries for plant {plant_id}, inverter {inverter_sn}")
            logger.info(f"|HoymilesFetcher|fetch_hoymiles_generacion_inversor_granular_dia| Total microinverter energy: {total_microinverter_energy} kW, Channels: {channel_energies}")
            
            # Print formatted JSON for debugging
            print("Parsed JSON response:")
            print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
            
            return parsed_data
            
        except HTTPError as e:
            logger.error(f"|HoymilesFetcher|fetch_hoymiles_generacion_inversor_granular_dia| HTTP error: {e}")
            raise RuntimeError(f"HTTP error: {e}")
        except Timeout as e:
            logger.error(f"|HoymilesFetcher|fetch_hoymiles_generacion_inversor_granular_dia| Request timeout: {e}")
            raise RuntimeError(f"Request timeout: {e}")
        except JSONDecodeError as e:
            logger.error(f"|HoymilesFetcher|fetch_hoymiles_generacion_inversor_granular_dia| JSON decode error: {e}")
            raise RuntimeError(f"Invalid JSON response: {e}")
        except RequestException as e:
            logger.error(f"|HoymilesFetcher|fetch_hoymiles_generacion_inversor_granular_dia| Request error: {e}")
            raise RuntimeError(f"Request error: {e}")
        except Exception as e:
            logger.error(f"|HoymilesFetcher|fetch_hoymiles_generacion_inversor_granular_dia| Error fetching data for plant {plant_id}, inverter {inverter_sn}: {e}")
            raise


