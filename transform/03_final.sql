
-- 03_final.sql
-- The tables the output reads from. In-scope vehicles only

-- final_driver_comparison: one row per in-scope driver record,
-- comparing what the driver got with what the official figures predict
-- for their own mix of city and highway driving
CREATE OR REPLACE TABLE final_driver_comparison AS
WITH joined AS (
    SELECT
        d.driver_record_id,
        v.vehicle_id,
        v.model_year,
        v.make,
        v.model,
        v.base_model,
        v.vehicle_class,
        v.engine_type,
        v.engine_litres,
        v.cylinders,
        v.transmission,
        v.drive,
        v.official_city_mpg,
        v.official_highway_mpg,
        v.official_combined_mpg,
        d.reported_mpg,
        d.mix_known,
        d.city_share,
        d.highway_share,
        d.is_outlier,
        d.last_date,
        d.state
    FROM clean_driver_records AS d
    JOIN clean_vehicles AS v USING (vehicle_id)
    WHERE v.in_scope
)
SELECT
    *,
    CASE WHEN mix_known THEN 'Own mix' ELSE 'EPA standard mix' END AS expected_basis,

    -- Harmonic weighting: add up fuel per mile for each part of the driving,
    -- then turn it back into MPG. With a 55/45 mix this reproduces comb08 exactly
    CASE
        WHEN mix_known
            THEN 1 / (city_share / official_city_mpg + highway_share / official_highway_mpg)
        ELSE official_combined_mpg
    END AS expected_mpg,

    -- Positive = the driver beat the official figure, negative = fell short
    reported_mpg / expected_mpg - 1 AS gap_pct
FROM joined;


-- final_vehicle_summary: one row per in-scope vehicle, for comparing
-- two specific cars. Outliers are excluded from the averages

CREATE OR REPLACE TABLE final_vehicle_summary AS
SELECT
    vehicle_id,
    model_year,
    make,
    model,
    vehicle_class,
    engine_type,
    engine_litres,
    cylinders,
    transmission,
    official_combined_mpg,
    count(*) FILTER (WHERE NOT is_outlier) AS drivers,
    count(*) FILTER (WHERE is_outlier) AS outliers_excluded,
    -- Harmonic mean, the same method the API uses for its own avgMpg
    count(*) FILTER (WHERE NOT is_outlier)
        / sum(1 / reported_mpg) FILTER (WHERE NOT is_outlier) AS real_world_mpg,
    median(gap_pct) FILTER (WHERE NOT is_outlier) AS median_gap_pct
FROM final_driver_comparison
GROUP BY ALL;

-- final_engine_summary: turbo vs naturally aspirated, overall and by
-- vehicle class. Outliers are excluded

CREATE OR REPLACE TABLE final_engine_summary AS
SELECT
    COALESCE(vehicle_class, 'All classes') AS vehicle_class,
    engine_type,
    count(DISTINCT vehicle_id) AS vehicles,
    count(*)  AS drivers,
    median(gap_pct) AS median_gap_pct,
    avg(gap_pct) AS mean_gap_pct,
    avg(CASE WHEN gap_pct >= 0 THEN 1 ELSE 0 END) AS share_beating_official
FROM final_driver_comparison
WHERE NOT is_outlier
GROUP BY GROUPING SETS ((engine_type), (vehicle_class, engine_type))
ORDER BY vehicle_class, engine_type;