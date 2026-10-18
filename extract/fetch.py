## Extract raw data from FuelEconomy.gov with my Mpg Endpoints

import json
import sys
import time
from datetime import datetime,timezone
from pathlib import Path

import requests

BASE = "https://www.fueleconomy.gov/ws/rest/"
DELAY = 0.2
MAX_RETRIES = 2
YEARS = range(2015,2021)

RAW = Path(__file__).resolve().parent.parent /"data" / "raw"

session = requests.Session()
session.headers.update({"Accept":"application/json"})

request_count = 0

def fetch(path, params=None):
    global request_count
    for attempt in range(MAX_RETRIES + 1):
        time.sleep(DELAY)
        request_count +=1
        try:
            resp = session.get( BASE + path, params=params, timeout=30)
        except requests.RequestException as err:
            print(f" network error({err}), attempt {attempt +1}")
            time.sleep(2)
            continue
        if resp.status_code >= 500 and attempt < MAX_RETRIES:
            print (f"{resp.status_code} on {resp.url}, retrying")
            time.sleep(2)
            continue
        return resp.status_code, resp.text
    return None, None


def parse (body, key):
    if not body:
        return[]
    try:
        value = json.loads(body).get(key)
    except ValueError:
        return[]
    if value is None:
        return []
    return value if isinstance(value, list) else [value]



    




