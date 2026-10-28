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


# Final driver table should have every in-scope driver record (expect 2,251)
con.sql("SELECT count(*) AS final_driver_rows FROM final_driver_comparison").show()

# Hand-checked example: Civic 38248 should give 38.28 (the API's own avgMpg)
con.sql("""
SELECT vehicle_id, drivers, round(real_world_mpg, 2) AS real_world_mpg
FROM final_vehicle_summary WHERE vehicle_id = 38248
""").show()

# The headline: turbo vs naturally aspirated, all classes
con.sql("""
SELECT engine_type, vehicles, drivers,
       round(median_gap_pct * 100, 1) AS median_gap_pct,
       round(mean_gap_pct * 100, 1)   AS mean_gap_pct,
       round(share_beating_official * 100) AS pct_beating_official
FROM final_engine_summary
WHERE vehicle_class = 'All classes'
""").show()

# How many drivers do vehicles have? (for deciding a minimum)
con.sql("""
SELECT drivers, count(*) AS vehicles
FROM final_vehicle_summary
GROUP BY 1 ORDER BY 1
""").show()

# Robustness Check
# 1. How spread out are the gaps? (middle 50% of drivers)
con.sql("""
SELECT engine_type,
       round(quantile_cont(gap_pct, 0.25) * 100, 1) AS p25_gap_pct,
       round(median(gap_pct) * 100, 1)              AS median_gap_pct,
       round(quantile_cont(gap_pct, 0.75) * 100, 1) AS p75_gap_pct
FROM final_driver_comparison
WHERE NOT is_outlier
GROUP BY 1
""").show()

# 2. Does the answer change depending on how expected MPG was calculated
con.sql("""
SELECT engine_type, expected_basis, count(*) AS drivers,
       round(median(gap_pct) * 100, 1) AS median_gap_pct
FROM final_driver_comparison
WHERE NOT is_outlier
GROUP BY 1, 2 ORDER BY 2, 1
""").show()

# 3. Same comparison within vehicle classes that have enough of both
con.sql("""
SELECT vehicle_class, engine_type, drivers,
       round(median_gap_pct * 100, 1) AS median_gap_pct
FROM final_engine_summary
WHERE vehicle_class <> 'All classes'
  AND vehicle_class IN (
      SELECT vehicle_class FROM final_engine_summary
      GROUP BY 1 HAVING min(drivers) >= 30 AND count(*) = 2)
ORDER BY vehicle_class, engine_type
""").show()