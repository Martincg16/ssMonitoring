import requests
from datetime import datetime, timezone
import hashlib
import base64
import json
import hmac

url = "https://www.soliscloud.com:13333"
key_id="1300386381677289904"
key_secret="313d4528cec14085b68a33608fb401c5"
#key_secret="6680182547"

def process_data_to_base64_md5(body):
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

def generate_signature(string_to_sign):
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
    hmac_sha1 = hmac.new(key_secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod='sha1')
    signature = base64.b64encode(hmac_sha1.digest()).decode('utf-8')
    return signature

def date():
    """
    Returns the current time in GMT in the format:
    EEE, d MMM yyyy HH:mm:ss 'GMT'
    Example: Fri, 23 May 2025 19:53:00 GMT
    """
    now = datetime.now(timezone.utc)
    # Compose the string manually to avoid zero-padding on day
    return now.strftime('%a, ') + str(now.day) + now.strftime(' %b %Y %H:%M:%S GMT')

def build_solis_headers(method, endpoint, body, content_type="application/json"):
    """
    Build Solis API headers (Content-MD5, Date, Authorization, etc.) for any endpoint and body.
    Returns the headers dict ready for requests.
    """
    md5 = process_data_to_base64_md5(body)
    my_date = date()
    string_to_sign = (
        f"{method}\n"
        f"{md5}\n"
        f"{content_type}\n"
        f"{my_date}\n"
        f"{endpoint}"
    )
    signature = generate_signature(string_to_sign)
    headers = {
        "Content-Type": content_type,
        "Content-MD5": md5,
        "Date": my_date,
        "Authorization": f"API {key_id}:{signature}"
    }
    return headers

def list_plants_api():
    endpoint = "/v1/api/userStationList"
    body = {"pageNo":1,"pageSize":100}
    headers = build_solis_headers("POST", endpoint, body)
    response = requests.post(url + endpoint, headers=headers, json=body)
    try:
        parsed = response.json()
        print("Parsed JSON response:")
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    except Exception as e:
        print("Response is not valid JSON:", e)
    return response