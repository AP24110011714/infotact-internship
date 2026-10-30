"""
CareFlow - Page 2: Patient Journey Analysis
Interactive individual journey tracer, timeline visualization, department handoffs, and case-level conformance audit.
"""

import streamlit as st
import pandas as pd
import config
from src import dashboard_utils, process_mining, conformance_analysis, visualizations

st.set_page_config(page_title="Patient Journey Analysis | CareFlow", page_icon="🏥", layout="wide")
dashboard_utils.inject_custom_styles()

df = dashboard_utils.get_cached_dataset()
filtered_df = dashboard_utils.render_sidebar_filters(df)

st.title("🏥 Patient Journey & Clinical Trajectory Tracer")
st.markdown("Examine step-by-step clinical event sequences, waiting gaps, and department handoffs for individual patient cases.")

# Select Case ID
all_case_ids = sorted(filtered_df["Case_ID"].unique().tolist())
if not all_case_ids:
    st.warning("No cases match the selected sidebar filters. Please reset filters.")
    st.stop()

col_sel1, col_sel2 = st.columns([2, 3])
with col_sel1:
    selected_case = st.selectbox("Select Patient Journey (Case ID):", options=all_case_ids, index=0)

case_details = process_mining.get_patient_journey_details(filtered_df, selected_case)

if "error" in case_details:
    st.error(case_details["error"])
    st.stop()

# Case Metrics Banner
kcol1, kcol2, kcol3, kcol4, kcol5 = st.columns(5)
with kcol1:
    dashboard_utils.render_kpi_card("Admission Type", case_details["admission_type"], "Triage Priority")
with kcol2:
    dashboard_utils.render_kpi_card("Primary Diagnosis", case_details["diagnosis"][:20], "Admitting Diagnosis")
with kcol3:
    dashboard_utils.render_kpi_card("Total Journey Stay", f"{case_details['total_duration_hours']:.1f} hrs", f"~{case_details['total_duration_days']:.1f} days")
with kcol4:
    dashboard_utils.render_kpi_card("Total Activities", str(case_details["total_events"]), "Clinical Events")
with kcol5:
    dashboard_utils.render_kpi_card("Discharge Outcome", case_details["outcome_category"], case_details["outcome"][:22])

st.markdown("---")

# Individual Journey Timeline
st.subheader(f"⏱️ Chronological Timeline for Case: {selected_case}")
fig_timeline = visualizations.create_patient_journey_timeline(case_details["events_df"])
st.plotly_chart(fig_timeline, use_container_width=True)

# Step-by-Step Clinical Activity Log Table
st.subheader("📋 Step-by-Step Clinical Activity Audit")
events_display = case_details["events_df"][[
    "Activity", "Timestamp", "Department", "Resource", "Event_Status", "Step_Duration_Hours"
]].copy()
events_display.columns = ["Clinical Activity", "Timestamp", "Department", "Staff Resource", "Status", "Step Dwell (Hours)"]

st.dataframe(events_display, use_container_width=True, hide_index=True)

# Conformance Audit for this case
st.subheader("🔍 Case Conformance & Deviation Audit")
ref_name = st.selectbox("Reference Guideline for Comparison:", list(config.REFERENCE_PATHWAYS.keys()), index=0)
ref_pathway = config.REFERENCE_PATHWAYS[ref_name]

case_activities = case_details["events_df"]["Activity"].tolist()
conf_eval = conformance_analysis.evaluate_case_conformance(case_activities, ref_pathway)

c_col1, c_col2 = st.columns(2)
with c_col1:
    st.markdown(f"**Conformance Status:** {'✅ Fully Conforming' if conf_eval['is_conforming'] else '⚠️ Deviant Pathway'}")
    st.markdown(f"**Sequence Fitness Score:** `{conf_eval['fitness_score'] * 100:.1f}%`")
    st.markdown(f"**Observed Steps:** `{conf_eval['observed_length']}` | **Expected Reference Steps:** `{conf_eval['reference_length']}`")

with c_col2:
    if conf_eval["missing_activities"]:
        st.markdown(f"**Missing Expected Activities:** <span class='badge-critical'>{', '.join(conf_eval['missing_activities'])}</span>", unsafe_allow_html=True)
    else:
        st.markdown("**Missing Activities:** None (All expected steps present)")
        
    if conf_eval["unexpected_activities"]:
        st.markdown(f"**Unexpected / Extra Activities:** <span class='badge-warning'>{', '.join(conf_eval['unexpected_activities'])}</span>", unsafe_allow_html=True)
    else:
        st.markdown("**Unexpected Activities:** None")
        
    if conf_eval["repeated_activities"]:
        rep_str = ", ".join([f"{act} ({count}x)" for act, count in conf_eval["repeated_activities"].items()])
        st.markdown(f"**Repeated Activities (Loops):** <span class='badge-warning'>{rep_str}</span>", unsafe_allow_html=True)
    else:
        st.markdown("**Repeated Activities:** None (Linear sequence)")
