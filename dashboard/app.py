"""CareFlow Streamlit Dashboard — 5,000-patient sepsis analytics."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed"

st.set_page_config(page_title="CareFlow Clinical Dashboard", layout="wide", page_icon="🏥")
st.title("🏥 CareFlow: Sepsis Clinical Analytics")
st.caption("Synthetic 5,000-patient dataset · Infotact Solutions Data Analytics Internship")

# ── load outputs ────────────────────────────────────────────────────────────
required_files = {
    "cleaned dataset":        DATA_DIR / "Sepsis_Dataset_cleaned.csv",
    "analysis summary":       DATA_DIR / "summary.json",
    "clinical measurements":  DATA_DIR / "clinical_metrics_summary.csv",
    "clinical by sepsis":     DATA_DIR / "clinical_metrics_by_sepsis.csv",
    "ward summary":           DATA_DIR / "ward_summary.csv",
    "sepsis summary":         DATA_DIR / "sepsis_summary.csv",
}
missing = [lbl for lbl, p in required_files.items() if not p.is_file()]
if missing:
    st.error(f"Missing outputs: {', '.join(missing)}. Run `python main.py` then refresh.")
    st.stop()

@st.cache_data
def load_data():
    summary  = json.loads((DATA_DIR / "summary.json").read_text(encoding="utf-8"))
    patients = pd.read_csv(DATA_DIR / "Sepsis_Dataset_cleaned.csv", parse_dates=["admission_date"])
    metrics  = pd.read_csv(DATA_DIR / "clinical_metrics_summary.csv")
    by_sep   = pd.read_csv(DATA_DIR / "clinical_metrics_by_sepsis.csv")
    wards    = pd.read_csv(DATA_DIR / "ward_summary.csv")
    return summary, patients, metrics, by_sep, wards

summary, patients, metrics, by_sep, wards = load_data()

# ── sidebar filters ──────────────────────────────────────────────────────────
st.sidebar.header("Filters")
all_wards = sorted(patients["ward"].dropna().unique())
sel_wards = st.sidebar.multiselect("Ward", all_wards, default=all_wards)
sel_flags = st.sidebar.multiselect("Sepsis status", ["Yes", "No"], default=["Yes", "No"])

filtered = patients[
    patients["ward"].isin(sel_wards) &
    patients["sepsis_flag"].isin(sel_flags)
].copy()

if filtered.empty:
    st.warning("No patients match the selected filters.")
    st.stop()

# ── KPI row ──────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
n_total  = len(filtered)
n_yes    = int((filtered["sepsis_flag"] == "Yes").sum())
n_no     = int((filtered["sepsis_flag"] == "No").sum())
rate     = n_yes / n_total * 100 if n_total else 0
avg_hr   = filtered["heart_rate"].mean()

c1.metric("Patients",        f"{n_total:,}")
c2.metric("Sepsis-positive", f"{n_yes:,}")
c3.metric("Sepsis-negative", f"{n_no:,}")
c4.metric("Sepsis rate",     f"{rate:.1f}%")
c5.metric("Avg heart rate",  f"{avg_hr:.0f} bpm" if not pd.isna(avg_hr) else "N/A")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Clinical Measurements", "🏨 Ward Analysis", "📋 Patient Records", "📈 Sepsis Trends"]
)

# TAB 1 — Clinical measurements
with tab1:
    st.subheader("Clinical Measurements by Sepsis Status")
    metric_names = metrics["metric"].tolist()
    metric_labels = dict(zip(metrics["metric"], metrics["label"]))

    chosen = st.selectbox(
        "Select measurement",
        metric_names,
        format_func=lambda k: metric_labels.get(k, k),
    )
    metric_row = metrics[metrics["metric"] == chosen].iloc[0]

    col_a, col_b = st.columns(2)
    with col_a:
        # Overall stats
        vals = pd.to_numeric(filtered[chosen], errors="coerce").dropna()
        stat1, stat2, stat3, stat4 = st.columns(4)
        stat1.metric("Valid values", f"{len(vals):,}")
        stat2.metric("Mean", f"{vals.mean():.2f}")
        stat3.metric("Median", f"{vals.median():.2f}")
        stat4.metric("Missing", f"{len(filtered) - len(vals):,}")
        st.bar_chart(vals.rename(metric_row["label"]))

    with col_b:
        # Sepsis vs non-sepsis comparison
        st.write("**Mean comparison: Sepsis+ vs Sepsis−**")
        sub = by_sep[by_sep["metric"] == chosen].copy()
        sub = sub[sub["sepsis_status"].isin(["Yes", "No"])].set_index("sepsis_status")
        if not sub.empty:
            chart_data = sub[["mean"]].rename(columns={"mean": metric_row["label"]})
            st.bar_chart(chart_data)
            for status in ["Yes", "No"]:
                if status in sub.index:
                    r = sub.loc[status]
                    label = "Sepsis+" if status == "Yes" else "Sepsis−"
                    st.metric(f"{label} mean", f"{r['mean']:.2f} {metric_row['unit']}", delta=None)

# TAB 2 — Ward analysis
with tab2:
    st.subheader("Patients and Sepsis Rates by Ward")
    ward_filtered = wards[wards["ward"].isin(sel_wards)].copy()

    col_x, col_y = st.columns(2)
    with col_x:
        st.write("**Patients per ward**")
        ward_counts = filtered.groupby("ward")["patient_id"].count().sort_values(ascending=False)
        st.bar_chart(ward_counts)

    with col_y:
        st.write("**Sepsis rate per ward (%)**")
        rate_data = ward_filtered.set_index("ward")["sepsis_rate_percent"].dropna().sort_values(ascending=False)
        st.bar_chart(rate_data)

    st.write("**Ward summary table**")
    display_cols = ["ward", "patients", "sepsis_positive", "sepsis_rate_percent"]
    display_cols = [c for c in display_cols if c in ward_filtered.columns]
    st.dataframe(ward_filtered[display_cols].sort_values("patients", ascending=False), hide_index=True)

    st.write("**Patients by doctor**")
    doc_counts = filtered.groupby("doctor_on_duty")["patient_id"].count().sort_values(ascending=False)
    st.bar_chart(doc_counts)

# TAB 3 — Patient records
with tab3:
    st.subheader("Patient Records")
    st.write(f"Showing {len(filtered):,} patients matching the current filters.")
    st.dataframe(
        filtered.sort_values("admission_date", ascending=False).reset_index(drop=True),
        hide_index=True,
        use_container_width=True,
    )
    csv_out = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download filtered dataset (CSV)",
        data=csv_out,
        file_name="careflow_filtered.csv",
        mime="text/csv",
    )

# TAB 4 — Sepsis trends
with tab4:
    st.subheader("Sepsis Admissions Over Time")
    time_df = filtered.copy()
    time_df["month"] = time_df["admission_date"].dt.to_period("M").astype(str)
    monthly_all = time_df.groupby("month")["patient_id"].count().rename("All patients")
    monthly_sep = time_df[time_df["sepsis_flag"] == "Yes"].groupby("month")["patient_id"].count().rename("Sepsis+")
    trend = pd.concat([monthly_all, monthly_sep], axis=1).fillna(0).astype(int)
    st.line_chart(trend)

    st.subheader("Sepsis Status Distribution")
    sep_dist = filtered["sepsis_flag"].value_counts().rename_axis("Status").reset_index(name="Patients")
    st.bar_chart(sep_dist.set_index("Status"))

st.divider()
st.caption(
    f"Dataset: Sepsis_Dataset_5000.csv | "
    f"Range: {summary['earliest_admission']} → {summary['latest_admission']} | "
    "Descriptive results only — not medical advice."
)
