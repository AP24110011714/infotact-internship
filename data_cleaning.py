#!/usr/bin/env python3
"""Clean and standardize the patient-level Infotact sepsis dataset."""

import argparse
import re
from pathlib import Path

import pandas as pd


VALID_RANGES = {
    "temperature_c": (30.0, 45.0),
    "bp_systolic": (50.0, 200.0),
    "bp_diastolic": (30.0, 130.0),
    "heart_rate": (20.0, 220.0),
    "wbc_count": (0.0, 40.0),
    "lactate_mmol_l": (0.0, 10.0),
}

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = PROJECT_ROOT / "Sepsis_Dataset_5000.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "Sepsis_Dataset_cleaned.csv"


def normalize_column_name(name: object) -> str:
    text = str(name).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def load_dataset(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xls", ".xlsx"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported file type: {path.suffix}")


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [normalize_column_name(c) for c in df.columns]
    return df


def map_expected_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "patient_id": ["patient_id", "patient", "case_id", "case", "pid"],
        "admission_date": ["admission_date", "date", "admission", "visit_date"],
        "temperature_c": ["temperature_c", "temp_c", "temperature", "temp"],
        "bp_systolic": ["bp_systolic", "systolic_bp", "sys_bp", "bp_sys"],
        "bp_diastolic": ["bp_diastolic", "diastolic_bp", "dia_bp", "bp_dia"],
        "heart_rate": ["heart_rate", "hr", "pulse_rate"],
        "wbc_count": ["wbc_count", "wbc", "white_blood_cell_count"],
        "lactate_mmol_l": ["lactate_mmol_l", "lactate", "lactic_acid"],
        "sepsis_flag": ["sepsis_flag", "sepsis", "flag_sepsis"],
        "ward": ["ward", "department", "unit"],
        "doctor_on_duty": ["doctor_on_duty", "doctor", "attending_doctor"],
    }

    renamed = {}
    cols = {normalize_column_name(c): c for c in df.columns}
    for target, candidates in mapping.items():
        for candidate in candidates:
            key = normalize_column_name(candidate)
            if key in cols:
                renamed[cols[key]] = target
                break
    return df.rename(columns=renamed)


def clean_patient_id(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.upper().replace(
        {"": pd.NA, "NAN": pd.NA, "NONE": pd.NA, "NULL": pd.NA}
    )


def clean_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def normalize_flag(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.lower()
    mapping = {
        "yes": "Yes",
        "y": "Yes",
        "true": "Yes",
        "1": "Yes",
        "no": "No",
        "n": "No",
        "false": "No",
        "0": "No",
        "nan": pd.NA,
        "none": pd.NA,
        "null": pd.NA,
        "": pd.NA,
    }
    return s.map(mapping)


def clean_text(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "none": pd.NA, "null": pd.NA})
    )


def validate_numeric_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    cleaned = df.copy()
    invalid_by_column = {}
    for column, (low, high) in VALID_RANGES.items():
        if column in cleaned.columns:
            original = cleaned[column]
            values = pd.to_numeric(original, errors="coerce")
            invalid = original.notna() & (values.isna() | ~values.between(low, high))
            invalid_by_column[column] = int(invalid.sum())
            cleaned[column] = values.mask(invalid)
    return cleaned, invalid_by_column


def clean_dataset(
    raw_path: str | Path, output_path: str | Path
) -> tuple[pd.DataFrame, dict[str, object]]:
    raw_df = load_dataset(raw_path)
    raw_rows = len(raw_df)
    df = raw_df
    df = standardize_columns(df)
    df = map_expected_columns(df)

    required_columns = ["patient_id", "admission_date"]
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["patient_id"] = clean_patient_id(df["patient_id"])
    df["admission_date"] = clean_date(df["admission_date"])

    invalid_required = df["patient_id"].isna() | df["admission_date"].isna()
    required_rows_removed = int(invalid_required.sum())
    df = df.loc[~invalid_required].copy()

    for col in ["ward", "doctor_on_duty"]:
        if col in df.columns:
            df[col] = clean_text(df[col]).fillna("Unknown")

    if "sepsis_flag" in df.columns:
        df["sepsis_flag"] = normalize_flag(df["sepsis_flag"])

    before_dup = len(df)
    df = df.drop_duplicates(subset=["patient_id"], keep="first").copy()
    dup_removed = before_dup - len(df)

    df, invalid_numeric_by_column = validate_numeric_columns(df)

    df = df.sort_values(["admission_date", "patient_id"]).reset_index(drop=True)

    preferred_order = [
        "patient_id",
        "admission_date",
        "temperature_c",
        "bp_systolic",
        "bp_diastolic",
        "heart_rate",
        "wbc_count",
        "lactate_mmol_l",
        "sepsis_flag",
        "ward",
        "doctor_on_duty",
    ]
    final_columns = [c for c in preferred_order if c in df.columns] + [
        c for c in df.columns if c not in preferred_order
    ]
    df = df[final_columns]

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)

    report = {
        "raw_rows": raw_rows,
        "final_rows": len(df),
        "rows_missing_required_fields_removed": required_rows_removed,
        "duplicates_removed": dup_removed,
        "invalid_numeric_measurements_by_column": invalid_numeric_by_column,
        "invalid_numeric_measurements": sum(invalid_numeric_by_column.values()),
        "unique_patients": int(df["patient_id"].nunique()),
        "earliest_admission": str(df["admission_date"].min()) if "admission_date" in df.columns and not df.empty else "N/A",
        "latest_admission": str(df["admission_date"].max()) if "admission_date" in df.columns and not df.empty else "N/A",
    }

    return df, report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.input.is_file():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    _, report = clean_dataset(args.input, args.output)
    print("Generated cleaned dataset:", args.output)
    print(report)
