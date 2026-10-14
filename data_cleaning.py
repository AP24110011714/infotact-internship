#!/usr/bin/env python3
"""
Clean and standardize the Infotact sepsis dataset.

This script reads the raw Excel file in the repository and creates a cleaned CSV.
It removes duplicate patient IDs, standardizes column names, parses dates,
validates numeric clinical fields, and writes a cleaned dataset ready for analysis.

Usage:
    python data_cleaning.py "Sepsis_Dataset ....xlsx" "Sepsis_Dataset_cleaned.csv"
"""

import os
import sys
import re
from pathlib import Path

import pandas as pd


VALID_RANGES = {
    "Temperature_C": (30.0, 45.0),
    "BP_Systolic": (50.0, 200.0),
    "BP_Diastolic": (30.0, 130.0),
    "Heart_Rate": (20.0, 220.0),
    "WBC_Count": (0.0, 40.0),
    "Lactate_mmol_L": (0.0, 10.0),
}


def normalize_column_name(name):
    text = str(name).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def load_dataset(path):
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xls", ".xlsx"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported file type: {path.suffix}")


def standardize_columns(df):
    df = df.copy()
    df.columns = [normalize_column_name(c) for c in df.columns]
    return df


def map_expected_columns(df):
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


def clean_patient_id(series):
    s = series.astype(str).str.strip().str.upper()
    s = s.replace({"NAN": pd.NA, "NONE": pd.NA, "NULL": pd.NA})
    s = s.replace(r"^\s*$", pd.NA, regex=True)
    return s


def clean_date(series):
    return pd.to_datetime(series, errors="coerce")


def normalize_flag(series):
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
    }
    return s.map(mapping).fillna(s.str.title())


def clean_text(series):
    s = series.astype(str).str.strip()
    s = s.replace({"nan": pd.NA, "none": pd.NA, "null": pd.NA})
    s = s.replace(r"^\s*$", pd.NA, regex=True)
    return s


def validate_numeric_columns(df):
    cleaned = df.copy()
    for column, (low, high) in VALID_RANGES.items():
        if column in cleaned.columns:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
            cleaned = cleaned[cleaned[column].between(low, high) | cleaned[column].isna()].copy()
    return cleaned


def clean_dataset(raw_path: str, output_path: str):
    df = load_dataset(raw_path)
    df = standardize_columns(df)
    df = map_expected_columns(df)

    required_columns = ["patient_id", "admission_date"]
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["patient_id"] = clean_patient_id(df["patient_id"])
    df["admission_date"] = clean_date(df["admission_date"])

    # Remove rows with missing patient ID or admission date.
    df = df[df["patient_id"].notna()].copy()
    df = df[df["admission_date"].notna()].copy()

    for col in ["ward", "doctor_on_duty"]:
        if col in df.columns:
            df[col] = clean_text(df[col]).fillna("Unknown")
            df[col] = df[col].str.title()

    if "sepsis_flag" in df.columns:
        df["sepsis_flag"] = normalize_flag(df["sepsis_flag"])

    # Remove duplicates based on patient ID.
    before_dup = len(df)
    df = df.drop_duplicates(subset=["patient_id"], keep="first").copy()
    dup_removed = before_dup - len(df)

    # Validate numeric fields and drop clinically invalid values.
    before_num = len(df)
    df = validate_numeric_columns(df)
    num_removed = before_num - len(df)

    # Sort final dataset for readability.
    df = df.sort_values(["admission_date", "patient_id"]).reset_index(drop=True)

    # Standardize output column order.
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
    final_columns = [c for c in preferred_order if c in df.columns] + [c for c in df.columns if c not in preferred_order]
    df = df[final_columns]

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)

    report = {
        "raw_rows": before_dup + num_removed,
        "final_rows": len(df),
        "duplicates_removed": dup_removed,
        "invalid_numeric_rows_removed": num_removed,
        "unique_patients": int(df["patient_id"].nunique()),
        "earliest_admission": str(df["admission_date"].min()) if "admission_date" in df.columns and not df.empty else "N/A",
        "latest_admission": str(df["admission_date"].max()) if "admission_date" in df.columns and not df.empty else "N/A",
    }

    return df, report


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python data_cleaning.py <raw_dataset.xlsx|csv> <cleaned_output.csv>")
        sys.exit(1)

    raw_path = sys.argv[1]
    output_path = sys.argv[2]

    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Input file not found: {raw_path}")

    df, report = clean_dataset(raw_path, output_path)
    print("Generated cleaned dataset:", output_path)
    print(report)
