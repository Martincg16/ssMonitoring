import requests
from solarData.models import Proyecto, Inversor

class HuaweiFetcher:
    BASE_URL = "https://la5.fusionsolar.huawei.com/thirdData/"
    LOGIN_BODY = {
        "userName": "api_rocasol",
        "systemCode": "api_rsol1"
    }

    def login(self):
        login_url = self.BASE_URL + "login"
        try:
            response = requests.post(login_url, json=self.LOGIN_BODY)
            response.raise_for_status()  # Raises HTTPError for bad responses
            xsrf_token = response.headers.get("xsrf-token")
            if not xsrf_token:
                raise ValueError("xsrf-token not found in response headers")
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
    def midnight_gmt5_timestamp(dt):
        """
        Given a datetime, return the GMT-5 midnight timestamp in milliseconds.
        """
        from datetime import timezone, timedelta, datetime
        gmt5 = timezone(timedelta(hours=-5))
        local_midnight = dt.astimezone(gmt5).replace(hour=0, minute=0, second=0, microsecond=0)
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
        if batch_number < 1:
            raise ValueError("batch_number must be >= 1")
        if collect_time is None:
            raise ValueError("collect_time (milliseconds since epoch) is required.")
        if not token:
            raise ValueError("xsrf-token is required as a parameter.")

        # If collect_time is a datetime, convert to UTC midnight ms
        from datetime import datetime
        if isinstance(collect_time, datetime):
            collect_time = self.midnight_gmt5_timestamp(collect_time)

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

        # Extract PVYield for the specified collect_time for each plant
        result = []
        for plant in api_response.get('data', []):
            if plant.get('collectTime') == collect_time:
                station_code = plant.get('stationCode')
                pvyield = plant.get('dataItemMap', {}).get('PVYield')
                result.append({
                    'stationCode': station_code,
                    'collectTime': collect_time,
                    'PVYield': pvyield
                })
        return result
    
    def fetch_huawei_generacion_inversor_dia(self, dev_type_id, batch_number=1, collect_time=None, token=None):
        """
        Fetch daily generation data for inverters with a given devTypeId.
        Args:
            dev_type_id (str): The devTypeId to filter inverters.
            batch_number (int): Which batch of 100 to return.
            collect_time (int): Timestamp in milliseconds since epoch (midnight GMT-5).
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
                'product_power': product_power,
            })
        return result
