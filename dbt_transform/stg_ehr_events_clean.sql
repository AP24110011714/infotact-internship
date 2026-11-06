-- ====================================================================
-- CAREFLOW dbt Model: stg_ehr_events_clean.sql
-- Handles NULL values, standardizes schema, and imputes missing metrics
-- Modern Data Stack (Google BigQuery)
-- ====================================================================

WITH raw_source AS (
  SELECT
    TRIM(case_id) AS case_id,
    TRIM(activity) AS activity,
    timestamp,
    resource,
    department,
    age_group,
    severity,
    duration_min
  FROM `careflow_dw.raw_ehr_events`
  -- Rule 1: Eliminate fatal nulls (Process Mining requires Case, Activity, Time)
  WHERE case_id IS NOT NULL 
    AND activity IS NOT NULL 
    AND TRIM(activity) != ''
    AND timestamp IS NOT NULL
),

activity_baselines AS (
  -- Compute fallback average duration per activity for missing duration imputation
  SELECT 
    activity,
    ROUND(AVG(duration_min), 2) AS avg_activity_duration
  FROM raw_source
  WHERE duration_min IS NOT NULL
  GROUP BY activity
)

SELECT
  r.case_id,
  r.activity,
  r.timestamp,
  
  -- Rule 2: Coalesce missing resource to 'Unassigned' or automated staff
  COALESCE(NULLIF(TRIM(r.resource), ''), 'Unassigned_Staff') AS resource,
  
  -- Rule 3: Default missing department to 'Emergency Department'
  COALESCE(NULLIF(TRIM(r.department), ''), 'Emergency_Department') AS department,
  
  -- Rule 4: Default missing demographics
  COALESCE(NULLIF(TRIM(r.age_group), ''), 'Unknown_Age') AS age_group,
  COALESCE(NULLIF(TRIM(r.severity), ''), 'Standard') AS severity,
  
  -- Rule 5: Impute NULL duration with benchmark activity average
  COALESCE(r.duration_min, b.avg_activity_duration, 15.0) AS duration_min,
  
  -- Event sequence number per patient case
  ROW_NUMBER() OVER (
    PARTITION BY r.case_id 
    ORDER BY r.timestamp ASC
  ) AS event_seq

FROM raw_source r
LEFT JOIN activity_baselines b
  ON r.activity = b.activity;
