
-- ============================================================
-- CareFlow BigQuery Event Log Warehouse Schema
-- Partitioned by DATE(timestamp) and clustered by case_id, activity
-- ============================================================

CREATE OR REPLACE TABLE `careflow_dw.raw_ehr_events` (
  case_id STRING NOT NULL,
  activity STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  resource STRING,
  department STRING,
  age_group STRING,
  severity STRING,
  duration_min FLOAT64
)
PARTITION BY DATE(timestamp)
CLUSTER BY case_id, activity
OPTIONS (
  description = "Chronological EHR hospital event logs ingested from EHR systems"
);

CREATE OR REPLACE TABLE `careflow_dw.stg_ehr_events_clean` (
  case_id STRING NOT NULL,
  activity STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  resource STRING,
  department STRING,
  age_group STRING,
  severity STRING,
  duration_min FLOAT64,
  event_seq INT64
)
PARTITION BY DATE(timestamp)
CLUSTER BY case_id, activity;
