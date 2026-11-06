#!/usr/bin/env python3
"""
CareFlow Bottleneck & Transition Time Analytics
================================================
Calculates average transition and wait times between every single node in the
clinical pathway to identify hidden operational friction.
"""

from pathlib import Path
import pandas as pd
import numpy as np

def calculate_bottlenecks(clean_path: str, output_path: str) -> pd.DataFrame:
    print(f"⏱️ [Analytics] Calculating node-to-node transition bottlenecks from {clean_path}...")
    df = pd.read_csv(clean_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by=['case_id', 'timestamp']).reset_index(drop=True)
    
    # Pairwise transitions per case
    df['next_activity'] = df.groupby('case_id')['activity'].shift(-1)
    df['next_timestamp'] = df.groupby('case_id')['timestamp'].shift(-1)
    
    transitions = df.dropna(subset=['next_activity', 'next_timestamp']).copy()
    transitions['wait_minutes'] = (
        (transitions['next_timestamp'] - transitions['timestamp']).dt.total_seconds() / 60.0
    )
    
    # Filter non-negative waits
    transitions = transitions[transitions['wait_minutes'] >= 0]
    
    grouped = transitions.groupby(['activity', 'next_activity'])
    
    stats = grouped.agg(
        count=('wait_minutes', 'count'),
        mean_min=('wait_minutes', 'mean'),
        median_min=('wait_minutes', 'median'),
        p90_min=('wait_minutes', lambda s: np.percentile(s, 90)),
        min_min=('wait_minutes', 'min'),
        max_min=('wait_minutes', 'max')
    ).reset_index()
    
    stats.columns = ['source', 'target', 'transition_count', 'mean_wait_min', 'median_wait_min', 'p90_wait_min', 'min_wait_min', 'max_wait_min']
    
    # Round metrics
    for col in ['mean_wait_min', 'median_wait_min', 'p90_wait_min', 'min_wait_min', 'max_wait_min']:
        stats[col] = stats[col].round(2)
        
    stats['total_hours_lost'] = ((stats['transition_count'] * stats['mean_wait_min']) / 60.0).round(1)
    stats = stats.sort_values(by='mean_wait_min', ascending=False)
    
    stats.to_csv(output_path, index=False)
    print(f"✅ [Analytics] Bottlenecks saved to {output_path} ({len(stats)} distinct transitions).")
    return stats

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parent.parent
    clean_csv = base_dir / "data" / "processed" / "ehr_events_clean.csv"
    out_csv = base_dir / "data" / "processed" / "bottlenecks.csv"
    calculate_bottlenecks(str(clean_csv), str(out_csv))
