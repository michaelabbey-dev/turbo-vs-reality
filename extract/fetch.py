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


def build_url(path, params=None):
    return requests.Request("GET", BASE + path, params=params).prepare().url

def load_saved(file):
     saved ={}
     if file.exists():
         with open(file, encoding = "utf-8") as f:
             for line in f :
                 record = json.loads(line)
                 saved [record["url"]] = record
                 return saved

def get(file, saved, path, params=None):

    url = build_url(path, params)
    if url in saved:
        return saved[url]["body"]

    status, body = fetch(path, params)
    if status in (200,204,404):
        record = {
            "url": url,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "body": body,
        }
        with open(file, "a", encoding ="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        saved [url] = record
        return body
    print(f" gave up on {url} (status{status}), will retry on next run")
    return None



    




