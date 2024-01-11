import json
import logging
import requests
import time
from datetime import datetime
from rich import print as pprint

from utils import config


WIS_ISS_URL = config["Where-is-ISS"]["url"]
REV_GEO_URL = config["Geoapify"]["url"]
REV_GEO_KEY = config["Geoapify"]["key"]
LOG_FILE = config["Paths"]["log"]
LOCATIONS_FILE = config["Paths"]["locations"]


logging.basicConfig(
    handlers=[logging.FileHandler(LOG_FILE),logging.StreamHandler()],
    format='%(asctime)s: %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %I:%M:%S %p',
    level=logging.INFO
)


def time_this(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.info(f"Time taken by {func.__name__}: {end_time - start_time} seconds")
        return result
    return wrapper


@time_this
def get_data_from_api(url: str) -> json:
    """Returns json object result of API data fetch or logs an error"""
    try:
        response = requests.get(url)
        if response.status_code >= 400:
            invalid_request_reason = response.text
            print(f"Your request has failed because: {invalid_request_reason}")
            return {}
        else:
            return response.json()
    except requests.exceptions.ConnectionError as err:
        logging.error(f"Your request has failed because: {err}")


def unixtime_to_date(timestamp: int) -> str:
    """Converts UNIX timestamp to UTC time in the format YYYY-MM-DD HH:MM:SS+00:00 (UTC)"""
    return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S+00:00 (UTC)")


def reverse_geolocate(lat: str, long: str) -> json:
    """Return reverse geolocation details"""
    URL = f"{REV_GEO_URL}?lat={lat}&lon={long}&apiKey={REV_GEO_KEY}"
    return get_data_from_api(URL)


def reverse_geolocated_address(data: json) -> str:
    """Extracts and returns formatted address from geolocation data"""
    try:
        return data["features"][0]["properties"]["formatted"]
    except (KeyError, IndexError):
        logging.error("Invalid geolocation data format")
        return ""


def transform_iss_data() -> None:
    logging.info("Fetch ISS data")
    iss_data = get_data_from_api(WIS_ISS_URL)
    if iss_data:
        logging.info("Reverse Geolocate Lat/Long")
        geo_data = reverse_geolocate(iss_data['latitude'], iss_data['longitude'])
        address = reverse_geolocated_address(geo_data)
        logging.info("Update ISS data Record")
        iss_data['address'] = address
        return iss_data
    return {}


def main() -> None:
    iss_data = transform_iss_data()
    # To do: write iss_data to DB
