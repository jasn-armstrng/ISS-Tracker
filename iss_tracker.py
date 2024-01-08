import json
import logging
import requests
from datetime import datetime

from utils import config


ISS_NOW_URL = config["Open-Notify"]["url"]
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


def parse_iss_data(data: json) -> dict:
    """Extracts and returns ISS position (lat, long) and timestamp"""
    try:
        timestamp = data["timestamp"]
        position = data["iss_position"]
        return {
            'timestamp': unixtime_to_date(timestamp),
            'latitude': position["latitude"],
            'longitude': position["longitude"]
        }
    except KeyError:
        logging.error("Invalid ISS data format")
        return {}


def reverse_geolocate(lat: str, long: str) -> json:
    """Return reverse geolocation details"""
    URL = f"{REV_GEO_URL}?lat={lat}&lon={long}&apiKey={REV_GEO_KEY}"
    return get_data_from_api(URL)


def get_formatted_address(data: json) -> str:
    """Extracts and returns formatted address from geolocation data"""
    try:
        return data["features"][0]["properties"]["formatted"]
    except (KeyError, IndexError):
        logging.error("Invalid geolocation data format")
        return ""


def iss_position() -> None:
    iss_data = get_data_from_api(ISS_NOW_URL)
    if iss_data:
        _iss_position = parse_iss_data(iss_data)
        if iss_position:
            geo_data = reverse_geolocate(_iss_position['latitude'], _iss_position['longitude'])
            address = get_formatted_address(geo_data)
            _iss_position['address'] = address
            return _iss_position
    return {}


def main() -> None:
    iss_pos = iss_position()

    with open(LOCATIONS_FILE, "a") as file:
        if iss_pos:
            file.write(f"{iss_pos['timestamp']};ISS;{iss_pos['latitude']},{iss_pos['longitude']};{iss_pos['address']}\n")
        else:
            logging.info("No data")
