"""Sanity checks on the tables built by pipeline.py. Run after the pipeline:
    python transform/checks.py
"""
import duckdb

con = duckdb.connect("turbo.duckdb", read_only=True)

# Why vehicles are in or out of scope
con.sql("""
SELECT COALESCE(exclusion_reason, 'In scope') AS status, engine_type, count(*) AS vehicles
FROM clean_vehicles
GROUP BY 1, 2 ORDER BY 1, 3 DESC
""").show()

# Driver records: mix known, outliers, in scope
con.sql("""
SELECT in_scope, mix_known, is_outlier, count(*) AS records
FROM clean_driver_records
GROUP BY ALL ORDER BY ALL
""").show()

# Every driver record should match a vehicle (should be 0)
con.sql("""
SELECT count(*) AS orphan_driver_records
FROM stg_driver_records d
WHERE d.vehicle_id NOT IN (SELECT vehicle_id FROM clean_vehicles)
""").show()