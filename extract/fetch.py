## Extract raw data from FuelEconomy.gov with my Mpg Endpoints

import json
import sys
import time
from datetime import datetime,timezone
from pathlib import Path

import requests

BASE = "https://www.fueleconomy.gov/ws/rest/"
DELAY = 0.2  ##seconds between requests
MAX_RETRIES = 2  ##attempts after a 500 or network error
YEARS = range(2015,2021)

RAW = Path(__file__).resolve().parent.parent /"data" / "raw"

session = requests.Session()
session.headers.update({"Accept":"application/json"})

request_count = 0

def fetch(path, params=None):  ## making one GET request, retrying 500s and network errors. Returning status and body
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


def parse (body, key): ## Turning response into a list whether API sent a list or a single object
    if not body:
        return[]
    try:
        value = json.loads(body).get(key)
    except ValueError:
        return[]
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def build_url(path, params=None):  ##Building full URL as the request would send it
    return requests.Request("GET", BASE + path, params=params).prepare().url

def load_saved(file): ##Returning url&record for every response already saved in a jsonl file.
     saved ={}
     if file.exists():
         with open(file, encoding = "utf-8") as f:
             for line in f :
                 record = json.loads(line)
                 saved [record["url"]] = record
                 return saved

def get(file, saved, path, params=None): ##Returning the body for a request, using the saved copy if it is there saved already

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


def safe_name(text): ##sensible name to use as a file name
    return "".join(c if c.isalnum()else "_" for c in text)

def main(only_make = None):
    (RAW / "shared_vehicles").mkdir(parents=True, exist_ok=True)
    (RAW / "driver_record").mkdir(parents=True, exist_ok=True)

    makes_file = RAW / "shared_makes.jsonl"
    models_file = RAW / "shared_models.jsonl"
    makes_saved = load_saved(makes_file)
    models_saved = load_saved(models_file)

    body = get(makes_file, makes_saved, "ympg/shared/menu/model")
    models = [item["value"] for item in parse(body,"menuItem")]
    print(f"{len(makes)}makes")
    if only_make:
        makes = [m for m in makes if m == only_make]

    for make in makes:
        print(f"\n[make]")
        vehicles_file = RAW / "shared_vehicles" / f"{safe_name(make)}.jsonl"
        drivers_file = RAW / "driver_records" / f"{safe_name(make)}.jsonl"
        vehicles_saved = load_saved(vehicles_file)
        drivers_saved = load_saved(drivers_file)

        body = get(models_file, models_saved, "ympg/shared/menu/model", {"make":make} )
        models = [item["value"] for item in parse(body,"menuItem")]
        
        in_range = 0
        for model in models:
            body = get(vehicles_file, vehicles_saved,"ympg/shared/vehicles",{"make": make, "model":model})

            for vehicle in parse(body,"vehicle"):
                if int(vehicle["year"]) in YEARS:
                    in_range +=1
                    get(drivers_file, drivers_saved, f"ympg/shared/ympgDriverVehicle/{vehicle['id']}")

            print(f"{len(models)} models, {in_range} vehicles in 2015-2020")

        print(f"\nDone. Requests made this run :{request_count}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv)> 1 else None)
    




