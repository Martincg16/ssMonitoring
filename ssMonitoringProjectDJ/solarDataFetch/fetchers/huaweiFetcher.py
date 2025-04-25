import requests
from solarData.models import Proyecto

class HuaweiFetcher:
    LOGIN_URL = "https://la5.fusionsolar.huawei.com/thirdData/login"
    LOGIN_BODY = {
        "userName": "api_rocasol",
        "systemCode": "api_rsol1"
    }

    def login(self):
        try:
            response = requests.post(self.LOGIN_URL, json=self.LOGIN_BODY)
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
    def fetch_huawei_solar_production():
        """
        Fetch and return solar production data for Proyectos with marca_inversor_id=1 (Huawei).
        For now, this only queries the database and prepares the data structure.
        """
        proyectos = Proyecto.objects.filter(marca_inversor_id=1)
        data = []
        for proyecto in proyectos:
            data.append({
                'id': proyecto.id,
                'dealname': proyecto.dealname,
                'ciudad': proyecto.ciudad,
                'departamento': proyecto.departamento,
                'fecha_entrada_en_operacion': proyecto.fecha_entrada_en_operacion,
                'restriccion_de_autoconsumo': proyecto.restriccion_de_autoconsumo,
                'identificador_marca': proyecto.identificador_marca,
                'marca_inversor': proyecto.marca_inversor.marca if proyecto.marca_inversor else None,
            })
        return data
