#!/usr/bin/env python3
"""
CareFlow Process Variant Analysis
==================================
Identifies distinct patient pathways (variants), frequency, and deviation from
the standard clinical flow.
"""

from pathlib import Path
import pandas as pd

def analyze_variants(clean_path: str, output_path: str) -> pd.DataFrame:
    print(f"📊 [Analytics] Discovering Process Variants from {clean_path}...")
    df = pd.read_csv(clean_path)
    df = df.sort_values(by=['case_id', 'timestamp'])
    
    # Aggregate trace per case
    traces = df.groupby('case_id')['activity'].agg(lambda acts: ' → '.join(acts)).reset_index()
    traces.columns = ['case_id', 'variant_path']
    
    total_cases = len(traces)
    variant_counts = traces['variant_path'].value_counts().reset_index()
    variant_counts.columns = ['variant_path', 'case_count']
    variant_counts['percentage'] = ((variant_counts['case_count'] / total_cases) * 100).round(2)
    variant_counts['variant_id'] = [f"Variant {i+1}" for i in range(len(variant_counts))]
    variant_counts['step_count'] = variant_counts['variant_path'].apply(lambda x: len(x.split(' → ')))
    variant_counts['has_loopback'] = variant_counts['variant_path'].str.contains('X-Ray.*Triage', regex=True)
    
    variant_counts = variant_counts[['variant_id', 'case_count', 'percentage', 'step_count', 'has_loopback', 'variant_path']]
    
    variant_counts.to_csv(output_path, index=False)
    print(f"✅ [Analytics] Discovered {len(variant_counts)} unique patient pathways across {total_cases:,} cases.")
    print(f"   Top 3 Variants account for {variant_counts['percentage'].head(3).sum():.1f}% of all admissions.")
    return variant_counts

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parent.parent
    clean_csv = base_dir / "data" / "processed" / "ehr_events_clean.csv"
    out_csv = base_dir / "data" / "processed" / "variants.csv"
    analyze_variants(str(clean_csv), str(out_csv))
