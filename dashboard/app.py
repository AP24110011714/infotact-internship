import pandas as pd
import streamlit as st

P = "data/processed/"

st.set_page_config(page_title="CareFlow Dashboard", layout="wide")
st.title("CareFlow: Clinical Pathway Process Mining")
st.caption("Analysis of the Sepsis hospital event log")


@st.cache_data
def load(name):
    return pd.read_csv(P + name)


dur = load("case_durations.csv")
var = load("variants.csv")
wait = load("transition_waiting_times.csv")
rep = load("repeated_activities_by_case.csv")

total = len(dur)
rework_cases = rep.iloc[:, 0].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total cases", f"{total:,}")
c2.metric("Median duration (hours)", f"{dur['duration_hours'].median():.2f}")
c3.metric("Unique variants", f"{len(var):,}")
c4.metric("Cases with rework", f"{rework_cases / total * 100:.1f}%")

st.subheader("Longest cases")
st.dataframe(dur.sort_values("duration_hours", ascending=False).head(10),
              use_container_width=True)

st.subheader("Slowest transitions")
st.dataframe(wait.head(10), use_container_width=True)
