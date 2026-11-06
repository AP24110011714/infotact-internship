import pandas as pd
import pytest
from pathlib import Path

from clinical_analysis import analyze_dataset
from data_cleaning import clean_dataset, normalize_flag, validate_numeric_columns
from dbt_transform.clean_event_log import transform_event_log
from mining.bottlenecks import calculate_bottlenecks
from mining.conformance import check_conformance
from mining.variants import analyze_variants

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
    assert len(cleaned) == 2
    assert set(cleaned["patient_id"].tolist()) == {"P1", "P2"}
    assert set(cleaned["ward"].tolist()) == {"icu", "Unknown"}
    assert report["raw_rows"] == 4
    assert report["invalid_numeric_measurements"] == 1
    assert report["duplicates_removed"] == 1


def test_analyze_dataset_rejects_empty_dataset(tmp_path):
    cleaned_path = tmp_path / "processed" / "empty.csv"
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=["patient_id", "admission_date"]).to_csv(cleaned_path, index=False)

    with pytest.raises(ValueError, match="contains no patient records"):
        analyze_dataset(cleaned_path, tmp_path / "outputs", tmp_path / "findings.md")


def test_real_source_pipeline_produces_valid_cleaned_dataset(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    source = project_root / "Sepsis_Dataset ....xlsx"
    if not source.is_file():
        pytest.skip("Repository source workbook is not available.")

    cleaned_path = tmp_path / "processed" / "cleaned.csv"
    cleaned, report = clean_dataset(source, cleaned_path)

    assert len(cleaned) > 0
    assert cleaned["patient_id"].is_unique
    assert cleaned["admission_date"].notna().all()


# ==============================================================================
# CareFlow Process Mining Tests (Infotact Specification Verification)
# ==============================================================================

def test_dbt_event_log_transformation(tmp_path):
    raw_path = tmp_path / "raw.csv"
    clean_path = tmp_path / "clean.csv"
    
    pd.DataFrame({
        "case_id": ["C1", "C1", "C2"],
        "activity": [" Registration ", "Triage", "Registration"],
        "timestamp": ["2025-01-01 10:00:00", "2025-01-01 10:15:00", "2025-01-01 11:00:00"],
        "resource": ["Staff A", "Nurse B", "Staff A"],
        "department": ["ER", "ER", "ER"],
        "age_group": ["Adult", "Adult", "Senior"],
        "severity": ["Urgent", "Urgent", "Normal"]
    }).to_csv(raw_path, index=False)
    
    df_clean = transform_event_log(str(raw_path), str(clean_path))
    assert len(df_clean) == 3
    assert "event_seq" in df_clean.columns
    assert df_clean["activity"].tolist() == ["Registration", "Triage", "Registration"]


def test_bottleneck_calculations(tmp_path):
    clean_path = tmp_path / "clean.csv"
    out_path = tmp_path / "bottlenecks.csv"
    
    pd.DataFrame({
        "case_id": ["C1", "C1", "C2", "C2"],
        "activity": ["Registration", "Triage", "Registration", "Triage"],
        "timestamp": [
            "2025-01-01 10:00:00", "2025-01-01 10:20:00",
            "2025-01-01 11:00:00", "2025-01-01 11:40:00"
        ]
    }).to_csv(clean_path, index=False)
    
    df_b = calculate_bottlenecks(str(clean_path), str(out_path))
    assert len(df_b) == 1
    assert df_b.iloc[0]["source"] == "Registration"
    assert df_b.iloc[0]["target"] == "Triage"
    assert df_b.iloc[0]["mean_wait_min"] == 30.0  # (20 + 40) / 2


def test_process_mining_production_artifacts():
    project_root = Path(__file__).resolve().parents[1]
    proc_dir = project_root / "data" / "processed"
    
    # 1. Event log clean
    assert (proc_dir / "ehr_events_clean.csv").is_file()
    df_events = pd.read_csv(proc_dir / "ehr_events_clean.csv")
    assert len(df_events) >= 5000
    assert "case_id" in df_events.columns
    assert "activity" in df_events.columns
    assert "timestamp" in df_events.columns

    # 2. DFG edges & loopbacks
    assert (proc_dir / "dfg_edges.csv").is_file()
    df_edges = pd.read_csv(proc_dir / "dfg_edges.csv")
    loopback_row = df_edges[(df_edges["source"] == "X-Ray") & (df_edges["target"] == "Triage")]
    assert len(loopback_row) == 1
    assert loopback_row.iloc[0]["count"] > 1000  # verified ~1217 loopbacks (~40% of X-Ray)

    # 3. Variants & Conformance
    assert (proc_dir / "variants.csv").is_file()
    assert (proc_dir / "conformance.csv").is_file()
    df_conf = pd.read_csv(proc_dir / "conformance.csv")
    assert len(df_conf) == 5000
    assert df_conf["fitness_score"].mean() > 0.85
