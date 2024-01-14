import json
import logging
import requests
import questdb.ingress as qdb
import textwrap
import time
from datetime import datetime
from utils import config


WIS_ISS_URL = config["Where-is-ISS"]["url"]
REV_GEO_URL = config["Geoapify"]["url"]
REV_GEO_KEY = config["Geoapify"]["key"]
LOG_FILE = config["Paths"]["log"]


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
    return datetime.fromtimestamp(timestamp)


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


def load_iss_data(data: dict) -> None:
    """Write data to Time-series DB"""
    try:
        with qdb.Sender('localhost', 9009) as sender:
            sender.row(
                'iss_tracker',
                columns=data,
                at=data['timestamp'])
            pending = str(sender)
            logging.info('About to flush:\n%s', textwrap.indent(pending, '    '))
            sender.flush()
    except qdb.IngressError as e:
        logging.error(f"{e}")


def transform_iss_data(data: json) -> dict:
    """Transform ISS data Record"""
    data['timestamp'] = unixtime_to_date(data['timestamp'])
    logging.info("Reverse Geolocate ISS Lat/Long")
    geo_data = reverse_geolocate(data['latitude'], data['longitude'])
    address = reverse_geolocated_address(geo_data)
    data['geolocated_address'] = address
    return data


def main() -> None:
    logging.info("Fetch ISS data")
    iss_data = get_data_from_api(WIS_ISS_URL)
    if iss_data:
        logging.info("Transform ISS data")
        iss_data_transform = transform_iss_data(iss_data)
        logging.info("Load ISS data")
        load_iss_data(iss_data_transform)
    else:
        logging.error("No data received")
    # Next:
    # - Handle errors from db write
    # - Maybe write logs to db
    # - Compile to executable
    # - Replace .sh with executable in launchd
    # - Create a build system
