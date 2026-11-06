#!/usr/bin/env python3
"""
CareFlow PM4Py Petri Net Discovery Engine
==========================================
Discovers formal Petri Net models (places, transitions, and arcs) from normalized EHR logs
using PM4Py Inductive Miner:
  - Discovers Petri net, initial marking, and final marking
  - Exports standard PNML (Petri Net Markup Language) file for academic & BI tools
  - Generates structural metrics (Places, Transitions, Arcs, Silent Transitions)
"""

from pathlib import Path
import json
import pandas as pd

def discover_petri_net(clean_path: str, output_pnml: str, summary_json: str):
    import pm4py
    
    print(f"🕸️ [PM4Py] Discovering Petri Net from {clean_path}...")
    df = pd.read_csv(clean_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    log = pm4py.format_dataframe(
        df,
        case_id='case_id',
        activity_key='activity',
        timestamp_key='timestamp'
    )
    
    # Discover Petri net using Inductive Miner
    net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(log)
    
    # Export PNML file
    pm4py.write_pnml(net, initial_marking, final_marking, output_pnml)
    
    places = list(net.places)
    transitions = list(net.transitions)
    arcs = list(net.arcs)
    
    visible_transitions = [t.label for t in transitions if t.label is not None]
    silent_transitions = [t.name for t in transitions if t.label is None]
    
    summary = {
        "model_type": "Inductive Miner Petri Net",
        "places_count": len(places),
        "transitions_count": len(transitions),
        "visible_transitions_count": len(visible_transitions),
        "silent_transitions_count": len(silent_transitions),
        "arcs_count": len(arcs),
        "pnml_file": str(Path(output_pnml).name),
        "visible_activities": sorted(list(set(visible_transitions)))
    }
    
    with open(summary_json, "w") as f:
        json.dump(summary, f, indent=2)
        
    print(f"✅ [PM4Py] Petri Net Discovered:")
    print(f"   • Places: {len(places)}")
    print(f"   • Transitions: {len(transitions)} ({len(visible_transitions)} visible, {len(silent_transitions)} silent)")
    print(f"   • Arcs: {len(arcs)}")
    print(f"   • PNML Exported → {output_pnml}")
    return net, summary

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parent.parent
    clean_csv = base_dir / "data" / "processed" / "ehr_events_clean.csv"
    pnml_path = base_dir / "data" / "processed" / "careflow_petri_net.pnml"
    sum_json = base_dir / "data" / "processed" / "petri_net_summary.json"
    discover_petri_net(str(clean_csv), str(pnml_path), str(sum_json))
