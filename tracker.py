import json
import requests
from datetime import datetime
from dataclasses import dataclass
from typing import Any


@dataclass
class WhereIsISSOver:
    """Class for <to complete meaningfully>"""
    timestamp: str
    latitude: str
    longitude: str


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


def parse_iss_now_data(data: dict) -> Any:
    """Returns a object with partial details of the ISS's position"""
    timestamp = data.get("timestamp", None)
    latitude  = data.get("iss_position", None).get("latitude", None)
    longitude = data.get("iss_position", None).get("longitude", None)
    record = WhereIsISSOver(unixtime_to_date(timestamp), latitude, longitude)
    return record


if __name__ == "__main__":
    ISS_NOW_URL = "http://api.open-notify.org/iss-now.json"
    iss_now = get_data_from_api(ISS_NOW_URL)
    where_is_iss = parse_iss_now_data(iss_now)
    # Next:
    # • Pass where_is_iss lat, long to reverse-geolocating function
    # • Identify the addressing fields to be used from results returned
    # • Complete speciification of WhereIsISSOver
    # • Pass where_is_iss lat, long to reverse-geolocating function
    #   and update WhereIsISSOver
