#!/usr/bin/env python3
"""
dbt Model Simulation: Event Log Normalization & NULL Handling
=============================================================
Implements the dbt transformation layer for CareFlow:
  - Ingests raw EHR event logs from BigQuery / raw storage
  - Drops fatal missing keys (case_id, activity, timestamp)
  - Imputes non-fatal missing values (resource, department, severity, duration)
  - Enforces standard process mining schema: (case_id, activity, timestamp, resource)
  - Validates chronological order and generates event sequence surrogate key
"""

import sys
from pathlib import Path
import pandas as pd

def transform_event_log(raw_path: str, output_path: str) -> pd.DataFrame:
    print(f"🔄 [dbt] Loading raw EHR events from {raw_path}...")
    df = pd.read_csv(raw_path)
    
    # 1. Standardize column names
    col_map = {
        'case_id': 'case_id',
        'activity': 'activity',
        'timestamp': 'timestamp',
        'resource': 'resource',
        'department': 'department',
        'age_group': 'age_group',
        'severity': 'severity',
        'duration_min': 'duration_min'
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    
    # 2. Strict type casting and fatal null removal (Process Mining requires Case, Activity, Timestamp)
    df = df.dropna(subset=['case_id', 'activity', 'timestamp'])
    df['case_id'] = df['case_id'].astype(str).str.strip()
    df['activity'] = df['activity'].astype(str).str.strip()
    df = df[df['activity'] != '']
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 3. NULL Imputation & Coalesce (Parity with BigQuery SQL Model)
    if 'resource' in df.columns:
        df['resource'] = df['resource'].fillna('Unassigned_Staff').astype(str).str.strip()
    if 'department' in df.columns:
        df['department'] = df['department'].fillna('Emergency_Department').astype(str).str.strip()
    if 'age_group' in df.columns:
        df['age_group'] = df['age_group'].fillna('Unknown_Age')
    if 'severity' in df.columns:
        df['severity'] = df['severity'].fillna('Standard')
    if 'duration_min' in df.columns:
        activity_means = df.groupby('activity')['duration_min'].transform('mean')
        df['duration_min'] = df['duration_min'].fillna(activity_means).fillna(15.0).round(2)
        
    # 4. Chronological ordering per patient case
    df = df.sort_values(by=['case_id', 'timestamp']).reset_index(drop=True)
    
    # 5. Add dbt surrogate key & event sequence index per case
    df['event_seq'] = df.groupby('case_id').cumcount() + 1
    
    # 6. Export cleaned event log
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    
    print(f"✅ [dbt] Normalized {len(df):,} events across {df['case_id'].nunique():,} cases → {out}")
    return df

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parent.parent
    raw_csv = base_dir / "data" / "raw" / "ehr_events.csv"
    clean_csv = base_dir / "data" / "processed" / "ehr_events_clean.csv"
    transform_event_log(str(raw_csv), str(clean_csv))
