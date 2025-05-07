import requests
from solarData.models import Proyecto, Inversor

def register_and_fetch_huawei_history(token, station_code, start_time, end_time):
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
    # --- 1. Register inverters from API ---
    url = "https://la5.fusionsolar.huawei.com/thirdData/getDevList"
    headers = {
        "XSRF-TOKEN": token,
        "Content-Type": "application/json",
    }
    body = {"stationCodes": station_code}
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    api_response = response.json()

    try:
        proyecto = Proyecto.objects.get(identificador_planta=station_code)
    except Proyecto.DoesNotExist:
        raise ValueError(f"No Proyecto found with identificador_planta='{station_code}'")

    inverters = []
    dev_dns = []  # This will be the devDn ("NE=...") for each inverter
    dev_type_id = None
    for dev in api_response.get("data", []):
        # devTypeId: "1" or "38" (string or int)
        if str(dev.get("devTypeId")) in ("1", "38"):
            inversor, _ = Inversor.objects.update_or_create(
                identificador_inversor=dev["devDn"],  # devDn is for display and API
                id_proyecto=proyecto,
                defaults={
                    "huawei_devTypeId": str(dev["devTypeId"]),
                }
            )
            inverters.append(inversor)
            dev_dns.append(dev["devDn"])  # This is the devDn (string) required by the history API
            dev_type_id = str(dev["devTypeId"])  # All should be the same for the project

    if not dev_dns or not dev_type_id:
        raise ValueError("No inverters with devTypeId 1 or 38 found for this project.")

    # --- 2. Fetch history KPI for all these devices ---
    url = "https://la5.fusionsolar.huawei.com/thirdData/getDevHistoryKpi"
    body = {
        "devIds": ",".join(dev_dns),
        "devTypeId": dev_type_id,
        "startTime": start_time,
        "endTime": end_time
    }
    resp = requests.post(url, headers=headers, json=body)
    resp.raise_for_status()
    history_response = resp.json()
    return inverters, history_response
