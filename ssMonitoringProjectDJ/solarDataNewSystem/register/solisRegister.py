import requests
from datetime import datetime, timezone
import hashlib
import base64
import json
import hmac

from solarData.models import Proyecto, Inversor, MarcasInversores
from datetime import date
import logging

logger = logging.getLogger(__name__)

class SolisRegister:
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

    def solis_obtain_inverter_list(self, batch_number=1):
        """
        Fetch daily energy data for all registered Solis plants (structure only).
        Uses /v1/api/stationDayEnergyList endpoint.
        For now, only prepares and prints the request details.
        """
        endpoint = "/v1/api/inverterList"
        # Placeholder body; update as needed for real request
        body = {
            "pageNo":f"{batch_number}", "pageSize": 100
            }
        headers = self.build_solis_headers("POST", endpoint, body)

        try:
            response = requests.post(self.url + endpoint, headers=headers, json=body)
            response.raise_for_status()  # Raises HTTPError for 4XX/5XX responses
            parsed = response.json()
            
            # Extract only inverter_id and plant_id from the response
            inverter_list = []
            records = parsed.get("data", {}).get("page", {}).get("records", [])
            
            for record in records:
                inverter_id = record.get("id")
                plant_id = record.get("stationId")
                station_name = record.get("stationName")
                power = record.get("power")
                
                if inverter_id and plant_id:
                    inverter_list.append({
                        "inverter_id": inverter_id,
                        "plant_id": plant_id,
                        "station_name": station_name,
                        "power": power
                    })
            
            return inverter_list
            
        except requests.exceptions.HTTPError as http_err:
            raise RuntimeError(f"HTTP error occurred: {http_err}") from http_err
        except json.JSONDecodeError as json_err:
            raise RuntimeError(f"Failed to parse JSON response: {json_err}") from json_err
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}") from e
        
    def solis_register_new_project(self):
        """
        Register all Solis projects and inverters in the database.
        Loops through all pages to get complete inverter list.
        """
        
        # Get Solis brand (marca_inversor_id = 2)
        try:
            marca_solis = MarcasInversores.objects.get(id=2)
        except MarcasInversores.DoesNotExist:
            logger.error("MarcasInversores with id=2 (Solis) not found in database")
            raise RuntimeError("Solis brand not found in database. Please create MarcasInversores with id=2")
        
        total_projects_created = 0
        total_inverters_created = 0
        batch_number = 1
        
        while True:
            print(f"🔄 Processing batch {batch_number}...")
            
            # Get inverter list for current batch
            inverter_data = self.solis_obtain_inverter_list(batch_number)
            
            if not inverter_data:
                print(f"✅ No more data found at batch {batch_number}. Stopping.")
                break
            
            # Group inverters by plant_id to avoid duplicate projects
            plants_data = {}
            for item in inverter_data:
                plant_id = item["plant_id"]
                if plant_id not in plants_data:
                    plants_data[plant_id] = {
                        "station_name": item["station_name"],
                        "power": item["power"],
                        "inverters": []
                    }
                plants_data[plant_id]["inverters"].append(item["inverter_id"])
            
            # Process each plant
            for plant_id, plant_info in plants_data.items():
                # Create or get project
                proyecto, created = Proyecto.objects.get_or_create(
                    identificador_planta=plant_id,
                    defaults={
                        'dealname': plant_info["station_name"] or f"Solis Plant {plant_id}",
                        'ciudad': '',  # Empty as not provided by API
                        'departamento': '',  # Empty as not provided by API
                        'fecha_entrada_en_operacion': date.today(),  # Only set on creation
                        'restriccion_de_autoconsumo': False,
                        'marca_inversor': marca_solis,
                        'capacidad_instalada_ac': plant_info["power"] or 0
                    }
                )
                
                if created:
                    total_projects_created += 1
                    logger.info(f"✅ Created new Proyecto: {proyecto.dealname} (ID: {plant_id})")
                    print(f"✅ Created project: {proyecto.dealname}")
                else:
                    logger.info(f"⚡ Project already exists: {proyecto.dealname} (ID: {plant_id})")
                    print(f"⚡ Project exists: {proyecto.dealname}")
                
                # Create inverters for this project
                for inverter_id in plant_info["inverters"]:
                    inversor, inv_created = Inversor.objects.get_or_create(
                        identificador_inversor=inverter_id,
                        defaults={
                            'id_proyecto': proyecto
                        }
                    )
                    
                    if inv_created:
                        total_inverters_created += 1
                        logger.info(f"✅ Created new Inversor: {inverter_id} for project {proyecto.dealname}")
                        print(f"  ✅ Created inverter: {inverter_id}")
                    else:
                        logger.info(f"⚡ Inversor already exists: {inverter_id}")
                        print(f"  ⚡ Inverter exists: {inverter_id}")
            
            # Check if we got less than 100 items (last page)
            if len(inverter_data) < 100:
                print(f"✅ Last batch processed (got {len(inverter_data)} items). Stopping.")
                break
            
            batch_number += 1
        
        return {
            "batches_processed": batch_number,
            "projects_created": total_projects_created,
            "inverters_created": total_inverters_created
        }
