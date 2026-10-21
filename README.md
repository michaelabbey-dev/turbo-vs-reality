
# Turbo vs Reality

Do turbocharged petrol cars deliver their official fuel economy in real-world driving, compared with naturally aspirated cars?

**Status:** in progress. Data extraction is complete; data shaping in DuckDB is under way.

## Who this is for
- Someone buying a used car who is choosing between a small turbocharged engine and a larger naturally aspirated one. Official MPG figures often favour the turbo, but turbos are known to be more sensitive to how they're driven. This project compares official EPA figures with fuel economy reported by real drivers, so the buyer can see whether the turbo's advantage holds up.

## Data source
- U.S. Department of Energy, fueleconomy.gov web services (https://www.fueleconomy.gov/feg/ws/). Used for non-commercial, educational purposes in line with the site's copyright statement.

The pipeline uses two kinds of data:
- **Official vehicle records:** EPA city, highway and combined MPG, engine size, cylinders, and turbo/supercharger flags.
- **Real-world driver records:** MPG submitted by drivers, with each driver's share of city and highway driving.

## Scope
- Model years 2015 to 2020
- Petrol cars only (diesel, hybrid, plug-in hybrid, electric and flex-fuel vehicles are excluded)
- Turbocharged vs naturally aspirated (supercharged and twincharged cars are excluded, as there are only 21 in range)

## How it works

### 1. Extract (`extract/fetch.py`) – complete
- Walks the API's shared-data menus: makes → models → vehicles, then fetches driver records for each vehicle in 2015–2020.
- Saves every response untouched as JSON Lines in `data/raw/`, alongside the URL and the time it was fetched.
- Pauses 0.2 seconds between requests, retries server errors and dropped connections, and can resume after a crash without re-fetching anything.
- The full run made 3,972 requests in about 40 minutes and collected 1,519 vehicles with 3,325 driver records.

### 2. Shape (`transform/`) – in progress
SQL in DuckDB, in three layers:
- **Staging:** one row per vehicle and per driver record, with correct types.
- **Clean:** scope rules, engine type classification, and data quality flags.
- **Final:** each driver's expected MPG for their own mix of city and highway driving, and the gap between expected and actual.

### 3. Output – not started

## Key decisions
- **Comparing fairly:** the official combined figure assumes 55% city / 45% highway driving. Each driver is instead compared against an expected figure for their own driving mix, using a harmonic weighting that reproduces the EPA's combined figure exactly.
- **Missing driving mix:** 464 driver records have no city/highway split recorded. Rather than drop 14% of the data, these are compared against the EPA's standard mix and labelled as such.
- **Raw data is never modified:** all cleaning happens in SQL, so every result can be traced back to the original response.

Full reasoning, findings and the decision log are in [`NOTES.md`](NOTES.md).

## How to run
Requires Python 3.11+.
git clone <https://github.com/michaelabbey-dev/turbo-vs-reality>
cd turbo-vs-reality
python -m venv .venv
.venv\Scripts\activate # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python extract/fetch.py #raw data is already committed
`python extract/fetch.py Honda` fetches a single make, which is useful for testing.

## Known limitations
- US-market data only, so some models and engines differ from UK cars.
- Only vehicles with driver-submitted data are included, so popular models are over-represented.
- Driver records are self-reported and many vehicles have only one or two drivers.