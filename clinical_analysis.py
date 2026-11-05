"""Generate patient-level clinical summaries from the cleaned dataset."""

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = PROJECT_ROOT / "data" / "processed" / "Sepsis_Dataset_cleaned.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_FINDINGS = PROJECT_ROOT / "docs" / "findings.md"

CLINICAL_METRICS = {
    "temperature_c": ("Temperature", "°C"),
    "bp_systolic": ("Systolic blood pressure", "mmHg"),
    "bp_diastolic": ("Diastolic blood pressure", "mmHg"),
    "heart_rate": ("Heart rate", "bpm"),
    "wbc_count": ("White blood cell count", "10^9/L"),
    "lactate_mmol_l": ("Lactate", "mmol/L"),
}


def _sepsis_labels(df: pd.DataFrame) -> pd.Series:
    if "sepsis_flag" not in df.columns:
        return pd.Series("Unknown", index=df.index, dtype="string")
    return df["sepsis_flag"].astype("string").fillna("Unknown")


def _write_findings(
    summary: dict[str, object],
    metrics: pd.DataFrame,
    wards: pd.DataFrame,
    cleaning_report: dict[str, object] | None,
    path: Path,
) -> None:
    lines = [
        "# CareFlow Clinical Data Findings",
        "",
        "## Dataset overview",
        f"- Unique patients: {summary['total_patients']}",
        f"- Admission date range: {summary['earliest_admission']} to {summary['latest_admission']}",
        f"- Sepsis-positive records: {summary['sepsis_positive']}",
        f"- Sepsis-negative records: {summary['sepsis_negative']}",
        f"- Records with unknown sepsis status: {summary['sepsis_unknown']}",
    ]

    if summary["sepsis_rate_percent"] is None:
        lines.append("- Sepsis rate: unavailable because no records have a known status.")
    else:
        lines.append(
            f"- Sepsis rate among records with a known status: "
            f"{summary['sepsis_rate_percent']:.1f}%"
        )

    lines.extend(["", "## Clinical measurements", ""])
    if metrics.empty:
        lines.append("No supported clinical measurement columns were available.")
    else:
        lines.extend(
            [
                "| Measurement | Unit | Valid values | Missing values | Mean | Median |",
                "| --- | --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for _, row in metrics.iterrows():
            mean = "N/A" if pd.isna(row["mean"]) else f"{row['mean']:.2f}"
            median = "N/A" if pd.isna(row["median"]) else f"{row['median']:.2f}"
            lines.append(
                f"| {row['label']} | {row['unit']} | {row['valid_values']} | "
                f"{row['missing_values']} | {mean} | {median} |"
            )

    lines.extend(["", "## Patients by ward", ""])
    if wards.empty:
        lines.append("No ward information was available.")
    else:
        lines.extend(
            [
                "| Ward | Patients | Sepsis-positive |",
                "| --- | ---: | ---: |",
            ]
        )
        for _, row in wards.iterrows():
            lines.append(
                f"| {row['ward']} | {row['patients']} | {row['sepsis_positive']} |"
            )

    if cleaning_report:
        invalid_count = cleaning_report["invalid_numeric_measurements"]
        lines.extend(
            [
                "",
                "## Data quality",
                f"- Rows removed for missing patient ID or admission date: "
                f"{cleaning_report['rows_missing_required_fields_removed']}",
                f"- Duplicate patient records removed: {cleaning_report['duplicates_removed']}",
                f"- Out-of-range numeric measurements set to missing: {invalid_count}",
            ]
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "These are descriptive summaries of the supplied patient-level records. "
            "They do not establish causes, diagnose sepsis, or measure care pathways. "
            "The supplied workbook currently labels every record as sepsis-negative, "
            "so comparisons between positive and negative groups are not possible.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def analyze_dataset(
    cleaned_path: str | Path = DEFAULT_INPUT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    findings_path: str | Path = DEFAULT_FINDINGS,
    cleaning_report: dict[str, object] | None = None,
) -> dict[str, object]:
    """Create patient, ward, sepsis-label, and clinical-measurement summaries."""
    df = pd.read_csv(cleaned_path, parse_dates=["admission_date"])
    required = {"patient_id", "admission_date"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Cleaned dataset is missing required columns: {sorted(missing)}")
    if df.empty:
        raise ValueError("The cleaned dataset contains no patient records.")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    sepsis = _sepsis_labels(df)
    status_counts = sepsis.value_counts()
    known_statuses = sepsis.isin(["Yes", "No"])
    positive = int((sepsis == "Yes").sum())
    negative = int((sepsis == "No").sum())
    known_count = positive + negative

    summary: dict[str, object] = {
        "total_patients": int(df["patient_id"].nunique()),
        "total_records": int(len(df)),
        "sepsis_positive": positive,
        "sepsis_negative": negative,
        "sepsis_unknown": int((~known_statuses).sum()),
        "sepsis_rate_percent": round(positive / known_count * 100, 2)
        if known_count
        else None,
        "earliest_admission": str(df["admission_date"].min().date()),
        "latest_admission": str(df["admission_date"].max().date()),
    }

    sepsis_summary = (
        sepsis.value_counts()
        .rename_axis("sepsis_status")
        .rename("patients")
        .reset_index()
    )
    sepsis_summary["percent"] = (
        sepsis_summary["patients"] / len(df) * 100
    ).round(2)
    sepsis_summary.to_csv(output / "sepsis_summary.csv", index=False)

    work = df.copy()
    work["sepsis_status"] = sepsis
    if "ward" not in work.columns:
        work["ward"] = "Unknown"
    else:
        work["ward"] = work["ward"].fillna("Unknown")
    ward_summary = (
        work.groupby("ward", dropna=False)
        .agg(
            patients=("patient_id", "nunique"),
            sepsis_positive=("sepsis_status", lambda values: int((values == "Yes").sum())),
            known_sepsis_status=("sepsis_status", lambda values: int(values.isin(["Yes", "No"]).sum())),
        )
        .reset_index()
        .sort_values("patients", ascending=False)
    )
    ward_summary["sepsis_rate_percent"] = (
        ward_summary["sepsis_positive"]
        .div(ward_summary["known_sepsis_status"].where(ward_summary["known_sepsis_status"] > 0))
        .mul(100)
        .round(2)
    )
    ward_summary.to_csv(output / "ward_summary.csv", index=False)

    metric_rows = []
    metric_group_rows = []
    for column, (label, unit) in CLINICAL_METRICS.items():
        if column not in df.columns:
            continue
        values = pd.to_numeric(df[column], errors="coerce")
        metric_rows.append(
            {
                "metric": column,
                "label": label,
                "unit": unit,
                "valid_values": int(values.notna().sum()),
                "missing_values": int(values.isna().sum()),
                "mean": values.mean(),
                "median": values.median(),
                "minimum": values.min(),
                "maximum": values.max(),
            }
        )
        groups = pd.DataFrame({"sepsis_status": sepsis, "value": values})
        grouped = groups.groupby("sepsis_status", dropna=False)["value"].agg(
            patients="count", mean="mean", median="median"
        )
        for status, row in grouped.iterrows():
            metric_group_rows.append(
                {
                    "metric": column,
                    "label": label,
                    "unit": unit,
                    "sepsis_status": status,
                    "patients": int(row["patients"]),
                    "mean": row["mean"],
                    "median": row["median"],
                }
            )

    metrics = pd.DataFrame(
        metric_rows,
        columns=[
            "metric",
            "label",
            "unit",
            "valid_values",
            "missing_values",
            "mean",
            "median",
            "minimum",
            "maximum",
        ],
    )
    metrics.to_csv(output / "clinical_metrics_summary.csv", index=False)
    pd.DataFrame(
        metric_group_rows,
        columns=["metric", "label", "unit", "sepsis_status", "patients", "mean", "median"],
    ).to_csv(output / "clinical_metrics_by_sepsis.csv", index=False)

    missingness = df.isna().sum().rename_axis("column").rename("missing_values").reset_index()
    missingness["percent_missing"] = (missingness["missing_values"] / len(df) * 100).round(2)
    missingness.to_csv(output / "missingness_summary.csv", index=False)

    (output / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    _write_findings(
        summary,
        metrics,
        ward_summary,
        cleaning_report,
        Path(findings_path),
    )
    return summary
