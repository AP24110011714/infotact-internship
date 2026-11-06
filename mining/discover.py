#!/usr/bin/env python3
"""
CareFlow PM4Py Process Discovery Engine
========================================
Algorithmically discovers the 'As-Is' patient process map from normalized EHR logs:
  - Discovers Directly Follows Graph (DFG)
  - Identifies Start and End activities
  - Exports process edges, node frequencies, and graph metadata for dashboards
"""

import sys
from pathlib import Path
import pandas as pd
import json

def run_process_discovery(clean_path: str, processed_dir: str):
    import pm4py
    
    print(f"🔍 [PM4Py] Discovering Process Model from {clean_path}...")
    df = pd.read_csv(clean_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Format dataframe for PM4Py
    log = pm4py.format_dataframe(
        df,
        case_id='case_id',
        activity_key='activity',
        timestamp_key='timestamp'
    )
    
    # 1. Discover DFG, Start Activities, and End Activities
    dfg, start_acts, end_acts = pm4py.discover_dfg(log)
    
    # 2. Activity / Node frequencies
    node_counts = df['activity'].value_counts().to_dict()
    node_list = []
    for act, count in node_counts.items():
        node_list.append({
            'activity': act,
            'count': int(count),
            'is_start': int(start_acts.get(act, 0)),
            'is_end': int(end_acts.get(act, 0))
        })
    df_nodes = pd.DataFrame(node_list)
    df_nodes.to_csv(Path(processed_dir) / "dfg_nodes.csv", index=False)
    
    # 3. Edge / Transition frequencies
    edges = []
    for (src, tgt), count in dfg.items():
        edges.append({
            'source': src,
            'target': tgt,
            'count': int(count),
            'is_loopback': bool(src == 'X-Ray' and tgt == 'Triage')
        })
    df_edges = pd.DataFrame(edges).sort_values(by='count', ascending=False)
    df_edges.to_csv(Path(processed_dir) / "dfg_edges.csv", index=False)
    
    # 4. Save metadata summary
    summary = {
        'total_cases': int(df['case_id'].nunique()),
        'total_events': int(len(df)),
        'unique_activities': int(df['activity'].nunique()),
        'unique_transitions': int(len(edges)),
        'start_activities': start_acts,
        'end_activities': end_acts
    }
    with open(Path(processed_dir) / "dfg_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
        
    print(f"✅ [PM4Py] DFG Discovered: {len(node_list)} activities, {len(edges)} transitions.")
    print(f"   Key Inefficiency Highlighted:")
    xray_triage = [e for e in edges if e['source'] == 'X-Ray' and e['target'] == 'Triage']
    if xray_triage:
        print(f"   ⚠️ Loopback detected: X-Ray → Triage occurred {xray_triage[0]['count']:,} times!")

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parent.parent
    clean_csv = base_dir / "data" / "processed" / "ehr_events_clean.csv"
    proc_dir = base_dir / "data" / "processed"
    run_process_discovery(str(clean_csv), str(proc_dir))
