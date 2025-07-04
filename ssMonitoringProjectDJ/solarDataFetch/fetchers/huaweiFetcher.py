import requests
import logging
from datetime import datetime
from solarData.models import Proyecto, Inversor
from collections import defaultdict

# Simple logger that will automatically go to CloudWatch via agent
logger = logging.getLogger('huawei_fetcher')

class HuaweiFetcher:
    BASE_URL = "https://la5.fusionsolar.huawei.com/thirdData/"
    LOGIN_BODY = {
        "userName": "api_rocasol",
        "systemCode": "api_rsol1"
    }

    def login(self):
        login_url = self.BASE_URL + "login"
        logger.info(f"Starting Huawei API login attempt to {login_url}")
        
        try:
            response = requests.post(login_url, json=self.LOGIN_BODY)
            response.raise_for_status()  # Raises HTTPError for bad responses
            
            xsrf_token = response.headers.get("xsrf-token")
            if not xsrf_token:
                raise ValueError("xsrf-token not found in response headers")
            
            logger.info(f"Huawei API login successful - token received")
            return xsrf_token
        except requests.exceptions.HTTPError as http_err:
            raise RuntimeError(f"HTTP error occurred during Huawei login: {http_err}") from http_err
        except requests.exceptions.ConnectionError as conn_err:
            raise RuntimeError(f"Connection error occurred during Huawei login: {conn_err}") from conn_err
        except requests.exceptions.Timeout as timeout_err:
            raise RuntimeError(f"Timeout occurred during Huawei login: {timeout_err}") from timeout_err
        except requests.exceptions.RequestException as req_err:
            raise RuntimeError(f"Request exception during Huawei login: {req_err}") from req_err
        except ValueError as val_err:
            raise RuntimeError(f"Login succeeded but response was missing xsrf-token: {val_err}") from val_err
        except Exception as exc:
            raise RuntimeError(f"Unexpected error during Huawei login: {exc}") from exc

    @staticmethod
    def midnight_colombia_timestamp(dt):
        """
        Given a datetime, return the Colombian timezone midnight timestamp in milliseconds.
        Properly handles DST transitions.
        """
        import pytz
        from django.utils import timezone as django_timezone
        
        colombia_tz = pytz.timezone('America/Bogota')
        
        # Ensure the datetime is timezone-aware
        if dt.tzinfo is None:
            dt = django_timezone.make_aware(dt)
            
        # Convert to Colombian timezone and set to midnight
        local_midnight = dt.astimezone(colombia_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        return int(local_midnight.timestamp() * 1000)
    
    def fetch_huawei_generacion_sistema_dia(self, batch_number=1, collect_time=None, token=None):
        """
        Fetches daily solar production data for a batch of Huawei solar systems.

        Args:
            batch_number (int): Which batch of 100 to return (1 = first 100, 2 = second 100, etc.)
            collect_time (int or datetime): The day to fetch, as milliseconds since epoch (UTC midnight) or a datetime (will be converted).
            token (str): The xsrf-token from login (required).

        Returns:
            dict: The parsed JSON response from the Huawei API.
        """
        logger.info(f"Fetching Huawei generation data for batch {batch_number} at {collect_time}")
        if batch_number < 1:
            raise ValueError("batch_number must be >= 1")
        if collect_time is None:
            raise ValueError("collect_time (milliseconds since epoch) is required.")
        if not token:
            raise ValueError("xsrf-token is required as a parameter.")

        # If collect_time is a datetime, convert to Colombian midnight ms
        from datetime import datetime
        if isinstance(collect_time, datetime):
            collect_time = self.midnight_colombia_timestamp(collect_time)

        batch_size = 100
        offset = (batch_number - 1) * batch_size
        qs = Proyecto.objects.filter(marca_inversor_id=1).order_by('id')
        batch = qs[offset:offset + batch_size]
        plant_codes = ','.join([p.identificador_planta for p in batch if p.identificador_planta])
        
        if not plant_codes:
            return {"error": "No Huawei projects found for this batch."}

        url = self.BASE_URL + "getKpiStationDay"
        headers = {
            "xsrf-token": token,
            "Content-Type": "application/json"
        }
        body = {
            "stationCodes": plant_codes,
            "collectTime": collect_time
        }
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        api_response = response.json()

        # Check if user must relogin (failCode 305)
        if (
            api_response.get('failCode') == 305
            and api_response.get('success') is False
            and api_response.get('message') == 'USER_MUST_RELOGIN'
        ):
            raise RuntimeError('Huawei API: USER_MUST_RELOGIN (305). Please re-login.', 305)

        # Check for rate limit error (failCode 407)
        if (
            api_response.get('failCode') == 407
            and api_response.get('success') is False
            and api_response.get('data') == 'ACCESS_FREQUENCY_IS_TOO_HIGH'
        ):
            raise RuntimeError('Huawei API: ACCESS_FREQUENCY_IS_TOO_HIGH (407). Rate limit exceeded.', 407)

        # Extract PVYield for the specified collect_time for each plant
        result = []
        for plant in api_response.get('data', []):
            if plant.get('collectTime') == collect_time:
                station_code = plant.get('stationCode')
                pvyield = plant.get('dataItemMap', {}).get('PVYield')
                result.append({
                    'stationCode': station_code,
                    'collectTime': collect_time,
                    'PVYield': 0 if pvyield in (None, "None") else pvyield
                })
        logger.info(f"Huawei generation data fetched for batch {batch_number} at {collect_time}")
        return result
    
    def fetch_huawei_generacion_inversor_dia(self, dev_type_id, batch_number=1, collect_time=None, token=None):
        """
        Fetch daily generation data for inverters with a given devTypeId.
        Args:
            dev_type_id (str): The devTypeId to filter inverters.
            batch_number (int): Which batch of 100 to return.
            collect_time (int): Timestamp in milliseconds since epoch (midnight Colombian time).
            token (str): Huawei API xsrf-token.
        Returns:
            Raw API response (dict)
        """
        if collect_time is None:
            raise ValueError("collect_time (milliseconds since epoch) is required.")
        if not token:
            raise ValueError("xsrf-token is required as a parameter.")

        batch_size = 100
        offset = (batch_number - 1) * batch_size
        qs = Inversor.objects.filter(huawei_devTypeId=dev_type_id).order_by('id')
        batch = qs[offset:offset + batch_size]
        dev_ids = [inv.identificador_inversor for inv in batch if inv.identificador_inversor]
        dev_ids_str = ",".join(dev_ids)
        if not dev_ids_str:
            return {"error": "No Huawei inverters found for this batch and devTypeId."}

        url = self.BASE_URL + "getDevKpiDay"
        headers = {
            "xsrf-token": token,
            "Content-Type": "application/json"
        }
        body = {
            "devIds": dev_ids_str,
            "devTypeId": dev_type_id,
            "collectTime": collect_time
        }
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        api_response = response.json()

        # Check if user must relogin (failCode 305)
        if (
            api_response.get('failCode') == 305
            and api_response.get('success') is False
            and api_response.get('message') == 'USER_MUST_RELOGIN'
        ):
            raise RuntimeError('Huawei API: USER_MUST_RELOGIN (305). Please re-login.', 305)

        # Check for rate limit error (failCode 407)
        if (
            api_response.get('failCode') == 407
            and api_response.get('success') is False
            and api_response.get('data') == 'ACCESS_FREQUENCY_IS_TOO_HIGH'
        ):
            raise RuntimeError('Huawei API: ACCESS_FREQUENCY_IS_TOO_HIGH (407). Rate limit exceeded.', 407)

        # Build a mapping from the last 8 digits of identificador_inversor to the full identificador_inversor
        batch_inversors = {inv.identificador_inversor[-8:]: inv.identificador_inversor for inv in batch if inv.identificador_inversor}
        
        result = []
        for entry in api_response.get('data', []):
            if entry.get('collectTime') != collect_time:
                continue  # Only keep the day we requested
            dev_id_str = str(entry.get('devId'))
            dev_id_suffix = dev_id_str[-8:]  # last 8 digits
            our_id = batch_inversors.get(dev_id_suffix)
            if not our_id:
                continue  # skip if no mapping found
            product_power = entry.get('dataItemMap', {}).get('product_power')
            result.append({
                'identificador_inversor': our_id,
                'collectTime': collect_time,
                'product_power': 0 if product_power in (None, "None") else product_power,
            })
        return result

    def fetch_huawei_generacion_granular_dia(self, dev_type_id, batch_number=1, collect_time_0=None, collect_time_1=None, token=None):
        """
        Prepares a batch of up to 10 devices of a given dev_type_id for data fetching.

        Args:
            dev_type_id (str or int): The device type ID to filter devices.
            batch_number (int): Which batch of 10 to return (1 = first 10, 2 = second 10, etc.).
            collect_time_0: The start of the time range (not used here).
            collect_time_1: The end of the time range (not used here).
            token: The authentication token (not used here).

        Returns:
            QuerySet: The batch of devices (Inversor objects) for this request.
        """
        if batch_number < 1:
            raise ValueError("batch_number must be >= 1")
        if dev_type_id is None:
            raise ValueError("dev_type_id is required.")

        batch_size = 10
        offset = (batch_number - 1) * batch_size
        qs = Inversor.objects.filter(huawei_devTypeId=dev_type_id).order_by('id')
        batch = qs[offset:offset + batch_size]
        if not batch:
            raise ValueError("No devices found for the given dev_type_id and batch number.")

        # Prepare devIds as a comma-separated string of serials
        dev_ids = ','.join([inv.identificador_inversor for inv in batch if inv.identificador_inversor])
        if not dev_ids:
            raise ValueError("No device serials found in batch.")

        url = self.BASE_URL + "getDevHistoryKpi"
        headers = {
            "xsrf-token": token,
            "Content-Type": "application/json"
        }
        body = {
            "devIds": dev_ids,
            "devTypeId": dev_type_id,
            "startTime": collect_time_0,
            "endTime": collect_time_1
        }

        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        api_response = response.json()

        # Check if user must relogin (failCode 305)
        if (
            api_response.get('failCode') == 305
            and api_response.get('success') is False
            and api_response.get('message') == 'USER_MUST_RELOGIN'
        ):
            raise RuntimeError('Huawei API: USER_MUST_RELOGIN (305). Please re-login.', 305)

        # Check for rate limit error (failCode 407)
        if (
            api_response.get('failCode') == 407
            and api_response.get('success') is False
            and api_response.get('data') == 'ACCESS_FREQUENCY_IS_TOO_HIGH'
        ):
            raise RuntimeError('Huawei API: ACCESS_FREQUENCY_IS_TOO_HIGH (407). Rate limit exceeded.', 407)

        # Process the response to compute energy produced by each MPPT tracker per device
        data = api_response.get("data", [])
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            data = []

        grouped = defaultdict(list)
        for entry in data:
            if not isinstance(entry, dict):
                continue  # Skip unexpected non-dict entries
            dev_id = str(entry["devId"])
            grouped[dev_id].append(entry)

        # Build a mapping from devId to 'NE=' serials (using last digits)
        serial_map = {}
        for inv in batch:
            # Remove any non-digit characters from identificador_inversor for matching
            serial_digits = ''.join(filter(str.isdigit, inv.identificador_inversor))
            for dev_id in grouped.keys():
                if dev_id.endswith(serial_digits):
                    serial_map[dev_id] = inv.identificador_inversor

        results = {}  # Initialize the results dictionary to store energy per device
        for dev_id, records in grouped.items():  # Iterate over each device's grouped records
            # Sort records by time to find first and last
            records.sort(key=lambda x: x["collectTime"])  # Sort the records for this device chronologically
            first = records[0]["dataItemMap"]  # Get the data for the first (earliest) 5-min window
            last = records[-1]["dataItemMap"]  # Get the data for the last (latest) 5-min window
            # Identify all MPPT keys in the data, excluding the total
            mppt_keys = [
                k for k in first.keys()
                if k.startswith("mppt_") and k.endswith("_cap") and k not in ("mppt_total_cap", "mppt-total-cap")
            ]
            mppt_results = {}  # Prepare a dictionary to store the calculated energy for each MPPT
            for key in mppt_keys:  # For each MPPT key
                first_val = first.get(key) or 0  # Get the MPPT value at the start of the day (default 0 if missing)
                last_val = last.get(key) or 0   # Get the MPPT value at the end of the day (default 0 if missing)
                # Only include if not both zero
                if not (first_val == 0 and last_val == 0):  # Ignore this MPPT if both values are zero
                    # Round to 2 decimals
                    mppt_results[key] = round(last_val - first_val, 2)  # Store the energy produced, rounded to 2 decimals
            # Use NE=... serial as key if found, else dev_id
            serial_key = serial_map.get(dev_id, dev_id)  # Use the NE=... serial if available, otherwise use dev_id
            results[serial_key] = mppt_results  # Store the MPPT results for this device in the results dictionary
        return results  # Return the final dictionary mapping NE=... serials (or devIds) to their MPPT energy results