"""Streamlit dashboard for the patient-level CareFlow clinical dataset."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed"

st.set_page_config(page_title="CareFlow Clinical Dashboard", layout="wide")
st.title("CareFlow: Sepsis Clinical Data Overview")
st.caption(
    "Descriptive patient-level summaries. This dataset does not contain event "
    "sequences or timestamps for process mining."
)

summary_path = DATA_DIR / "summary.json"
required_files = {
    "cleaned dataset": DATA_DIR / "Sepsis_Dataset_cleaned.csv",
    "analysis summary": summary_path,
    "clinical measurements": DATA_DIR / "clinical_metrics_summary.csv",
    "ward summary": DATA_DIR / "ward_summary.csv",
    "sepsis summary": DATA_DIR / "sepsis_summary.csv",
}
missing_files = [label for label, path in required_files.items() if not path.is_file()]
if missing_files:
    st.error(
        "Analysis outputs are missing: "
        + ", ".join(missing_files)
        + ". Run `python main.py` from the project folder, then refresh this page."
    )
    st.stop()

try:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    patients = pd.read_csv(required_files["cleaned dataset"], parse_dates=["admission_date"])
    metrics = pd.read_csv(required_files["clinical measurements"])
    wards = pd.read_csv(required_files["ward summary"])
    sepsis = pd.read_csv(required_files["sepsis summary"])
    grouped_metrics_path = DATA_DIR / "clinical_metrics_by_sepsis.csv"
    grouped_metrics = pd.read_csv(grouped_metrics_path) if grouped_metrics_path.is_file() else pd.DataFrame()
except (OSError, ValueError, json.JSONDecodeError, pd.errors.ParserError) as exc:
    st.error(f"Could not load generated analysis outputs: {exc}")
    st.stop()

if patients.empty:
    st.error("The cleaned dataset contains no patient records. Check the source file and rerun `python main.py`.")
    st.stop()

left, right = st.columns(2)
with left:
    selected_wards = st.multiselect("Filter by ward", sorted(patients["ward"].dropna().unique()) if "ward" in patients else [])
with right:
    selected_statuses = st.multiselect(
        "Filter by sepsis status",
        sorted(patients["sepsis_flag"].dropna().unique()) if "sepsis_flag" in patients else [],
    )

filtered = patients.copy()
if selected_wards and "ward" in filtered.columns:
    filtered = filtered[filtered["ward"].isin(selected_wards)]
if selected_statuses and "sepsis_flag" in filtered.columns:
    filtered = filtered[filtered["sepsis_flag"].isin(selected_statuses)]

if filtered.empty:
    st.warning("No patients match the selected filters.")
    st.stop()

metric_columns = st.columns(4)
metric_columns[0].metric("Patients", f"{filtered['patient_id'].nunique():,}")
metric_columns[1].metric(
    "Sepsis positive",
    f"{int((filtered['sepsis_flag'] == 'Yes').sum()):,}" if "sepsis_flag" in filtered else "N/A",
)
known_statuses = filtered["sepsis_flag"].isin(["Yes", "No"]) if "sepsis_flag" in filtered else pd.Series(dtype=bool)
known_count = int(known_statuses.sum())
if known_count:
    rate = (filtered.loc[known_statuses, "sepsis_flag"] == "Yes").mean() * 100
    rate_display = f"{rate:.1f}%"
else:
    rate_display = "N/A"
metric_columns[2].metric("Sepsis rate (known status)", rate_display)
metric_columns[3].metric(
    "Admission dates",
    f"{filtered['admission_date'].min():%Y-%m-%d} – {filtered['admission_date'].max():%Y-%m-%d}",
)

st.subheader("Clinical measurements")
available_metrics = metrics[metrics["metric"].isin(filtered.columns)].copy()
if available_metrics.empty:
    st.info("No supported clinical measurement columns are available.")
else:
    chosen_metric = st.selectbox(
        "Choose a measurement",
        available_metrics["metric"].tolist(),
        format_func=lambda key: available_metrics.loc[
            available_metrics["metric"] == key, "label"
        ].iloc[0],
    )
    metric_row = available_metrics.loc[available_metrics["metric"] == chosen_metric].iloc[0]
    measure = pd.to_numeric(filtered[chosen_metric], errors="coerce").dropna()
    if measure.empty:
        st.info("No valid values are available for this measurement under the current filters.")
    else:
        stat_cols = st.columns(4)
        stat_cols[0].metric("Valid values", f"{len(measure):,}")
        stat_cols[1].metric("Mean", f"{measure.mean():.2f} {metric_row['unit']}")
        stat_cols[2].metric("Median", f"{measure.median():.2f} {metric_row['unit']}")
        stat_cols[3].metric("Missing", f"{len(filtered) - len(measure):,}")
        st.bar_chart(measure.rename(metric_row["label"]))
        if not grouped_metrics.empty and not selected_wards and not selected_statuses:
            subset = grouped_metrics[grouped_metrics["metric"] == chosen_metric]
            subset = subset[subset["patients"] > 0].set_index("sepsis_status")
            if not subset.empty:
                st.caption("Measurement averages by sepsis status")
                st.bar_chart(subset["mean"])

st.subheader("Patients by ward")
if "ward" in filtered.columns:
    ward_counts = filtered.groupby("ward")["patient_id"].nunique().sort_values(ascending=False)
    if not ward_counts.empty:
        st.bar_chart(ward_counts)
    st.dataframe(
        wards[wards["ward"].isin(filtered["ward"].unique())],
        width="stretch",
        hide_index=True,
    )

st.subheader("Sepsis status distribution")
if "sepsis_flag" in filtered.columns:
    status_counts = filtered["sepsis_flag"].fillna("Unknown").value_counts()
    st.bar_chart(status_counts)

st.subheader("Patient records")
display_columns = [column for column in patients.columns if column in filtered.columns]
st.dataframe(
    filtered[display_columns].sort_values("admission_date", ascending=False),
    width="stretch",
    hide_index=True,
)

st.caption(
    f"Source range: {summary['earliest_admission']} to {summary['latest_admission']}. "
    "Descriptive results only; they do not establish diagnosis, cause, or care quality."
)
