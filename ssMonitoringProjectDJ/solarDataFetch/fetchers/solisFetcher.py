import requests
import json
import hashlib
import base64
import hmac
import pytz
import logging
from datetime import datetime, timezone
from solarData.models import Proyecto

# Set up logger for Solis fetcher operations
logger = logging.getLogger('solis_fetcher')

class SolisFetcher:
    url = "https://www.soliscloud.com:13333"
    key_id="1300386381677289904"
    key_secret="313d4528cec14085b68a33608fb401c5"

    def process_data_to_base64_md5(self, body):
        """
        Processes a string body or dict by:
        1. (If dict) Serializing to JSON string with canonical separators.
        2. Performing MD5 hashing on the body.
        3. Taking the resulting 128-bit binary hash.
        4. Base64 encoding this binary hash.

        Args:
            body (str or dict): The input string or dict to process.

        Returns:
            str: The Base64 encoded string of the MD5 hash of the body.
        """
        if isinstance(body, dict):
            body = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        encoded_body = body.encode('utf-8')
        md5_hasher = hashlib.md5()
        md5_hasher.update(encoded_body)
        binary_md5_hash = md5_hasher.digest()
        base64_encoded_bytes = base64.b64encode(binary_md5_hash)
        base64_encoded_string = base64_encoded_bytes.decode('ascii')
        return base64_encoded_string

    def generate_signature(self, string_to_sign):
        """
        Generates a digital signature for Solis API:
        - Uses HMAC-SHA1 with the provided secret key.
        - Base64 encodes the result.
        - The string_to_sign should use literal '\n' line breaks.
        Args:
            string_to_sign (str): The canonical string to sign.
        Returns:
            str: The base64-encoded HMAC-SHA1 signature.
        """
        hmac_sha1 = hmac.new(self.key_secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod='sha1')
        signature = base64.b64encode(hmac_sha1.digest()).decode('utf-8')
        return signature

    def get_colombia_timezone_offset(self, target_date=None):
        """
        Calculate the Colombian timezone offset for a given date.
        Handles DST transitions properly.
        
        Args:
            target_date (datetime or str): The date to check. If None, uses current date.
            
        Returns:
            int: Timezone offset in hours (e.g., -5 or -4)
        """
        colombia_tz = pytz.timezone('America/Bogota')
        
        if target_date is None:
            target_date = datetime.now()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d")
            
        # Create a datetime in Colombian timezone
        if target_date.tzinfo is None:
            # Make it timezone-aware in UTC first, then convert
            target_date = pytz.utc.localize(target_date)
        
        colombia_time = target_date.astimezone(colombia_tz)
        
        # Get the UTC offset in seconds and convert to hours
        offset_seconds = colombia_time.utcoffset().total_seconds()
        offset_hours = int(offset_seconds / 3600)
        
        return offset_hours

    def date(self):
        """
        Returns the current time in GMT in the format:
        EEE, d MMM yyyy HH:mm:ss 'GMT'
        Example: Fri, 23 May 2025 19:53:00 GMT
        """
        now = datetime.now(timezone.utc)
        # Compose the string manually to avoid zero-padding on day
        return now.strftime('%a, ') + str(now.day) + now.strftime(' %b %Y %H:%M:%S GMT')

    def build_solis_headers(self, method, endpoint, body, content_type="application/json"):
        """
        Build Solis API headers (Content-MD5, Date, Authorization, etc.) for any endpoint and body.
        Returns the headers dict ready for requests.
        """
        md5 = self.process_data_to_base64_md5(body)
        my_date = self.date()
        string_to_sign = (
            f"{method}\n"
            f"{md5}\n"
            f"{content_type}\n"
            f"{my_date}\n"
            f"{endpoint}"
        )
        signature = self.generate_signature(string_to_sign)
        headers = {
            "Content-Type": content_type,
            "Content-MD5": md5,
            "Date": my_date,
            "Authorization": f"API {self.key_id}:{signature}"
        }
        return headers

    def fetch_solis_generacion_sistema_dia(self, batch_number=1, collect_time=None):
        """
        Fetch daily energy data for Solis plants.
        Uses /v1/api/stationDayEnergyList endpoint.
        Returns data with PVYield=0 for any system with no data.
        """
        logger.info(f"|SolisFetcher|fetch_solis_generacion_sistema_dia| Starting Solis system generation data fetch for batch {batch_number} on date {collect_time}")
        
        endpoint = "/v1/api/stationDayEnergyList"
        body = {"pageNo":f"{batch_number}", "pageSize": 100, "time": collect_time}
        headers = self.build_solis_headers("POST", endpoint, body)

        try:
            logger.info(f"|SolisFetcher|fetch_solis_generacion_sistema_dia| Making Solis API call to {self.url + endpoint} for batch {batch_number}")
            response = requests.post(self.url + endpoint, headers=headers, json=body)
            response.raise_for_status()
            parsed = response.json()
            
            # Log the full API response for debugging
            try:
                response_json_str = json.dumps(parsed, ensure_ascii=False, separators=(',', ':'))
                # Truncate if very large (>5000 chars) to avoid log bloat
                if len(response_json_str) > 5000:
                    truncated_response = response_json_str[:5000] + "... [TRUNCATED]"
                    logger.info(f"|SolisFetcher|fetch_solis_generacion_sistema_dia| API response for batch {batch_number} (TRUNCATED): {truncated_response}")
                else:
                    logger.info(f"|SolisFetcher|fetch_solis_generacion_sistema_dia| API response for batch {batch_number}: {response_json_str}")
            except Exception as e:
                logger.warning(f"|SolisFetcher|fetch_solis_generacion_sistema_dia| Could not serialize API response for logging: {e}")
            
            # Check if the API returned an error in the JSON body
            if not parsed.get("success", False):
                error_msg = parsed.get("msg", "Unknown error from Solis API")
                error_code = parsed.get("code", "N/A")
                logger.error(f"|SolisFetcher|fetch_solis_generacion_sistema_dia| Solis API returned error for batch {batch_number}: {error_msg} (code {error_code})")
                raise RuntimeError(f"Solis API error (code {error_code}): {error_msg}")
                
            # Transform to required output structure, ensuring PVYield is 0 when no data
            result_list = [
                {
                    "id": rec["id"],
                    "collectTime": rec["dateStr"],
                    "PVYield": rec["energy"] if rec.get("energy") is not None else 0
                }
                for rec in parsed.get("data", {}).get("records", [])
            ]
            
            logger.info(f"|SolisFetcher|fetch_solis_generacion_sistema_dia| Solis system generation data fetched successfully for batch {batch_number}: {len(result_list)} systems")
            return result_list
            
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"|SolisFetcher|fetch_solis_generacion_sistema_dia| HTTP error in Solis system fetch for batch {batch_number}: {http_err}")
            raise RuntimeError(f"HTTP error occurred: {http_err}") from http_err
        except json.JSONDecodeError as json_err:
            logger.error(f"|SolisFetcher|fetch_solis_generacion_sistema_dia| JSON decode error in Solis system fetch for batch {batch_number}: {json_err}")
            raise RuntimeError(f"Failed to parse JSON response: {json_err}") from json_err
        except Exception as e:
            logger.error(f"|SolisFetcher|fetch_solis_generacion_sistema_dia| Unexpected error in Solis system fetch for batch {batch_number}: {e}")
            raise RuntimeError(f"Unexpected error: {e}") from e

    def fetch_solis_generacion_un_inversor_dia(self, inverter_id, collect_time):
        """
        Fetch inverter data from Solis API.
        
        Args:
            inverter_id (str): The ID of the inverter to fetch data for.
            collect_time (str): The date to collect data for in YYYY-MM-DD format.
            
        Returns:
            dict: Dictionary containing inverter data with keys:
                - 'identificador_inversor' (str): The inverter ID.
                - 'collectTime' (str): Date in DD-MM-YYYY format.
                - 'PVYield' (float): Power output of the inverter.
                
        Raises:
            RuntimeError: If there's an HTTP error, JSON decode error, or API returns success=False.
        """
        logger.info(f"|SolisFetcher|fetch_solis_generacion_un_inversor_dia| Starting Solis inverter data fetch for inverter {inverter_id} on date {collect_time}")
        
        endpoint = "/v1/api/inverterDay"
        body = {
            "id": inverter_id,
            "time": collect_time,
            "timeZone": self.get_colombia_timezone_offset(collect_time),
            "money": "COP"
        }
        headers = self.build_solis_headers("POST", endpoint, body)

        try:
            logger.info(f"|SolisFetcher|fetch_solis_generacion_un_inversor_dia| Making Solis API call to {self.url + endpoint} for inverter {inverter_id}")
            response = requests.post(self.url + endpoint, headers=headers, json=body)
            response.raise_for_status()
            parsed = response.json()
            
            # Log the full API response for debugging
            try:
                response_json_str = json.dumps(parsed, ensure_ascii=False, separators=(',', ':'))
                # Truncate if very large (>5000 chars) to avoid log bloat
                if len(response_json_str) > 5000:
                    truncated_response = response_json_str[:5000] + "... [TRUNCATED]"
                    logger.info(f"|SolisFetcher|fetch_solis_generacion_un_inversor_dia| API response for inverter {inverter_id} (TRUNCATED): {truncated_response}")
                else:
                    logger.info(f"|SolisFetcher|fetch_solis_generacion_un_inversor_dia| API response for inverter {inverter_id}: {response_json_str}")
            except Exception as e:
                logger.warning(f"|SolisFetcher|fetch_solis_generacion_un_inversor_dia| Could not serialize API response for logging: {e}")
            
            # Extract last eToday value and format output
            data_array = parsed.get("data", [])
            if not data_array:
                logger.warning(f"|SolisFetcher|fetch_solis_generacion_un_inversor_dia| No data found for Solis inverter {inverter_id} on {collect_time}, returning 0 production")
                # Return 0 production if no data found
                return {
                    'identificador_inversor': f'{inverter_id}',
                    'collectTime': datetime.strptime(collect_time, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    'PVYield': 0.0
                }
            
            # Get the last entry (latest time)
            last_entry = data_array[-1]
            etoday_value = last_entry.get("eToday", 0)  # Default to 0 if no eToday value
            
            # Extract date from the JSON response (timeStr format: "2025-06-18 18:35:41")
            time_str = last_entry.get("timeStr", "")
            date_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            formatted_date = date_obj.strftime("%d-%m-%Y")
            
            # Create output in requested format
            result = {
                'identificador_inversor': f'{inverter_id}',
                'collectTime': formatted_date,
                'PVYield': float(etoday_value) if etoday_value is not None else 0.0  # Convert None to 0
            }
            
            logger.info(f"|SolisFetcher|fetch_solis_generacion_un_inversor_dia| Solis inverter data fetched successfully for inverter {inverter_id}: PVYield = {result['PVYield']} kWh")
            return result
            
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"|SolisFetcher|fetch_solis_generacion_un_inversor_dia| HTTP error in Solis inverter fetch for {inverter_id}: {http_err}")
            raise RuntimeError(f"HTTP error occurred: {http_err}") from http_err
        except json.JSONDecodeError as json_err:
            logger.error(f"|SolisFetcher|fetch_solis_generacion_un_inversor_dia| JSON decode error in Solis inverter fetch for {inverter_id}: {json_err}")
            raise RuntimeError(f"Failed to parse JSON response: {json_err}") from json_err
        except Exception as e:
            logger.error(f"|SolisFetcher|fetch_solis_generacion_un_inversor_dia| Unexpected error in Solis inverter fetch for {inverter_id}: {e}")
            raise RuntimeError(f"Unexpected error: {e}") from e