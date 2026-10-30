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

# ---- Sidebar filters ----
st.sidebar.header("Filters")

max_h = float(dur["duration_hours"].max())
hours = st.sidebar.slider("Case duration (hours)", 0.0, max_h, (0.0, max_h))
dur = dur[dur["duration_hours"].between(hours[0], hours[1])]
rep = rep[rep.iloc[:, 0].isin(dur.iloc[:, 0])]

acts = sorted(set(wait["from"]).union(wait["to"]))
chosen = st.sidebar.multiselect("Show transitions involving these activities", acts)
if chosen:
    wait = wait[wait["from"].isin(chosen) | wait["to"].isin(chosen)]

if dur.empty:
    st.warning("No cases match the selected filters.")
    st.stop()
    st.subheader("Conformance to the ideal pathway")

    conf = load("conformance_results.csv")
    ok = int(conf["conforms"].sum())
    n = len(conf)
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Conforming cases", f"{ok:,}")
    k2.metric("Non-conforming cases", f"{n - ok:,}")
    k3.metric("Conformance rate", f"{ok / n * 100:.1f}%")
    
    dev = (conf.loc[~conf["conforms"], "missing_or_out_of_order"]
           .value_counts().head(10).rename("cases"))
    if not dev.empty:
        st.bar_chart(dev)
        st.caption("Most common deviations: key steps that are missing or out "
                   "of order. This is a simplified order check, not a full "
                   "token-based replay.")
    
    st.dataframe(conf[~conf["conforms"]].head(50), use_container_width=True)
