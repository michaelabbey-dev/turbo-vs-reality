## This project is answering the question of "Comparing the offical data to the real world MPG for turbocharged cars and naturally aspirated

Audience: someone buying a used car who is choosing between a small turbocharged engine and a larger naturally aspirated one, and wants to know whether the turbo's official MPG advantage holds up in real-world driving.

## API
The API studied for this project is from the U.S Deparment of Energy, does not require a key for access and it naturally returns XMl by default. 

To get the data returned as JSON instead, send the request header `Accept: application/json` 

## Licence check
 https://www.fueleconomy.gov/
  The fueleconomy.gov copyright statement says documents from the site were produced by a contractor of the U.S. Government (contract DE-AC05-00OR22725) and "may be freely distributed and used for non-commercial, scientific and educational purposes". This project is a non-commercial, educational portfolio project, so publishing the raw responses and outputs in a public repo fits within these terms. Vehicle photographs are separately copyrighted by the manufacturers, but my pipeline doesn't fetch any. The driver records are anonymous (US state only, no names), so there's no personal data concern. I will credit fueleconomy.gov as the source in the README.

## Endpoints explored
https://www.fueleconomy.gov/ws/rest/vehicle/menu/year
 The returned XML from this endpoint is the year of  available models years. 

https://www.fueleconomy.gov/ws/rest/vehicle/menu/make?year=2020
The inputs for this endpoints is the year 2020, which returns values of different makes of vehicles for that year such as Aston Martini, Audi and etc.

https://www.fueleconomy.gov/ws/rest/vehicle/menu/model?year=2020&make=Ford
This endpoint returns the models for that year and the make.

https://www.fueleconomy.gov/ws/rest/vehicle/menu/options?year=2020&make=Ford&model=Mustang
The input for this endpoint is 2020, Ford and Mustang. The return endpoint outputs the style of transmission, the amount of cyclinders, engine size, turbocharged or naturally aspirated and a vehicle ID.
The vehicle ID is used for the next request to specify data for that particular vehicle 

https://www.fueleconomy.gov/ws/rest/vehicle/41952
This endpoint returns data such as the emission, fuel score, class of car and the urban and motoway MPG. It also returns whether users have uploaded any real MPG scores.

https://www.fueleconomy.gov/ws/rest/ympg/shared/ympgVehicle/41952
This endpoint return no results, there was no error 500 at all.


## Things i found
A malformed vehicle ID (e.g. with curly brackets) returns a 500 server error rather than a 400 (bad request) or 404 (not found). This means my script can't tell from the status code alone whether the server failed or I sent a bad request, so I can't just retry every 500. I'll need to validate IDs before sending them and limit how many times a failed request is retried.

https://www.fueleconomy.gov/ws/rest/vehicle/{41952}
This endpoint with curly brackets results in an server  error 500 - "There is a problem with the resource you are looking for, and it cannot be displayed"

I also found that when i requested for the real world MPG for 41952, there was no results, no error at all. This indicates that there is no entry for
 by drivers who have submitted their own figures regarding MPG. 

 From looking on,
 https://www.fueleconomy.gov/ws/rest/vehicle/41952
 a giveaway sign whether an vehicle has real world MPG figures is by seeing whether this field "mpgData" has values "Y" for yes and "N" for no. This tells in advance if a vehicle has real world MPG figures or not.
 
 So my script will only call the real-world MPG endpoint for vehicles where mpgData = Y, which avoids wasted requests. I will NOT drop the other vehicles from the dataset. I need them to measure coverage (what share of vehicles have real-world data) and to check whether turbo or naturally aspirated cars are better represented, which could bias the comparison.

 This API was decided over the MOT API as it did not require a key and a 5 day wait for approval. The MoT API requires the reg number for each lookup, whereas this API i can lookup any vehicle by usin the menu. In particular, it has direct turbo and supercharger fields, which is more suited to my question.


 ## 12 Oct: explored the menu endpoints, found the mpgData field.


ID: 38248
 - 1.5T 6s manual results:
 - Engine Type: TurboCharged
 - Transmission: Manual 6-spd
 - Offical figures Rounded: city08:31, highway08:42, comb08:35, 
 - Offical figures Unrounded: city08:30.9997, highway08:42.1485, comb08:35.1882, 
 - Real world summary: avgMPG:38.280173986, recordcount:2, cityPercent:51, highwayPercent:49, maxMpg:46, minMpg:33,  
 - Driver record1:Mpg:46.2, cityPercent:20, highwayPercent:80 , lastdate: 2018-02-23T00:00:00-05:00
 - Driver record2:Mpg:32.678302361, cityPercent:83, highwayPercent:18, lastdate: 2018-01-04T00:00:00-05:00

 ID: 38247
 - 2.0 NA CVT Auto results:
 - Engine Type: Naturally Aspirated NA
 - Transmission:Automatic (variable gear ratios) CVT
 - Offical figures Rounded: city08:28, highway08:40, comb08:32, 
 - Offical figures Unrounded: city08:28.0, highway08:40.0499, comb08:32.3846, 
 - Real world summary: avgMPG:57.0, recordcount:1, cityPercent:10, highwayPercent:90, maxMpg:57, minMpg:57,  
 - Driver record:Mpg:57, cityPercent:10, highwayPercent:90, recordCount: 1, lastdate: 2020-05-30T00:00:00-04:00
- Side note: no results for manual 2.0 NA engine

The comparisons of these two results show that the gap for Naturally Aspirated engines and Turbocharged is massive, however these results tell me a lot and nothing at the same time.
First off, the sample used for the Civics is tiny, there is a total of 3 driver records, which indicates that there should be a minimun recordCount before using a vehicles real-world figures.
The next point is that the 57mpg figure for 2.0 NA engine is most likey an outlier of a result. This is well above the the car's offical highway figure of 40mpg. There could be a few factors for this figure, a data entry mistake, someone driving extremely economical or even a short sample.For the process of cleaning the data, i will most likey flag any extreme outliers, as excluding them is not accurate as it may actually be achievable in some rare cases. 

Another finding was the driving mix between the two engine types. The NA driver did 90% highway miles, which is unfair to compare against the 49% and 18% for the driver record of the 1.5T engines. Using the comb08 as the measurement for this isn't fair, so i will most likey calculate the offical figure for each driver's own mix, resulting in the harmonic mix.

Another comparision is the transmission types. A manual and an CVT transmission differ in gearboxes, which is an example of a cofounder in this case.

Driving mix percentages: Some driver records don't add up to 100% (e.g. vehicle 38248, driver 2: 83% city + 18% highway = 101%). I checked the raw response, and this is in the data, not a mistake in my notes. Where the total is between 95 and 105, I'll treat the difference as rounding and rescale both values so they sum to 100% (83/18 becomes 82.2/17.8). Where it's outside that range, or both are zero, I'll flag the record and exclude it from the mix-adjusted comparison, but keep it in the data. I'll keep the raw percentages alongside the rescaled ones so the change is visible. Once I have the full dataset, I'll count how many records fall outside the tolerance to check the rule is sensible.

Dates: lastDate comes back as a timestamp with a timezone offset (e.g. 2018-02-23T00:00:00-05:00).  I'll keep only the date (2018-02-23), since I only need it at day or year level for checking how recent a record is. The raw string stays in staging and the clean date goes in the final table.
 
 ## 13 Oct: explored 1.5t and 2.0 NA engines, 1.5t manuel ID 38248, 2.0 NA Auto ID 38247

 ## Postman
 Test 1: https://www.fueleconomy.gov/ws/rest/vehicle/38248
 - status: 200
 - Time taken : 180.24 ms
 - Format : XML

 Test 2: Json
 - https://www.fueleconomy.gov/ws/rest/vehicle/38248
 - Adding header with the key 'Accept' and values 'application/json'
 - Results:  "atvType": "",
    "barrels08": "8.500285714285715",
    "barrelsA08": "0.0",
    "battery": "-1",

 Json with the same data, everything is in quotation, even numerical values, indicating it is a string and not a integer. The empty values are not null but are empty strings.

 Test 3: A menu with some items
 The structure of the Json while using the header 'Accept' and the value being 'application/json' is:
 "menuItem": [
        {
            "text": "Acura",
            "value": "Acura"
        },]

 Test 4: Menu with single item
 https://www.fueleconomy.gov/ws/rest/vehicle/menu/model?year=2019&make=Bugatti
 - Status: 200
 - Time Taken: 1.97ms
 - Request result: {
    "menuItem": {
        "text": "Chiron",
        "value": "Chiron"
    }
}

 Test 5: Error cases
 - Bad ID:
 - https://www.fueleconomy.gov/ws/rest/vehicle/abc
 - Status - 404 Not found
 - Time Taken -203ms

 Wrong model name -
 - https://www.fueleconomy.gov/ws/rest/vehicle/menu/options?year=2017&make=Honda&model=Civic
 - Status - 20o
 - Time Taken - 212ms
 - Request results: null

 Requests with no data:
 - https://www.fueleconomy.gov/ws/rest/ympg/shared/ympgVehicle/41952
 - Status: 204
 - Time Taken:1.98ms
 - Message: No content 

 Test 6: Limits and headers
 - After retrying successful requests such as : https://www.fueleconomy.gov/ws/rest/vehicle/38247, - https://www.fueleconomy.gov/ws/rest/ympg/shared/ympgDriverVehicle/38248
-  On the headers section there was no rate limit header found so ill add my own delays between requests to be safe.

  Summary of tests:

 Findings:
 - Sending the header `Accept: application/json` returns JSON; without it, the API returns XML.
 - Every value comes back as a string, including numbers ("31", "8.5002...").
 - Empty values come back as empty strings (""), not null. For example, sCharger and tCharger are "" on the NA Civic (38247) and atvType is "" on 38248.
 - Some numeric fields use -1 to mean "not available" (e.g. battery, and feScore/ghgScore according to the documentation).
 - Menus with several items return a list (`"menuItem": [ ... ]`), but a menu with one item returns a single object (`"menuItem": { ... }`) with no list.
 - A non-numeric vehicle ID returns 404. A malformed URL (curly brackets) returned 500.
 - A wrong model name returns an empty menu, not an error.
 - A vehicle with no real-world data returns 204 (no content).
 - No rate limit headers were found.

 Decisions:
 - Always send `Accept: application/json` on every request.
 - Convert every field to its proper type in staging (numbers, dates), because nothing arrives typed.
 - Convert empty strings to NULL in staging, so "missing" is handled the same way everywhere.
 - Treat -1 in numeric fields as NULL, not as a real value, so it doesn't distort averages.
 - Classify engines from tCharger/sCharger: "T" = turbocharged, "S" = supercharged, both empty = naturally aspirated.
 - Handle menus that return either a list or a single object, otherwise single-item menus would break the script.
 - Treat a 204 as "no data" and record it, rather than treating it as an error.
 - Never retry a 404. Retry a 500 at most twice, with a delay.
 - Log a warning when a menu comes back empty, because a wrong name fails silently.
 - Pause between every request, since no rate limits are published.
 
## Scope Decisions
The years of vehicles i will be taking into account for this project is from 2015-2020. This is as there will be more data to be manipulated and more likey more data of driver records. Also, with this range, small cars with small turbos became more common, instead of high powered vehicles.

I will be taking the shared menu approach for my style of chain menus. This style will use fewer requests as it will only use vehicles that have data.

The type of vehicles in scope will only be petrol vehicles. I have decided this as diesels vehicles are designed more for long commutes, whereas petrol engines are a variantion of short and long distances. I will be exculding hybrids and EV's from this as they have too many variables such as types of batteries and other things which i must account. Also EV have estimated ranges which become heavily influenced by things such as AC, driving habits and battery health.

The minimum data for a vehicle is to be decided once i see the distribution.

I will be storing raw responses as one file per year, with each line holding the URL, the time the request was fetched and the response body untouched. It is worth noting the the URL as this is the point where i was see the original data compared to the manipulated data, also the time of the request fetched will be noted as .....

The delay between requests will be 0.2 when i concluded test 6, there was no rate header limit  published. Also, at 5 requests per second at most ensures that my load on a free governemnt servic is light. In Postman, each request was roughly about 200ms.

## 18/10/2026

https://www.fueleconomy.gov/ws/rest/ympg/shared/menu/model?make=Ford
Count: 161

https://www.fueleconomy.gov/ws/rest/ympg/shared/menu/model?make=BMW
Count: 170

https://www.fueleconomy.gov/ws/rest/ympg/shared/menu/model?make=Honda
Count: 65

Avg Count: 132

HONDA
https://www.fueleconomy.gov/ws/rest/ympg/shared/vehicles?make=Honda&model=Civic
Total vehicles:
126
2015-2020:
2
https://www.fueleconomy.gov/ws/rest/ympg/shared/vehicles?make=Honda&model=Accord
Total vehicles:
131
2015-2020:
17

https://www.fueleconomy.gov/ws/rest/ympg/shared/vehicles?make=Honda&model=Odyssey
Total vehicles:
39
2015-2020:
8

FORD
https://www.fueleconomy.gov/ws/rest/ympg/shared/vehicles?make=Ford&model=Mustang
Total vehicles:
134
2015-2020:
9

https://www.fueleconomy.gov/ws/rest/ympg/shared/vehicles?make=Ford&model=Fiesta
Total vehicles:
2
2015-2020:
0

https://www.fueleconomy.gov/ws/rest/ympg/shared/vehicles?make=Ford&model=Focus
Total vehicles:
36
2015-2020:
0

Mazda
https://www.fueleconomy.gov/ws/rest/ympg/shared/vehicles?make=Mazda&model=MX-5
Total vehicles:
25
2015-2020:
5

https://www.fueleconomy.gov/ws/rest/ympg/shared/vehicles?make=Mazda&model=6
Total vehicles:
45
2015-2020:
11

https://www.fueleconomy.gov/ws/rest/ympg/shared/vehicles?make=Mazda&model=5

Total vehicles:
15
2015-2020:
1

## Request estimate

Shared makes: 71

Models per make (sample of Ford 161, BMW 170, Honda 65): avg 132

Vehicles per model (sample of 9 models across Honda, Ford and Mazda): 553 vehicles in total, 53 of them from 2015-2020. That is about 6 in range per model, or roughly 10% of each list.

Estimate:
- Shared makes menu: 1
- Model menu per make: 71
- Vehicles list per model: 71 x 132 = 9,372
- Driver records for in range vehicles: 9,372 x 6 = 56,232
Total ≈ 65,676 requests, at 0.4s each ≈ 7.3 hours.

- This estimate is most likely too high. My sample is biased towards popular makes and models (Ford and BMW are both large makes, and the models i picked are well known), whereas the full model menus include lots of older models with nothing from 2015 onwards. The 71 makes also include many small and defunct makes with far fewer models than my sample, and often nothing from 2015-2020, so the real figure should be much lower.
- A run of a few hours is fine, as i can start it and leave it, as long as the script can resume where it left off. If the real estimate came out over 8 hours, i would cut it down by using the full menus to find which model names exist in 2015-2020, and only fetching shared vehicle lists for those.
I will log the real request count after the first full run and compare it to this estimate.

-Note: the shared vehicles list contains nearly full vehicle records, including year, city08, highway08, tCharger and sCharger. This means i can filter by year from the list and don't need to fetch each vehicle record separately.

## Model name finding
- The Civic only had 2 vehicles in range, even though i already found two 2017 Civics with driver data (38247 and 38248). The Ford Focus had 0 in range, even though it was sold until 2018. My guess is that model names change over the years, so newer cars are listed under different names (e.g. "Civic 4Dr" or "Civic HB" instead of "Civic"). TO CHECK: look in Honda's shared model menu for other Civic entries.
- This doesn't break the plan, as the script walks every model name anyway. But when i group my results by model later, one car could be spread across several names, so i may need a cleaned up model name column.

## 18 Oct
 - Counted shared makes (71), models for Ford, BMW and Honda, and in range vehicles for 9 models. Estimated about 65,700 requests (≈7.3 hours), likely an overestimate. Found the shared vehicles list includes the year and near full vehicle records, so no separate vehicle record calls are needed.

 ## 19 Oct
Real-world check
- A full Honda run took ~185 requests (65 models, 118 vehicles in 2015-2020, ~1.8 per model vs my estimate of 6). Using Honda as an upper bound: 71 x 185 ≈ 13,000 requests ≈ 1.5 hours, much lower than my original estimate of 65,676, which confirms my sample was biased towards popular models.

## 20 Oct
- Full run: 3,972 requests in about 40 minutes (~0.6s per request including the 0.2s delay). This is far below my original estimate of 65,676 requests (7.3 hours) and my Honda-based revised estimate of ~13,000. My sample of popular makes and models heavily overestimated the totals, as most of the 71 makes are small or defunct with few or no vehicles from 2015-2020. A second run made 0 requests, confirming the dataset is complete. Failed requests that were never saved: 1.

## Exploring the raw data in DuckDB (20-21 Oct)
- I loaded the raw .jsonl files into DuckDB with read_json, keeping the body as plain text so nothing is changed on the way in. The script for this is in transform/explore.py.

How i turned the raw responses into rows:
- read_json reads every make file at once using a wildcard (*.jsonl), so new makes are picked up automatically.
- The API sometimes returns a single object instead of a list (Test 4, Bugatti). In SQL i wrapped the single objects in a list with json_array, so every response can be handled the same way.
- unnest turns each list into one row per vehicle (or one row per driver record).
- v->>'field' pulls a field out of a vehicle as text.

Checks i ran and what they showed:
- All 2,380 vehicle list responses were status 200. There were no 204s, so every shared model had at least one vehicle.
- 14,450 vehicles across all years, and 14,450 unique vehicle IDs. No vehicle appears in more than one model list, so no deduplication is needed.
- 1,519 vehicles are in 2015-2020. This matches the driver record requests from the full run: 3,972 total requests - 1 makes menu - 71 model menus - 2,380 vehicle lists = 1,520, with the extra 1 being the dropped connection that was retried. Two separate counts agreeing shows the extraction is complete.
- Turbos became far more common over time: about 2% of vehicles in 1993 compared to about 40% in 2018 and 46% in 2024. Newer years have fewer vehicles overall, as newer cars have had less time to collect driver submissions.

Engine types (2015-2020, before fuel rules):
- 531 turbocharged and 21 supercharged. 18 of the 21 supercharged vehicles also have a turbo (twincharged), so only 3 are supercharged alone.
- Decision: i am excluding all supercharged vehicles, including the twincharged ones, from the comparison. 21 vehicles is too few to draw anything reliable from, and twincharged engines don't fit a turbo vs naturally aspirated question. I will report their count.

Fuel types (2015-2020):
- Kept: petrol with no atvType. Regular Gasoline 895, Premium Gasoline 252, Midgrade Gasoline 21 = 1,168 vehicles.
- Removed: hybrids 128, diesel 67, plug-in hybrids 61, flex-fuel 57, electric 38 = 351 vehicles.
- 1,168 + 351 = 1,519, so every vehicle is accounted for.
- Rule in SQL: fuelType1 contains "Gasoline" and atvType is empty.

Driver records:
- 3,325 driver records across all 1,519 vehicles in range, about 2.2 drivers per vehicle.
- City + highway percentage totals: 2,794 are exactly 100, 67 are 101 or 99 (rounding), and 464 are 0/0 (the driver never entered their mix). There are no other values.
- Vehicle 41393 has drivers reporting 80.8 and 70.2 mpg, which is very high for petrol. It is probably a hybrid that my scope removes; if not, it's a case for the outlier flag.

Bug found and fixed:
- In DuckDB the ->> operator is applied after AND, so `v->>'tCharger' = 'T' AND v->>'sCharger' = 'S'` was read the wrong way and errored. Wrapping each lookup in brackets, `(v->>'tCharger') = 'T'`, fixed it. Any query combining conditions needs brackets around each field lookup.

## 21 Oct: explored the raw data in DuckDB. Confirmed the extraction is complete (1,519 vehicles in range matches the driver record requests), found the 0/0 driving mix records, decided to exclude supercharged and twincharged vehicles, and set the fuel type rule.

## Staging layer (25 Oct)
transform/01_staging.sql turns the raw responses into typed tables. Staging only changes how values are represented (text to numbers, empty strings to NULL); no business rules are applied here, so it's clear where each decision happens.
- raw_vehicle_lists (2,380 rows) and raw_driver_lists (1,519 rows): every saved response, as written.
- stg_vehicles (14,450 rows): one row per vehicle, all years. I kept about 20 of the ~80 fields the API returns, only those my question needs; the rest stay in the raw files.
- stg_driver_records (3,325 rows): one row per driver record. The API gives driver records no ID, so each gets one from its vehicle ID and its position in the list (e.g. 38248-1). This is the same on every run.
- The API uses 0 for "unrounded MPG not available", so those become NULL rather than a 0 that would distort averages.
- I use CAST rather than TRY_CAST so the pipeline fails loudly on an unexpected value instead of silently turning it into NULL.
- CREATE OR REPLACE rebuilds every table from the raw files each run. I ran the pipeline 3 times and got identical row counts, so re-running doesn't create duplicates.
- pipeline.py runs every numbered SQL file in transform/ in order, into turbo.duckdb (which is not committed, as it's rebuilt from the raw files).