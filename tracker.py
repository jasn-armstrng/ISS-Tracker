import json
import requests


def get_data_from_api(url: str, api_key: str=None) -> json:
    try:
        request = requests.get(url)
        # process the specific codes from the range 400-599
        # that you are interested in first
        if request.status_code == 400:
            invalid_request_reason = request.text
            print(f"Your request has failed because: {invalid_request_reason}")
            return
        # this will handle all other errors
        elif request.status_code > 400:
            print(f"Your request has failed with status code: {request.status_code}")
            return
    except requests.exceptions.ConnectionError as err:
        raise SystemExit(err)

    return request.json()


if __name__ == "__main__":
    ISS_NOW_URL = "http://api.open-notify.org/iss-now.json"
    iss_now = get_data_from_api(ISS_NOW_URL)
    timestamp = iss_now.get("timestamp", None)
    latitude  = iss_now.get("iss_position", None).get("latitude", None)
    longitude = iss_now.get("iss_position", None).get("longitude", None)
    print(f"{timestamp}: {latitude}, {longitude}")
