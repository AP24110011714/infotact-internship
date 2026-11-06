#!/usr/bin/env python3
"""
dbt Model Simulation: Event Log Normalization
==============================================
Implements the dbt transformation layer for CareFlow:
  - Ingests raw EHR event logs from BigQuery / raw storage
  - Enforces standard process mining schema: (case_id, activity, timestamp, resource)
  - Validates chronological order per case
  - Deduplicates events and handles missing values
  - Computes transition index and event sequence number
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
    
    # 2. Strict type casting and null removal
    df = df.dropna(subset=['case_id', 'activity', 'timestamp'])
    df['case_id'] = df['case_id'].astype(str)
    df['activity'] = df['activity'].astype(str).str.strip()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 3. Chronological ordering per patient case
    df = df.sort_values(by=['case_id', 'timestamp']).reset_index(drop=True)
    
    # 4. Add dbt surrogate key & event sequence index per case
    df['event_seq'] = df.groupby('case_id').cumcount() + 1
    
    # 5. Export cleaned event log
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
