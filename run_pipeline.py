#!/usr/bin/env python3
"""
CareFlow End-to-End Execution Pipeline
======================================
Infotact Solutions Internship - CareFlow: Clinical Pathway Process Mining
Orchestrates the entire 4-week development pipeline:
  Week 1: EHR Simulation (generate_event_log.py) & Warehouse Loader (mining/bigquery_loader.py)
  Week 2: Event Normalization (dbt_transform/clean_event_log.py) & Process Discovery (mining/discover.py)
  Week 3: Bottleneck Calculations (mining/bottlenecks.py)
  Week 4: Conformance Checking (mining/conformance.py) & Variant Analysis (mining/variants.py)
"""

import sys
import subprocess
from pathlib import Path

def run_step(step_num: int, title: str, cmd: list):
    print(f"\n{'='*70}")
    print(f"🚀 STEP {step_num}: {title}")
    print(f"{'='*70}")
    result = subprocess.run(cmd, check=True)
    if result.returncode != 0:
        raise RuntimeError(f"Step {step_num} failed with code {result.returncode}")

def main():
    root = Path(__file__).resolve().parent
    python = sys.executable
    
    print("\n" + "="*70)
    print("🏥 CAREFLOW: CLINICAL PATHWAY PROCESS MINING PIPELINE")
    print("Infotact Solutions Internship - Batch 22.1")
    print("="*70)
    
    # 1. Week 1: Event Log Simulation
    run_step(1, "EHR Simulation (5,000 cases with 40% X-Ray loopbacks)", 
             [python, str(root / "generate_event_log.py"), "--cases", "5000"])
             
    # 2. Week 2: dbt Transformation Layer
    run_step(2, "dbt Event Log Normalization", 
             [python, str(root / "dbt_transform" / "clean_event_log.py")])
             
    # 3. Week 1/2: BigQuery & MDS Storage
    run_step(3, "BigQuery Warehouse Staging & DDL Generation", 
             [python, str(root / "mining" / "bigquery_loader.py")])
             
    # 4. Week 2: PM4Py Process Discovery (As-Is DFG)
    run_step(4, "PM4Py Process Discovery (Directly Follows Graph)", 
             [python, str(root / "mining" / "discover.py")])

    # 4b. Week 2: PM4Py Petri Net Discovery (Inductive Miner)
    run_step("4b", "PM4Py Formal Petri Net Discovery (PNML Generation)", 
             [python, str(root / "mining" / "petri_net.py")])
             
    # 5. Week 3: Transition & Bottleneck Calculation
    run_step(5, "Bottleneck & Transition Time Analytics", 
             [python, str(root / "mining" / "bottlenecks.py")])
             
    # 6. Week 4: Variant Analysis
    run_step(6, "Process Variant Mining", 
             [python, str(root / "mining" / "variants.py")])
             
    # 7. Week 4: Conformance Checking
    run_step(7, "Clinical Pathway Conformance Checking", 
             [python, str(root / "mining" / "conformance.py")])
             
    print("\n" + "="*70)
    print("🎉 ALL 4 WEEKS OF CAREFLOW PIPELINE EXECUTED SUCCESSFULLY!")
    print("="*70)

if __name__ == '__main__':
    main()
