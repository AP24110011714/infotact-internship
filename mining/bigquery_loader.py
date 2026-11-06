#!/usr/bin/env python3
"""
CareFlow Google BigQuery Warehouse Setup & Loader
=================================================
MDS (Modern Data Stack) Integration:
  - Generates BigQuery DDL for partitioned & clustered chronological event logs
  - Simulates BigQuery staging dataset in SQLite / Parquet for local offline testing
  - Provides BigQuery Python SDK client integration script
"""

import sys
from pathlib import Path
import sqlite3
import pandas as pd

BIGQUERY_DDL = """
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
"""

def setup_local_warehouse(csv_path: str, db_path: str):
    print(f"📦 [BigQuery/MDS] Initializing CareFlow Data Warehouse storage...")
    df = pd.read_csv(csv_path)
    
    conn = sqlite3.connect(db_path)
    df.to_sql("stg_ehr_events_clean", conn, if_exists="replace", index=False)
    
    # Save DDL script for BigQuery production deployment
    ddl_file = Path(db_path).parent / "bigquery_schema.sql"
    with open(ddl_file, "w") as f:
        f.write(BIGQUERY_DDL)
        
    print(f"✅ [BigQuery/MDS] Loaded {len(df):,} events into warehouse staging database ({db_path})")
    print(f"✅ [BigQuery/MDS] BigQuery DDL generated at {ddl_file}")
    conn.close()

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parent.parent
    clean_csv = base_dir / "data" / "processed" / "ehr_events_clean.csv"
    db_file = base_dir / "data" / "processed" / "careflow_warehouse.db"
    setup_local_warehouse(str(clean_csv), str(db_file))
