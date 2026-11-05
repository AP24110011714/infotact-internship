import pandas as pd
import pytest

from clinical_analysis import analyze_dataset
from data_cleaning import clean_dataset, normalize_flag, validate_numeric_columns


def test_normalize_flag_only_accepts_known_values():
    values = pd.Series([" Yes ", "y", "TRUE", "0", "unknown", None])
    assert normalize_flag(values).tolist()[:4] == ["Yes", "Yes", "Yes", "No"]
    assert pd.isna(normalize_flag(values).iloc[4])
    assert pd.isna(normalize_flag(values).iloc[5])


def test_invalid_measurements_become_missing_without_dropping_patients():
    frame = pd.DataFrame(
        {
            "patient_id": ["P1", "P2"],
            "lactate_mmol_l": [-1.0, 2.0],
            "wbc_count": [5.0, 50.0],
        }
    )
    cleaned, invalid = validate_numeric_columns(frame)
    assert len(cleaned) == 2
    assert pd.isna(cleaned.loc[0, "lactate_mmol_l"])
    assert pd.isna(cleaned.loc[1, "wbc_count"])
    assert invalid == {"wbc_count": 1, "lactate_mmol_l": 1}


def test_clean_dataset_standardizes_columns_and_reports_quality(tmp_path):
    source = tmp_path / "source.csv"
    output = tmp_path / "processed" / "clean.csv"
    pd.DataFrame(
        {
            "Patient ID": [" p1 ", "P1", "P2", None],
            "Admission Date": ["2025-01-03", "2025-01-01", "2025-01-02", "2025-01-04"],
            "Lactate mmol/L": [-0.5, 1.0, 2.0, 1.0],
            "Sepsis Flag": ["y", "no", "unknown", "yes"],
            "Ward": [" icu ", "ER", None, "ward-x"],
        }
    ).to_csv(source, index=False)

    cleaned, report = clean_dataset(source, output)

    assert output.is_file()
    assert cleaned["patient_id"].tolist() == ["P2", "P1"]
    assert pd.isna(cleaned["sepsis_flag"].iloc[0])
    assert cleaned["sepsis_flag"].iloc[1] == "Yes"
    assert pd.isna(cleaned.loc[cleaned["patient_id"] == "P1", "lactate_mmol_l"].iloc[0])
    assert report["raw_rows"] == 4
    assert report["duplicates_removed"] == 1
    assert report["rows_missing_required_fields_removed"] == 1
    assert report["invalid_numeric_measurements"] == 1


def test_analysis_outputs_handle_missing_sepsis_status(tmp_path):
    cleaned_path = tmp_path / "clean.csv"
    output_dir = tmp_path / "outputs"
    findings_path = tmp_path / "docs" / "findings.md"
    pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3"],
            "admission_date": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"]),
            "temperature_c": [37.0, 38.0, None],
            "sepsis_flag": ["No", "No", None],
            "ward": ["ER", "ICU", "ICU"],
        }
    ).to_csv(cleaned_path, index=False)

    summary = analyze_dataset(cleaned_path, output_dir, findings_path)

    assert summary["total_patients"] == 3
    assert summary["sepsis_positive"] == 0
    assert summary["sepsis_negative"] == 2
    assert summary["sepsis_unknown"] == 1
    assert summary["sepsis_rate_percent"] == 0
    assert (output_dir / "clinical_metrics_summary.csv").is_file()
    assert (output_dir / "clinical_metrics_by_sepsis.csv").is_file()
    assert (output_dir / "ward_summary.csv").is_file()
    assert findings_path.is_file()
    assert "do not establish causes" in findings_path.read_text(encoding="utf-8")


def test_analysis_rejects_empty_dataset(tmp_path):
    cleaned_path = tmp_path / "empty.csv"
    pd.DataFrame(columns=["patient_id", "admission_date"]).to_csv(cleaned_path, index=False)

    with pytest.raises(ValueError, match="contains no patient records"):
        analyze_dataset(cleaned_path, tmp_path / "outputs", tmp_path / "findings.md")


def test_real_source_pipeline_produces_valid_cleaned_dataset(tmp_path):
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]
    source = project_root / "Sepsis_Dataset ....xlsx"
    if not source.is_file():
        pytest.skip("Repository source workbook is not available.")

    cleaned_path = tmp_path / "processed" / "cleaned.csv"
    cleaned, report = clean_dataset(source, cleaned_path)

    assert len(cleaned) > 0
    assert cleaned["patient_id"].is_unique
    assert cleaned["admission_date"].notna().all()
    assert cleaned["lactate_mmol_l"].dropna().between(0, 10).all()
    assert report["invalid_numeric_measurements"] > 0

    summary = analyze_dataset(
        cleaned_path,
        output_dir=tmp_path / "processed",
        findings_path=tmp_path / "docs" / "findings.md",
        cleaning_report=report,
    )
    assert summary["total_patients"] == len(cleaned)
