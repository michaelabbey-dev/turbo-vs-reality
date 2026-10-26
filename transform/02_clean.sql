-- 02_clean.sql
-- Applies the project's rules: scope, engine type, best official figures,
-- driving mix and data quality flags. Nothing is deleted from in-range
-- vehicles: rows outside scope are labelled with the reason, so the
-- counts can be reported.

-- clean_vehicles: one row per vehicle from 2015-2020
CREATE OR REPLACE TABLE clean_vehicles AS
WITH classified AS (
    SELECT
        *,
        CASE
            WHEN turbo_flag = 'T' AND supercharger_flag = 'S' THEN 'Twincharged'
            WHEN supercharger_flag = 'S' THEN 'Supercharged'
            WHEN turbo_flag = 'T' THEN 'Turbocharged'
            ELSE 'Naturally aspirated'
        END AS engine_type,

        -- Use the unrounded official figure where it exists, otherwise the rounded one
        COALESCE(city_mpg_unrounded, city_mpg) AS official_city_mpg,
        COALESCE(highway_mpg_unrounded, highway_mpg) AS official_highway_mpg,
        COALESCE(combined_mpg_unrounded, combined_mpg) AS official_combined_mpg
    FROM stg_vehicles
    WHERE model_year BETWEEN 2015 AND 2020
)
SELECT
    *,
    CASE
        WHEN fuel_type NOT LIKE '%Gasoline' OR alt_fuel_type IS NOT NULL
            THEN 'Not petrol-only (' || COALESCE(alt_fuel_type, fuel_type) || ')'
        WHEN engine_type IN ('Twincharged', 'Supercharged')
            THEN 'Supercharged (too few to compare)'
        ELSE NULL
    END AS exclusion_reason,
    exclusion_reason IS NULL AS in_scope
FROM classified;


-- clean_driver_records: one row per driver record for in-range vehicles
CREATE OR REPLACE TABLE clean_driver_records AS
WITH with_totals AS (
    SELECT
        d.*,
        d.city_percent_raw + d.highway_percent_raw AS percent_total,
        v.in_scope,
        v.official_combined_mpg
    FROM stg_driver_records AS d
    JOIN clean_vehicles AS v USING (vehicle_id)
)
SELECT
    driver_record_id,
    vehicle_id,
    reported_mpg,
    city_percent_raw,
    highway_percent_raw,
    percent_total,

    -- Driving mix: known if the two percentages add up to roughly 100.
    -- In practice the totals are 100, 99/101 (rounding) or 0 (not entered).
    percent_total BETWEEN 95 AND 105 AS mix_known,

    -- Rescale to shares that add up to exactly 1, e.g. 83/18 -> 0.822/0.178
    CASE WHEN mix_known THEN city_percent_raw / percent_total END AS city_share,
    CASE WHEN mix_known THEN highway_percent_raw / percent_total END AS highway_share,

    -- Keep only the date: the time is always midnight and the offset is just US Eastern time
    CAST(left(last_date_raw, 10) AS DATE) AS last_date,
    state,

    -- Flag (don't delete) values more than 50% away from the official combined figure
    reported_mpg > official_combined_mpg * 1.5
        OR reported_mpg < official_combined_mpg * 0.5 AS is_outlier,

    in_scope,
    source_url,
    fetched_at
FROM with_totals;