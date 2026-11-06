#!/usr/bin/env python3
"""
CareFlow Conformance Checking Engine
====================================
Compares the actual patient journeys against hospital clinical protocols:
  - Standard Ideal Journey: Registration → Triage → Doctor Consultation → Treatment → Discharge
  - Flags non-compliant paths, administrative rework, and paperwork loopbacks
  - Computes compliance fitness score per case and across the institution
"""

from pathlib import Path
import pandas as pd
import json

def check_conformance(clean_path: str, output_csv: str, summary_json: str):
    print(f"⚖️ [PM4Py Conformance] Evaluating clinical compliance from {clean_path}...")
    df = pd.read_csv(clean_path)
    df = df.sort_values(by=['case_id', 'timestamp'])
    
    records = []
    
    for case_id, group in df.groupby('case_id'):
        acts = list(group['activity'])
        demographics = group.iloc[0]
        
        # Check specific deviations
        has_xray_loopback = False
        has_double_doc = acts.count('Doctor Consultation') > 1
        has_registration = acts[0] == 'Registration' if len(acts) > 0 else False
        has_discharge = acts[-1] == 'Discharge' if len(acts) > 0 else False
        
        # Loopback detection
        for i in range(len(acts) - 1):
            if acts[i] == 'X-Ray' and acts[i+1] == 'Triage':
                has_xray_loopback = True
                break
                
        # Compliance logic: compliant if no loopbacks and starts with Registration and ends with Discharge
        is_compliant = (not has_xray_loopback) and (not has_double_doc) and has_registration and has_discharge
        
        # Fitness score (0.0 to 1.0)
        penalty = 0.0
        if has_xray_loopback: penalty += 0.35
        if has_double_doc: penalty += 0.20
        if not has_registration: penalty += 0.20
        if not has_discharge: penalty += 0.25
        fitness = max(0.0, round(1.0 - penalty, 2))
        
        records.append({
            'case_id': case_id,
            'severity': demographics.get('severity', 'Unknown'),
            'age_group': demographics.get('age_group', 'Unknown'),
            'total_steps': len(acts),
            'is_compliant': is_compliant,
            'fitness_score': fitness,
            'xray_triage_loopback': has_xray_loopback,
            'double_consultation': has_double_doc,
            'trace': ' → '.join(acts)
        })
        
    df_conf = pd.DataFrame(records)
    df_conf.to_csv(output_csv, index=False)
    
    total_cases = len(df_conf)
    compliant_cases = int(df_conf['is_compliant'].sum())
    loopback_cases = int(df_conf['xray_triage_loopback'].sum())
    double_doc_cases = int(df_conf['double_consultation'].sum())
    avg_fitness = float(df_conf['fitness_score'].mean().round(3))
    
    summary = {
        'total_cases': total_cases,
        'compliant_cases': compliant_cases,
        'compliance_rate_pct': round((compliant_cases / total_cases) * 100, 2),
        'avg_fitness_score': avg_fitness,
        'loopback_cases': loopback_cases,
        'loopback_rate_pct': round((loopback_cases / total_cases) * 100, 2),
        'double_consultation_cases': double_doc_cases,
        'double_consultation_pct': round((double_doc_cases / total_cases) * 100, 2)
    }
    
    with open(summary_json, "w") as f:
        json.dump(summary, f, indent=2)
        
    print(f"✅ [Conformance] Evaluated {total_cases:,} cases.")
    print(f"   Compliance Rate : {summary['compliance_rate_pct']}%")
    print(f"   X-Ray Loopbacks : {loopback_cases:,} cases ({summary['loopback_rate_pct']}%)")
    print(f"   Average Fitness : {avg_fitness}")
    return df_conf, summary

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parent.parent
    clean_csv = base_dir / "data" / "processed" / "ehr_events_clean.csv"
    out_csv = base_dir / "data" / "processed" / "conformance.csv"
    sum_json = base_dir / "data" / "processed" / "conformance_summary.json"
    check_conformance(str(clean_csv), str(out_csv), str(sum_json))
