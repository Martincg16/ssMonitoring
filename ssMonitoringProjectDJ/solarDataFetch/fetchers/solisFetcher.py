import requests
from datetime import datetime, timezone
import hashlib
import base64
import json
import hmac

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
        import json
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
        Fetch daily energy data for all registered Solis plants (structure only).
        Uses /v1/api/stationDayEnergyList endpoint.
        For now, only prepares and prints the request details.
        """
        endpoint = "/v1/api/stationDayEnergyList"
        # Placeholder body; update as needed for real request
        body = {"pageNo":f"{batch_number}", "pageSize": 100, "time": collect_time}
        headers = self.build_solis_headers("POST", endpoint, body)

        try:
            response = requests.post(self.url + endpoint, headers=headers, json=body)
            response.raise_for_status()  # Raises HTTPError for 4XX/5XX responses
            parsed = response.json()
            
            # Check if the API returned an error in the JSON body
            if not parsed.get("success", False):
                error_msg = parsed.get("msg", "Unknown error from Solis API")
                error_code = parsed.get("code", "N/A")
                raise RuntimeError(f"Solis API error (code {error_code}): {error_msg}")
                
            # Transform to required output structure
            result_list = [
                {
                    "id": rec["id"],
                    "collectTime": rec["dateStr"],
                    "PVYield": rec["energy"]
                }
                for rec in parsed.get("data", {}).get("records", [])
            ]
            return result_list
            
        except requests.exceptions.HTTPError as http_err:
            raise RuntimeError(f"HTTP error occurred: {http_err}") from http_err
        except json.JSONDecodeError as json_err:
            raise RuntimeError(f"Failed to parse JSON response: {json_err}") from json_err
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}") from e

    def fetch_solis_generacion_inversor_dia_data(self, batch_number=1):
        """
        Fetch inverter data from Solis API.
        
        Args:
            batch_number (int): Page number for pagination (starts at 1).
            
        Returns:
            list: List of dictionaries containing inverter data with keys:
                - 'identificador_inversor' (str): The inverter ID.
                - 'collectTime' (int): Timestamp in milliseconds.
                - 'PVYield' (float): Power output of the inverter.
                
        Raises:
            RuntimeError: If there's an HTTP error, JSON decode error, or API returns success=False.
        """
        endpoint = "/v1/api/inverterDetailList"
        body = {
            "pageNo": str(batch_number),
            "pageSize": 100
        }
        headers = self.build_solis_headers("POST", endpoint, body)

        try:
            response = requests.post(self.url + endpoint, headers=headers, json=body)
            response.raise_for_status()
            parsed = response.json()
            
            # 🔍 PRINT RAW RESPONSE - NICE AND ORGANIZED
            print("=" * 80)
            print("🌟 SOLIS INVERTER API RAW RESPONSE:")
            print("=" * 80)
            print(json.dumps(parsed, indent=4, ensure_ascii=False))
            print("=" * 80)
            
            if not parsed.get("success", False):
                error_msg = parsed.get("msg", "Unknown error from Solis API")
                error_code = parsed.get("code", "N/A")
                raise RuntimeError(f"Solis API error (code {error_code}): {error_msg}")
            
            # Transform to match Huawei's output format
            result_list = []
            for rec in parsed.get("data", {}).get("records", []):
                # Extract inverter ID and power (adjust field names based on actual API response)
                inverter_id = rec.get("inverterId") or rec.get("id")
                power = rec.get("power") or rec.get("pac", 0)  # Use actual power field from API
                
                if inverter_id:
                    result_list.append({
                        'identificador_inversor': str(inverter_id),
                        'collectTime': int(rec.get("collectTime", 0)),
                        'PVYield': float(power) if power not in (None, "None") else 0.0
                    })
            
            return result_list
            
        except requests.exceptions.HTTPError as http_err:
            raise RuntimeError(f"HTTP error occurred: {http_err}") from http_err
        except json.JSONDecodeError as json_err:
            raise RuntimeError(f"Failed to parse JSON response: {json_err}") from json_err
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}") from e
        
    def fetch_solis_generacion_un_inversor_dia(self, inverter_id, collect_time):
        """
        Fetch inverter data from Solis API.
        
        Args:
            batch_number (int): Page number for pagination (starts at 1).
            
        Returns:
            list: List of dictionaries containing inverter data with keys:
                - 'identificador_inversor' (str): The inverter ID.
                - 'collectTime' (int): Timestamp in milliseconds.
                - 'PVYield' (float): Power output of the inverter.
                
        Raises:
            RuntimeError: If there's an HTTP error, JSON decode error, or API returns success=False.
        """
        endpoint = "/v1/api/inverterDay"
        body = {
            "id": inverter_id,
            "time": collect_time,
            "timeZone": -5,
            "money": "COP"
        }
        headers = self.build_solis_headers("POST", endpoint, body)

        try:
            response = requests.post(self.url + endpoint, headers=headers, json=body)
            response.raise_for_status()
            parsed = response.json()

            # Extract last eToday value and format output
            data_array = parsed.get("data", [])
            if not data_array:
                raise RuntimeError("No data found in API response")
            
            # Get the last entry (latest time)
            last_entry = data_array[-1]
            etoday_value = last_entry.get("eToday", 0)
            
            # Extract date from the JSON response (timeStr format: "2025-06-18 18:35:41")
            time_str = last_entry.get("timeStr", "")
            from datetime import datetime
            date_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            formatted_date = date_obj.strftime("%d-%m-%Y")
            
            # Create output in requested format
            result = {
                'identificador_inversor': f'{inverter_id}',
                'collectTime': formatted_date,
                'PVYield': float(etoday_value)
            }
            
            return result
            
        except requests.exceptions.HTTPError as http_err:
            raise RuntimeError(f"HTTP error occurred: {http_err}") from http_err
        except json.JSONDecodeError as json_err:
            raise RuntimeError(f"Failed to parse JSON response: {json_err}") from json_err
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}") from e