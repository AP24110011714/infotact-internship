
import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path

# Project paths
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
MINING = OUTPUTS / "process_mining"

st.set_page_config(
    page_title="CareFlow Dashboard",
    page_icon="🏥",
    layout="wide"
)

st.title("CareFlow: Clinical Pathway Process Mining")
st.caption("Hospital patient journey analysis | Data Analytics Internship")

# Load CSV files
@st.cache_data
def load_csv(path):
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


events = load_csv(DATA / "hospital_event_log_clean.csv")
durations = load_csv(MINING / "patient_visit_duration.csv")
transitions = load_csv(MINING / "transition_performance.csv")
activities = load_csv(MINING / "activity_frequency.csv")
kpis = load_csv(OUTPUTS / "kpi_summary.csv")
loopbacks = load_csv(OUTPUTS / "loopbacks.csv")

# Validate essential data
if events.empty:
    st.error("Hospital event log not found. Please check data/processed/")
    st.stop()

events["timestamp"] = pd.to_datetime(events["timestamp"], errors="coerce")
events = events.dropna(subset=["timestamp"])

# Sidebar filters
st.sidebar.header("Dashboard Filters")

departments = sorted(events["department"].dropna().unique())
selected_departments = st.sidebar.multiselect(
    "Department",
    departments,
    default=departments
)

event_activities = sorted(events["activity"].dropna().unique())
selected_activities = st.sidebar.multiselect(
    "Activity",
    event_activities,
    default=event_activities
)

filtered = events[
    events["department"].isin(selected_departments)
    & events["activity"].isin(selected_activities)
].copy()

selected_cases = filtered["case_id"].nunique()

# KPI values
if not kpis.empty:
    total_cases = int(kpis.iloc[0]["total_cases"])
    total_events = int(kpis.iloc[0]["total_events"])
    avg_duration = float(kpis.iloc[0]["avg_case_duration_minutes"])
    avg_wait = float(kpis.iloc[0]["avg_wait_minutes"])
    loopback_rate = float(kpis.iloc[0]["loopback_rate"])
else:
    total_cases = events["case_id"].nunique()
    total_events = len(events)
    avg_duration = (
        durations["duration_minutes"].mean()
        if not durations.empty else 0
    )
    avg_wait = (
        transitions["average_wait_minutes"].mean()
        if not transitions.empty else 0
    )
    loopback_rate = 0

# Overview
st.subheader("Hospital Process Overview")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Cases", f"{total_cases:,}")
c2.metric("Total Events", f"{total_events:,}")
c3.metric("Avg Duration", f"{avg_duration:.2f} min")
c4.metric("Avg Waiting Time", f"{avg_wait:.2f} min")
c5.metric("Loopback Rate", f"{loopback_rate:.1f}%")

st.caption(
    f"Filtered view: {selected_cases:,} patient cases | "
    f"{len(filtered):,} events"
)

st.divider()

# Patient visit duration
st.subheader("Patient Visit Duration")

if not durations.empty:
    fig = px.histogram(
        durations,
        x="duration_minutes",
        nbins=20,
        title="Distribution of Patient Visit Duration",
        labels={"duration_minutes": "Duration (minutes)"}
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        durations.sort_values(
            "duration_minutes", ascending=False
        ).head(10),
        use_container_width=True
    )
else:
    st.info("Patient visit duration data is unavailable.")

st.divider()

# Activity frequency
st.subheader("Activity Frequency")

if not activities.empty:
    fig = px.bar(
        activities.sort_values("event_count", ascending=False),
        x="activity",
        y="event_count",
        title="Number of Events by Activity",
        labels={
            "activity": "Hospital Activity",
            "event_count": "Event Count"
        }
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Transition performance
st.subheader("Transition Waiting Time Analysis")

if not transitions.empty:
    slowest = transitions.sort_values(
        "average_wait_minutes", ascending=False
    ).head(10)

    fig = px.bar(
        slowest,
        x="average_wait_minutes",
        y="from_activity",
        color="to_activity",
        orientation="h",
        title="Top 10 Slowest Transitions",
        labels={
            "average_wait_minutes": "Average Wait (minutes)",
            "from_activity": "From Activity",
            "to_activity": "To Activity"
        }
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(slowest, use_container_width=True)
else:
    st.info("Transition performance data is unavailable.")

st.divider()

# Loopback analysis
st.subheader("Process Loopback Analysis")

if not loopbacks.empty:
    st.metric("Recorded Loopback Transitions", len(loopbacks))

    st.dataframe(loopbacks, use_container_width=True)
else:
    st.info("No loopback records available.")

st.divider()

# Patient event log
st.subheader("Patient Event Log")

st.dataframe(
    filtered.sort_values(
        ["case_id", "timestamp"]
    ),
    use_container_width=True,
    height=350
)

# Download filtered data
csv_data = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Event Log",
    data=csv_data,
    file_name="careflow_filtered_events.csv",
    mime="text/csv"
)

st.caption("CareFlow | Clinical Pathway Process Mining")
