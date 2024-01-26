#### ISS Tracker - Data ETL *ver.0.1*


###### To do
```
- Handle errors from db write
- Write logs to db
- Compile to executable
- Replace .sh with executable in launchd
- Separate production and development branches
```


###### Dependencies
```Python
import json
import logging
import requests
import questdb.ingress as qdb
import textwrap
import time
from datetime import datetime
from utils import config
```


###### Configurations
```Python
logging.basicConfig(
    handlers=[logging.FileHandler(config["Paths"]["log"]),logging.StreamHandler()],
    format='%(asctime)s: %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %I:%M:%S %p',
    level=logging.INFO
)
```


###### Helper functions
```Python
def time_this(func):
    """Return function runtime; timing decorator"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.info(f"Time taken by {func.__name__}: {end_time - start_time} seconds")
        return result
    return wrapper


def unixtime_to_date(timestamp: int) -> str:
    """Converts UNIX timestamp to UTC time in the format YYYY-MM-DD HH:MM:SS+00:00 (UTC)"""
    return datetime.fromtimestamp(timestamp)
```


###### ISS Data Extract
- Use to both get current data about the ISS and reverse-geolocating its lat/long.
```Python
@time_this
def get_data_from_api(url: str) -> json:
    """Returns json object result of API data fetch"""
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
```


###### ISS Data Transform
- Convert the unix timestamp from the ISS' about data record to datetime
- Add the address at ground-level the ISS is over to the 'about' data record.
```Python
def transform_iss_data(data: json) -> dict:
    """Transform ISS data Record"""

    def reverse_geolocate(lat: str, long: str) -> json:
        """Return reverse geolocation details"""
        REV_GEO_URL = config["Geoapify"]["url"]
        REV_GEO_KEY = config["Geoapify"]["key"]
        URL = f"{REV_GEO_URL}?lat={lat}&lon={long}&apiKey={REV_GEO_KEY}"
        return get_data_from_api(URL)

    def reverse_geolocated_address(data: json) -> str:
        """Returns formatted address from geolocation data"""
        try:
            return data["features"][0]["properties"]["formatted"]
        except (KeyError, IndexError):
            logging.error("Invalid geolocation data format")
            return ""

    data['timestamp'] = unixtime_to_date(data['timestamp'])
    logging.info("Reverse Geolocate ISS Lat/Long")
    geo_data = reverse_geolocate(data['latitude'], data['longitude'])
    address = reverse_geolocated_address(geo_data)
    data['geolocated_address'] = address
    return data
```


###### ISS Data Load
- Writes the data to the local time-series database (`QuestDB`)
- Script source: `https://py-questdb-client.readthedocs.io/en/latest/`
```Python
def load_iss_data(data: dict) -> None:
    """Write data to (local) Time-series DB"""
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
```


###### ISS Data ETL (main-entry-point)
```Python
def extract_transform_load() -> None:
    logging.info("Fetch ISS data")
    WIS_ISS_URL = config["Where-is-ISS"]["url"]
    iss_data = get_data_from_api(WIS_ISS_URL)
    if iss_data:
        logging.info("Transform ISS data")
        iss_data_transform = transform_iss_data(iss_data)
        logging.info("Load ISS data")
        load_iss_data(iss_data_transform)
    else:
        logging.error("No data received")
```
