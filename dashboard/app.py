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

st.subheader("Most common patient pathways (variants)")

top_n = st.slider("Number of variants to show", 3, 15, 10)
top = var.head(top_n).copy()
top["label"] = [f"V{i + 1}" for i in range(len(top))]

st.bar_chart(top.set_index("label")["cases"])

st.caption("Each bar is one pathway. V1 is the most common. "
           "Full sequences are listed below.")
st.dataframe(top[["label", "variant", "cases", "percent"]],
             use_container_width=True)

q = X_scaled['Insulin'].quantile(.95)
mask = X_scaled['Insulin'] < q
dataNew = X_scaled[mask]
y_outlier_detection = y_outlier_detection[mask]
