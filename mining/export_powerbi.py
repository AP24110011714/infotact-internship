#!/usr/bin/env python3
"""
CareFlow PowerBI & Looker Star-Schema Exporter
==============================================
Transforms and denormalizes the CareFlow process mining event logs into a Star Schema
optimized for Microsoft PowerBI, Power Automate Process Mining visual, and Looker Studio:
  - fact_event_log.csv: Granular chronological facts
  - fact_transitions.csv: Transition matrix and wait times
  - dim_patient.csv: Patient cases, conformance flags, and demographics
  - dim_activity.csv: Activity master table
"""

from pathlib import Path
import pandas as pd

def export_for_powerbi(clean_path: str, conf_path: str, bottlenecks_path: str, export_dir: str):
    print(f"📊 [PowerBI/Looker] Exporting Star-Schema datasets to {export_dir}...")
    out_dir = Path(export_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    df_clean = pd.read_csv(clean_path)
    df_conf = pd.read_csv(conf_path)
    df_bottlenecks = pd.read_csv(bottlenecks_path)
    
    # 1. Dimension: Patient Cases (dim_patient)
    dim_patient = df_conf[[
        'case_id', 'severity', 'age_group', 'total_steps', 
        'is_compliant', 'fitness_score', 'xray_triage_loopback', 'double_consultation'
    ]].copy()
    dim_patient.to_csv(out_dir / "dim_patient.csv", index=False)
    
    # 2. Dimension: Activities (dim_activity)
    unique_acts = df_clean['activity'].unique()
    dim_act = pd.DataFrame({
        'activity_id': range(1, len(unique_acts) + 1),
        'activity_name': unique_acts
    })
    dim_act.to_csv(out_dir / "dim_activity.csv", index=False)
    
    # 3. Fact: Event Log (fact_event_log)
    fact_events = df_clean[[
        'case_id', 'activity', 'timestamp', 'event_seq', 
        'resource', 'department', 'duration_min'
    ]].copy()
    fact_events.to_csv(out_dir / "fact_event_log.csv", index=False)
    
    # 4. Fact: Process Transitions (fact_transitions)
    df_bottlenecks.to_csv(out_dir / "fact_transitions.csv", index=False)
    
    print(f"✅ [PowerBI/Looker] Star-Schema export completed:")
    print(f"   • {out_dir / 'dim_patient.csv'} ({len(dim_patient):,} rows)")
    print(f"   • {out_dir / 'dim_activity.csv'} ({len(dim_act)} rows)")
    print(f"   • {out_dir / 'fact_event_log.csv'} ({len(fact_events):,} rows)")
    print(f"   • {out_dir / 'fact_transitions.csv'} ({len(df_bottlenecks)} rows)")

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parent.parent
    clean_csv = base_dir / "data" / "processed" / "ehr_events_clean.csv"
    conf_csv = base_dir / "data" / "processed" / "conformance.csv"
    b_csv = base_dir / "data" / "processed" / "bottlenecks.csv"
    pb_dir = base_dir / "data" / "powerbi_export"
    export_for_powerbi(str(clean_csv), str(conf_csv), str(b_csv), str(pb_dir))
