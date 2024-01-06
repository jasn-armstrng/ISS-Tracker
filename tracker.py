import json
import logging
import requests
from configparser import ConfigParser
from datetime import datetime


logging.basicConfig(
    handlers=[logging.FileHandler("./logs/execution.log"),logging.StreamHandler()],
    format='%(asctime)s: %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %I:%M:%S %p',
    level=logging.INFO
)


config = ConfigParser()
config.read("config.ini")
ISS_NOW_URL = config["Open-Notify"]["url"]
REV_GEO_URL = config["Geoapify"]["url"]
REV_GEO_KEY = config["Geoapify"]["key"]


def get_data_from_api(url: str, api_key: str=None) -> json:
    """Returns json object result of API data fetch"""
    try:
        request = requests.get(url)
        if request.status_code >= 400:
            invalid_request_reason = request.text
            logging.error(f"Your request has failed because: {invalid_request_reason}")
            return
    except requests.exceptions.ConnectionError as err:
        raise SystemExit(err)

    return request.json()


def unixtime_to_date(timestamp: int) -> str:
    """Retuns UTC time from UNIX timestamp"""
    utc_time = datetime.utcfromtimestamp(timestamp)
    return utc_time.strftime("%Y-%m-%d %H:%M:%S+00:00 (UTC)")


def parse_iss_now_data(data: json) -> dict:
    """Returns a object with partial details of the ISS's position"""
    timestamp = data.get("timestamp", None)
    latitude  = data.get("iss_position", None).get("latitude", None)
    longitude = data.get("iss_position", None).get("longitude", None)
    return {'timestamp': unixtime_to_date(timestamp), 'latitude': latitude, 'longitude': longitude}


def reverse_geolocate(lat: str, long: str) -> json:
    """Return reverse geolocation details in JSON"""
    URL = f"{REV_GEO_URL}?lat={lat}&lon={long}&apiKey={REV_GEO_KEY}"
    location = get_data_from_api(URL)
    return location


def parse_revgeo_data(data: json) -> str:
    """Returns address formatted address from reverse geolocation"""
    address = data.get("features", None)[0].get("properties", None).get("formatted", None)
    return address


if __name__ == "__main__":
    iss_now = get_data_from_api(ISS_NOW_URL)
    where_is_iss = parse_iss_now_data(iss_now)
    # pprint(where_is_iss)
    # Next:
    # • Pass where_is_iss lat, long to reverse-geolocating function
    addressing = reverse_geolocate(where_is_iss['latitude'], where_is_iss['longitude'])  # This can fail if ISS now has missing data
    # • Identify the addressing fields to be used from results returned
    # pprint(addressing)
    # • Complete speciification of WhereIsISSOver
    # • Pass where_is_iss lat, long to reverse geolocation parser
    address = parse_revgeo_data(addressing)
    # • Update where_is_iss
    where_is_iss['address'] = address
    logging.info(where_is_iss)
    # -> {'timestamp': '2024-01-06 04:39:44+00:00 (UTC)', 'latitude': '-11.4986', 'longitude': '57.0169', 'address': 'Indian Ocean'}
