-- ====================================================================
-- CAREFLOW: GOOGLE BIGQUERY NULL VALUE HANDLING SUITE
-- Modern Data Stack (MDS) Healthcare Informatics & Process Mining
-- ====================================================================

-- --------------------------------------------------------------------
-- 1. DATA QUALITY & NULL PROFILING QUERY
-- Audits missingness percentages across all columns before transformation
-- --------------------------------------------------------------------
SELECT
  COUNT(*) AS total_records,
  
  -- Mandatory Process Mining Keys (Must be 0% Nulls)
  COUNTIF(case_id IS NULL) AS null_case_id_count,
  ROUND(100.0 * COUNTIF(case_id IS NULL) / COUNT(*), 2) AS null_case_id_pct,
  
  COUNTIF(activity IS NULL OR TRIM(activity) = '') AS null_activity_count,
  ROUND(100.0 * COUNTIF(activity IS NULL OR TRIM(activity) = '') / COUNT(*), 2) AS null_activity_pct,
  
  COUNTIF(timestamp IS NULL) AS null_timestamp_count,
  ROUND(100.0 * COUNTIF(timestamp IS NULL) / COUNT(*), 2) AS null_timestamp_pct,
  
  -- Clinical & Operational Dimensions (Can be imputed)
  COUNTIF(resource IS NULL) AS null_resource_count,
  COUNTIF(department IS NULL) AS null_department_count,
  COUNTIF(severity IS NULL) AS null_severity_count,
  COUNTIF(duration_min IS NULL) AS null_duration_count,
  ROUND(100.0 * COUNTIF(duration_min IS NULL) / COUNT(*), 2) AS null_duration_pct

FROM `careflow_dw.raw_ehr_events`;


-- --------------------------------------------------------------------
-- 2. PRODUCTION CLEANING & IMPUTATION (dbt STAGING MODEL)
-- Enforces Process Mining schema, imputes missing durations via partition baselines
-- --------------------------------------------------------------------
CREATE OR REPLACE TABLE `careflow_dw.stg_ehr_events_clean` AS
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
  -- Rule 1: Drop fatal nulls for process mining graph validity
  WHERE case_id IS NOT NULL 
    AND activity IS NOT NULL 
    AND TRIM(activity) != ''
    AND timestamp IS NOT NULL
),

activity_baselines AS (
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
  
  -- Rule 2: Coalesce missing resource to 'Unassigned'
  COALESCE(NULLIF(TRIM(r.resource), ''), 'Unassigned_Staff') AS resource,
  
  -- Rule 3: Default missing department
  COALESCE(NULLIF(TRIM(r.department), ''), 'Emergency_Department') AS department,
  
  -- Rule 4: Default demographics
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


-- --------------------------------------------------------------------
-- 3. QUARANTINE / DEAD-LETTER TABLE (EHR COMPLIANCE AUDIT TRAIL)
-- Captures rejected rows with fatal missing keys for informatics audit
-- --------------------------------------------------------------------
CREATE OR REPLACE TABLE `careflow_dw.quarantined_corrupted_events` AS
SELECT
  *,
  CURRENT_TIMESTAMP() AS quarantined_at,
  CASE
    WHEN case_id IS NULL THEN 'MISSING_CASE_ID'
    WHEN activity IS NULL OR TRIM(activity) = '' THEN 'MISSING_ACTIVITY_NAME'
    WHEN timestamp IS NULL THEN 'MISSING_TIMESTAMP'
    ELSE 'MULTIPLE_FATAL_NULLS'
  END AS rejection_reason
FROM `careflow_dw.raw_ehr_events`
WHERE case_id IS NULL 
   OR activity IS NULL 
   OR TRIM(activity) = ''
   OR timestamp IS NULL;
