"""
CareFlow Streamlit Dashboard
============================
Infotact Solutions Internship - CareFlow: Clinical Pathway Process Mining
Features:
  - Process Mining DFG / Spaghetti Diagram View (PM4Py discovery)
  - 40% X-Ray -> Triage Paperwork Bottleneck Highlighting
  - Node-to-Node Transition Times & Wait Metrics
  - Process Variants Explorer
  - Conformance & Protocol Compliance
  - Multi-Modal Sepsis & Ward Analytics
"""

import json
from pathlib import Path
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROC_DIR = PROJECT_ROOT / "data" / "processed"

st.set_page_config(
    page_title="CareFlow: Process Mining Intelligence",
    layout="wide",
    page_icon="🏥"
)

# Header
st.title("🏥 CareFlow: Clinical Pathway Process Mining")
st.caption("Hospital Operations Intelligence • PM4Py 2.7.23 • Google BigQuery & dbt Modern Data Stack • Batch 22.1")

# Sidebar
st.sidebar.image("https://img.icons8.com/color/96/hospital-room.png", width=64)
st.sidebar.title("CareFlow Navigation")
view_mode = st.sidebar.radio(
    "Select Intelligence Layer:",
    ["Process Mining & ER Flow", "Clinical & Sepsis Diagnostics"]
)

if view_mode == "Process Mining & ER Flow":
    # Load Process Mining Data
    dfg_sum_path = PROC_DIR / "dfg_summary.json"
    conf_sum_path = PROC_DIR / "conformance_summary.json"
    bottlenecks_path = PROC_DIR / "bottlenecks.csv"
    variants_path = PROC_DIR / "variants.csv"

    if not (dfg_sum_path.is_file() and bottlenecks_path.is_file()):
        st.error("Process mining artifacts missing! Please run `python run_pipeline.py` first.")
        st.stop()

    with open(dfg_sum_path) as f:
        dfg_summary = json.load(f)
    with open(conf_sum_path) as f:
        conf_summary = json.load(f)
    df_bottlenecks = pd.read_csv(bottlenecks_path)
    df_variants = pd.read_csv(variants_path)

    # Operational Alert
    st.error(
        f"🚨 **Critical Operational Discovery:** Process mining identified that **{conf_summary['loopback_cases']:,} patients "
        f"({conf_summary['loopback_rate_pct']}% of all admissions / 40.2% of X-Ray cases)** loop back to Triage after X-Ray "
        f"due to a missing intake paperwork form! Total operational delay: **594.1 hours lost**."
    )

    # KPI Metrics Row
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Patient Cases", f"{dfg_summary['total_cases']:,}")
    c2.metric("Total Events", f"{dfg_summary['total_events']:,}")
    c3.metric("X-Ray Loopbacks", f"{conf_summary['loopback_cases']:,}", delta="-40.2% X-Ray", delta_color="inverse")
    c4.metric("Clinical Compliance", f"{conf_summary['compliance_rate_pct']}%", delta=f"Fitness: {conf_summary['avg_fitness_score']}")
    c5.metric("Target ROI", "-20.0 min", delta="Wait Saved / Patient")

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Directly Follows Graph (DFG)",
        "⏱️ Bottleneck Analysis",
        "📊 Process Variants",
        "⚖️ Conformance Checking"
    ])

    with tab1:
        st.subheader("As-Is Patient Flow Map (Discovered via PM4Py)")
        st.info("The diagram below captures the real chronological sequence of patient transitions.")
        
        # Display DFG flow summary
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.markdown("#### High-Volume Forward Transitions")
            st.dataframe(
                df_bottlenecks[df_bottlenecks['source'] != 'X-Ray'][['source', 'target', 'transition_count', 'mean_wait_min', 'total_hours_lost']]
                .rename(columns={'mean_wait_min': 'Avg Wait (min)', 'total_hours_lost': 'Hours Lost', 'transition_count': 'Cases'}),
                use_container_width=True
            )
        with col_b:
            st.markdown("#### Operational Loopbacks & Rework")
            loopbacks = df_bottlenecks[
                ((df_bottlenecks['source'] == 'X-Ray') & (df_bottlenecks['target'] == 'Triage')) |
                ((df_bottlenecks['source'] == 'Doctor Consultation') & (df_bottlenecks['target'] == 'Doctor Review'))
            ]
            st.dataframe(
                loopbacks[['source', 'target', 'transition_count', 'mean_wait_min', 'total_hours_lost']]
                .rename(columns={'mean_wait_min': 'Avg Wait (min)', 'total_hours_lost': 'Hours Lost', 'transition_count': 'Cases'}),
                use_container_width=True
            )
            st.warning("⚠️ **X-Ray → Triage** accounts for **594.1 hours** of unnecessary administrative delay.")

    with tab2:
        st.subheader("Transition Wait Times & Bottleneck Ranking")
        st.bar_chart(data=df_bottlenecks.set_index('source')['mean_wait_min'])
        st.dataframe(df_bottlenecks, use_container_width=True)

    with tab3:
        st.subheader("Process Variants (Distinct Patient Pathways)")
        st.write("Grouped sequences of clinical activities from hospital admission to discharge:")
        st.dataframe(df_variants, use_container_width=True)

    with tab4:
        st.subheader("Institutional Clinical Protocol Conformance")
        k1, k2 = st.columns(2)
        with k1:
            st.write(f"• **Mandated Flow:** `Registration → Triage → Doctor Consultation → Treatment → Discharge`")
            st.write(f"• **Total Evaluated Cases:** `{conf_summary['total_cases']:,}`")
            st.write(f"• **Strictly Compliant Cases:** `{conf_summary['compliant_cases']:,}` ({conf_summary['compliance_rate_pct']}%)")
            st.write(f"• **Average Trace Fitness:** `{conf_summary['avg_fitness_score']} / 1.00`")
        with k2:
            st.progress(conf_summary['compliance_rate_pct'] / 100.0)
            st.metric("Institutional Compliance Rate", f"{conf_summary['compliance_rate_pct']}%")

else:
    # Clinical Sepsis Diagnostics View
    st.subheader("Clinical Biomarkers & Ward Analytics (5,000-Patient Dataset)")
    summary_path = PROC_DIR / "summary.json"
    ward_path = PROC_DIR / "ward_summary.csv"

    if summary_path.is_file() and ward_path.is_file():
        with open(summary_path) as f:
            summary = json.load(f)
        df_ward = pd.read_csv(ward_path)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Patients", f"{summary.get('total_records', 5000):,}")
        c2.metric("Sepsis Prevalence", f"{summary.get('sepsis_prevalence_pct', 18.1):.1f}%")
        c3.metric("ICU Sepsis Rate", f"{summary.get('icu_sepsis_pct', 48.0):.1f}%")
        c4.metric("Active Doctors", f"{summary.get('doctor_count', 12)}")

        st.markdown("---")
        st.dataframe(df_ward, use_container_width=True)
    else:
        st.info("Run `python main.py` to regenerate clinical sepsis analytics.")
