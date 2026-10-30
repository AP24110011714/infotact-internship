"""
CareFlow - Page 1: Executive Overview
High-level operational overview, volume throughput, admission trends, and hospital KPIs.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import config
from src import dashboard_utils, eda, conformance_analysis, data_validation, visualizations

st.set_page_config(page_title="Executive Overview | CareFlow", page_icon="📊", layout="wide")
dashboard_utils.inject_custom_styles()

df = dashboard_utils.get_cached_dataset()
filtered_df = dashboard_utils.render_sidebar_filters(df)

st.title("📊 Executive Operational Overview")
st.markdown("Hospital-wide clinical pathway throughput, admission dynamics, and institutional KPIs.")

# Calculate KPIs
kpis = eda.compute_kpi_summary(filtered_df)
conformance = conformance_analysis.run_cohort_conformance_analysis(filtered_df)
val_report = data_validation.compute_data_quality_report(filtered_df)

# Top KPI Row
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    dashboard_utils.render_kpi_card("Total Patients", f"{kpis['total_cases']:,}", "Active cohort")
with col2:
    dashboard_utils.render_kpi_card("Total Activities", f"{kpis['total_events']:,}", "Events logged")
with col3:
    dashboard_utils.render_kpi_card("Avg Journey Stay", f"{kpis['avg_los_hours']}h", f"~{kpis['avg_los_days']} days")
with col4:
    dashboard_utils.render_kpi_card("Activities / Case", f"{kpis['avg_events_per_case']}", "Event intensity")
with col5:
    dashboard_utils.render_kpi_card("Deviation Rate", f"{conformance['deviation_rate_pct']}%", f"{conformance['deviating_cases']:,} cases")
with col6:
    dashboard_utils.render_kpi_card("Data Quality", f"{val_report['overall_quality_score']}%", f"Grade {val_report['quality_grade']}")

st.markdown("---")

# Row 2: Admission Cohorts & Department Workload
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🏥 Admission Type Distribution & Length of Stay")
    adm_df = eda.get_admission_type_analysis(filtered_df)
    fig_adm = px.bar(
        adm_df,
        x="Admission_Type",
        y="Patient_Count",
        color="Avg_LOS_Hours",
        color_continuous_scale="Teal",
        title="Patient Volume & Average Length of Stay by Admission Cohort",
        labels={"Patient_Count": "Patient Volume", "Admission_Type": "Admission Type", "Avg_LOS_Hours": "Avg LOS (Hrs)"},
        template="plotly_white",
        text="Patient_Count"
    )
    fig_adm.update_traces(textposition="outside")
    st.plotly_chart(fig_adm, use_container_width=True)

with col_right:
    st.subheader("🏢 Clinical Department Workload Share")
    dept_df = eda.get_department_distribution(filtered_df)
    fig_pie = px.pie(
        dept_df,
        names="Department",
        values="Total_Activities",
        title="Department Clinical Event Workload Share (%)",
        hole=0.45,
        color_discrete_sequence=px.colors.sequential.Teal
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# Row 3: Temporal Trends (Monthly and Day-of-Week)
st.subheader("📅 Hospital Admission Dynamics & Temporal Trends")
m_trend, dow_trend = eda.get_temporal_admission_trends(filtered_df)

col_t1, col_t2 = st.columns([3, 2])
with col_t1:
    fig_month = px.line(
        m_trend,
        x="Year_Month",
        y="Admission_Count",
        markers=True,
        title="Monthly Patient Admission Volume Over Time",
        labels={"Year_Month": "Admission Month", "Admission_Count": "New Admissions"},
        template="plotly_white",
        line_shape="spline"
    )
    fig_month.update_traces(line_color=config.THEME_COLORS["primary"], line_width=3)
    st.plotly_chart(fig_month, use_container_width=True)

with col_t2:
    fig_dow = px.bar(
        dow_trend,
        x="Day_of_Week",
        y="Admission_Count",
        title="Patient Arrivals by Day of Week",
        labels={"Day_of_Week": "Day", "Admission_Count": "Admissions"},
        template="plotly_white",
        color_discrete_sequence=[config.THEME_COLORS["secondary"]]
    )
    st.plotly_chart(fig_dow, use_container_width=True)
