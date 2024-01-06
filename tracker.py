import json
import requests
from datetime import datetime
from dataclasses import dataclass
from rich import print as pprint  # Makes deeply nested JSON easy to read
from typing import Any


@dataclass
class WhereIsISSOver:
    """Class for <to complete meaningfully>"""
    timestamp: str
    latitude: str
    longitude: str
    address: str = ""


def get_data_from_api(url: str, api_key: str=None) -> json:
    """Returns json object result of API data fetch"""
    try:
        request = requests.get(url)
        if request.status_code >= 400:
            invalid_request_reason = request.text
            print(f"Your request has failed because: {invalid_request_reason}")
            return
    except requests.exceptions.ConnectionError as err:
        raise SystemExit(err)

    return request.json()


def unixtime_to_date(timestamp: int) -> str:
    """Retuns UTC time from UNIX timestamp"""
    utc_time = datetime.utcfromtimestamp(timestamp)
    return utc_time.strftime("%Y-%m-%d %H:%M:%S+00:00 (UTC)")


def parse_iss_now_data(data: json) -> Any:
    """Returns a object with partial details of the ISS's position"""
    timestamp = data.get("timestamp", None)
    latitude  = data.get("iss_position", None).get("latitude", None)
    longitude = data.get("iss_position", None).get("longitude", None)
    record = WhereIsISSOver(unixtime_to_date(timestamp), latitude, longitude)
    return record


def reverse_geolocate(lat: str, long: str) -> json:
    API_KEY = "5a004b63903e44148e465009b91f48e2"
    URL = f"https://api.geoapify.com/v1/geocode/reverse?lat={lat}&lon={long}&apiKey={API_KEY}"
    location = get_data_from_api(URL)
    return location


# def parse_revgeo_data(data: json) -> Any:
#     address = data.get("features", None)[0].get("properties", None).get("formatted", None)
#     return address


if __name__ == "__main__":
    ISS_NOW_URL = "http://api.open-notify.org/iss-now.json"
    iss_now = get_data_from_api(ISS_NOW_URL)
    where_is_iss = parse_iss_now_data(iss_now)
    pprint(where_is_iss)
    # Next:
    # • Pass where_is_iss lat, long to reverse-geolocating function
    addressing = reverse_geolocate(where_is_iss.latitude, where_is_iss.longitude)
    # • Identify the addressing fields to be used from results returned
    pprint(addressing)
    # • Complete speciification of WhereIsISSOver
    # • Pass where_is_iss lat, long to reverse-geolocating function
    # address = parse_revgeo_data(addressing)
    #   and update WhereIsISSOver
    # where_is_iss.address = address
    # print(where_is_iss) # WhereIsISSOver(timestamp='2024-01-06 04:10:32+00:00 (UTC)', latitude='50.8165', longitude='-48.5167', address='North Atlantic Ocean')
