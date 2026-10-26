import duckdb

con = duckdb.connect()


# Every saved response for the shared vehicles lists, one row per line in the files
con.sql("""
CREATE OR REPLACE VIEW raw_vehicles AS
SELECT * FROM read_json('data/raw/shared_vehicles/*.jsonl',
    format = 'newline_delimited',
    columns = {'url': 'VARCHAR', 'fetched_at': 'VARCHAR', 'status': 'INTEGER', 'body': 'VARCHAR'})
""")

# One row per vehicle, whether the API sent a list or a single object
con.sql("""
CREATE OR REPLACE VIEW vehicle_items AS
WITH as_arrays AS (
    SELECT url, fetched_at,
           CASE WHEN json_type(body, '$.vehicle') = 'ARRAY'
                THEN json_extract(body, '$.vehicle')
                ELSE json_array(json_extract(body, '$.vehicle')) END AS vehicles
    FROM raw_vehicles
    WHERE status = 200
)
SELECT url, fetched_at, unnest(from_json(vehicles, '["JSON"]')) AS v
FROM as_arrays
""")

print(con.sql("SELECT status, count(*) AS responses FROM raw_vehicles GROUP BY status ORDER BY status"))

print(con.sql("""
SELECT v->>'year' AS year, count(*) AS vehicles,
       count(*) FILTER (WHERE v->>'tCharger' = 'T') AS turbocharged
FROM vehicle_items
GROUP BY 1 ORDER BY 1
""").show(max_rows=100))

# My scope: 2015-2020, by engine type
con.sql("""
SELECT v->>'year' AS year,
       count(*) AS vehicles,
       count(*) FILTER (WHERE v->>'tCharger' = 'T') AS turbocharged,
       count(*) FILTER (WHERE v->>'sCharger' = 'S') AS supercharged
FROM vehicle_items
WHERE (v->>'year')::INTEGER BETWEEN 2015 AND 2020
GROUP BY 1 ORDER BY 1
""").show()

# Any vehicles appear more than once across the list table
con.sql("""
SELECT count(*) AS rows, count(DISTINCT v->>'id') AS unique_vehicles
FROM vehicle_items
""").show()

# Any vehicles with BOTH a turbo and a supercharger (twincharged)?
con.sql("""
SELECT count(*) AS twincharged
FROM vehicle_items
WHERE (v->>'tCharger') = 'T' AND (v->>'sCharger') = 'S'
""").show()

# What fuel types are in range? My petrol-only rule will be enforced.
con.sql("""
SELECT v->>'fuelType1' AS fuel, v->>'atvType' AS atv, count(*) AS vehicles
FROM vehicle_items
WHERE (v->>'year')::INTEGER BETWEEN 2015 AND 2020
GROUP BY 1, 2 ORDER BY 3 DESC
""").show()

con.sql("""
CREATE OR REPLACE VIEW raw_drivers AS
SELECT * FROM read_json('data/raw/driver_records/*.jsonl',
    format = 'newline_delimited',
    columns = {'url': 'VARCHAR', 'fetched_at': 'VARCHAR', 'status': 'INTEGER', 'body': 'VARCHAR'})
""")

con.sql("""
CREATE OR REPLACE VIEW driver_items AS
WITH as_arrays AS (
    SELECT url,
           CASE WHEN json_type(body, '$.yourMpgDriverVehicle') = 'ARRAY'
                THEN json_extract(body, '$.yourMpgDriverVehicle')
                ELSE json_array(json_extract(body, '$.yourMpgDriverVehicle')) END AS drivers
    FROM raw_drivers
    WHERE status = 200
)
SELECT url, unnest(from_json(drivers, '["JSON"]')) AS d
FROM as_arrays
""")

con.sql("SELECT status, count(*) AS responses FROM raw_drivers GROUP BY status").show()

# How many driver records and how many have percentages that don't add up to 100
con.sql("""
SELECT count(*) AS driver_records,
       count(DISTINCT d->>'vehicleId') AS vehicles_with_drivers,
       count(*) FILTER (WHERE (d->>'cityPercent')::DOUBLE + (d->>'highwayPercent')::DOUBLE <> 100) AS not_100,
       count(*) FILTER (WHERE abs((d->>'cityPercent')::DOUBLE + (d->>'highwayPercent')::DOUBLE - 100) > 5) AS outside_tolerance
FROM driver_items
""").show()

# What do the totals actually look like?
con.sql("""
SELECT (d->>'cityPercent')::DOUBLE + (d->>'highwayPercent')::DOUBLE AS total,
       count(*) AS records
FROM driver_items
GROUP BY 1
ORDER BY 2 DESC
LIMIT 15
""").show()

# A few examples of records outside the tolerance
con.sql("""
SELECT d->>'vehicleId' AS vehicle, d->>'mpg' AS mpg,
       d->>'cityPercent' AS city, d->>'highwayPercent' AS highway
FROM driver_items
WHERE abs((d->>'cityPercent')::DOUBLE + (d->>'highwayPercent')::DOUBLE - 100) > 5
LIMIT 10
""").show()