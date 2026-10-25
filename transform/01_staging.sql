
-- Turning the raw API responses into typed tables, one row per thing
-- No business rules here: no filtering, no classification. Staging only
-- Changes how values are REPRESENTED (text -> numbers, "" -> NULL)
-- raw_vehicle_lists / raw_driver_lists
-- Every saved response, exactly as it was written to the .jsonl files

CREATE OR REPLACE TABLE raw_vehicle_lists AS
SELECT *
FROM read_json('data/raw/shared_vehicles/*.jsonl',
    format = 'newline_delimited',
    columns = {'url': 'VARCHAR', 'fetched_at': 'VARCHAR', 'status': 'INTEGER', 'body': 'VARCHAR'});

CREATE OR REPLACE TABLE raw_driver_lists AS
SELECT *
FROM read_json('data/raw/driver_records/*.jsonl',
    format = 'newline_delimited',
    columns = {'url': 'VARCHAR', 'fetched_at': 'VARCHAR', 'status': 'INTEGER', 'body': 'VARCHAR'});


-- stg_vehicles: one row per vehicle (all years)
CREATE OR REPLACE TABLE stg_vehicles AS
WITH as_arrays AS (
    -- The API sends a list, or a single object when there is only one vehicle
    -- Wrap single objects in a list so every response is handled the same way
    SELECT
        url,
        fetched_at,
        CASE WHEN json_type(body, '$.vehicle') = 'ARRAY'
             THEN json_extract(body, '$.vehicle')
             ELSE json_array(json_extract(body, '$.vehicle'))
        END AS vehicles
    FROM raw_vehicle_lists
    WHERE status = 200
),
items AS (
    SELECT url, fetched_at, unnest(from_json(vehicles, '["JSON"]')) AS v
    FROM as_arrays
)
SELECT
    -- identifiers
    CAST(v->>'id' AS INTEGER) AS vehicle_id,
    CAST(v->>'year' AS INTEGER) AS model_year,
    v->>'make' AS make,
    v->>'model' AS model,
    NULLIF(v->>'baseModel', '') AS base_model,
    NULLIF(v->>'VClass', '') AS vehicle_class,

    -- engine and drivetrain
    CAST(NULLIF(v->>'displ', '') AS DOUBLE) AS engine_litres,
    CAST(NULLIF(v->>'cylinders', '') AS INTEGER) AS cylinders,
    NULLIF(v->>'tCharger', '') AS turbo_flag,
    NULLIF(v->>'sCharger', '') AS supercharger_flag,
    NULLIF(v->>'eng_dscr', '') AS engine_descriptor,
    NULLIF(v->>'trany', '') AS transmission,
    NULLIF(v->>'drive', '') AS drive,
    NULLIF(v->>'startStop', '') AS start_stop,

    -- fuel
    NULLIF(v->>'fuelType1', '') AS fuel_type,
    NULLIF(v->>'atvType', '') AS alt_fuel_type,

    -- official MPG rounded, always present
    CAST(NULLIF(v->>'city08', '') AS DOUBLE) AS city_mpg,
    CAST(NULLIF(v->>'highway08', '') AS DOUBLE) AS highway_mpg,
    CAST(NULLIF(v->>'comb08', '') AS DOUBLE) AS combined_mpg,

    -- official MPG unrounded ,The API uses 0 for "not available"
    NULLIF(CAST(NULLIF(v->>'city08U', '') AS DOUBLE), 0) AS city_mpg_unrounded,
    NULLIF(CAST(NULLIF(v->>'highway08U', '') AS DOUBLE), 0) AS highway_mpg_unrounded,
    NULLIF(CAST(NULLIF(v->>'comb08U', '') AS DOUBLE), 0) AS combined_mpg_unrounded,

    -- lineage: where and when this row comes from
    url AS source_url,
    CAST(fetched_at AS TIMESTAMPTZ)AS fetched_at
FROM items;


-- stg_driver_records: one row per driver record
CREATE OR REPLACE TABLE stg_driver_records AS
WITH as_arrays AS (
    SELECT
        url,
        fetched_at,
        CASE WHEN json_type(body, '$.yourMpgDriverVehicle') = 'ARRAY'
             THEN json_extract(body, '$.yourMpgDriverVehicle')
             ELSE json_array(json_extract(body, '$.yourMpgDriverVehicle'))
        END AS drivers
    FROM raw_driver_lists
    WHERE status = 200
),
as_lists AS (
    SELECT url, fetched_at, from_json(drivers, '["JSON"]') AS driver_list
    FROM as_arrays
),
items AS (
    -- Keep each record's position in its list, so every row has a stable ID
    -- that is the same every time the pipeline runs.
    SELECT url, fetched_at, i + 1 AS record_number, driver_list[i + 1] AS d
    FROM as_lists, unnest(range(len(driver_list))) AS t(i)
)
SELECT
    CAST(d->>'vehicleId' AS INTEGER) || '-' || record_number AS driver_record_id,
    CAST(d->>'vehicleId' AS INTEGER) AS vehicle_id,
    CAST(d->>'mpg' AS DOUBLE) AS reported_mpg,
    CAST(NULLIF(d->>'cityPercent', '') AS DOUBLE) AS city_percent_raw,
    CAST(NULLIF(d->>'highwayPercent', '') AS DOUBLE) AS highway_percent_raw,
    NULLIF(d->>'state', '') AS state,
    NULLIF(d->>'lastDate', '') AS last_date_raw,
    url AS source_url,
    CAST(fetched_at AS TIMESTAMPTZ) AS fetched_at
FROM items;
