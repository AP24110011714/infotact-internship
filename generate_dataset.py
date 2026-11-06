#!/usr/bin/env python3
"""
CareFlow Synthetic Patient Dataset Generator
=============================================
Generates a realistic 5,000-patient sepsis dataset matching the exact schema
expected by the CareFlow data-cleaning pipeline:

    patient_id, admission_date, temperature_c, bp_systolic, bp_diastolic,
    heart_rate, wbc_count, lactate_mmol_l, sepsis_flag, ward, doctor_on_duty

Sepsis prevalence is set to ~18% (clinically realistic ICU rate).
Clinical values follow ward-stratified normal distributions with
realistic correlations (e.g. sepsis patients have higher temperature,
heart rate, WBC, and lactate).

Usage
-----
    python generate_dataset.py                          # writes default CSV
    python generate_dataset.py --rows 7500             # custom row count
    python generate_dataset.py --output myfile.csv     # custom output path
    python generate_dataset.py --seed 99               # reproducible seed
"""

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_ROWS = 5000
DEFAULT_SEED = 42
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "Sepsis_Dataset_5000.csv"

WARDS = ["ICU-A", "ICU-B", "Ward-X", "ER", "HDU", "Surgical-ICU"]

# Ward-level sepsis probability (ICUs and ER are higher risk)
WARD_SEPSIS_PROB = {
    "ICU-A":        0.35,
    "ICU-B":        0.32,
    "HDU":          0.20,
    "Surgical-ICU": 0.25,
    "ER":           0.12,
    "Ward-X":       0.07,
}

DOCTORS = [
    "Dr. Sharma", "Dr. Patel", "Dr. Mehta", "Dr. Reddy",
    "Dr. Kapoor", "Dr. Nair", "Dr. Joshi", "Dr. Verma",
    "Dr. Singh", "Dr. Gupta", "Dr. Iyer", "Dr. Das",
]

# Ward -> list of doctors who work there (each ward has 3–4 assigned docs)
WARD_DOCTORS = {
    "ICU-A":        ["Dr. Sharma", "Dr. Mehta", "Dr. Nair"],
    "ICU-B":        ["Dr. Patel", "Dr. Kapoor", "Dr. Reddy"],
    "HDU":          ["Dr. Joshi", "Dr. Verma", "Dr. Iyer"],
    "Surgical-ICU": ["Dr. Singh", "Dr. Gupta", "Dr. Das"],
    "ER":           ["Dr. Sharma", "Dr. Patel", "Dr. Singh", "Dr. Verma"],
    "Ward-X":       ["Dr. Reddy", "Dr. Nair", "Dr. Joshi", "Dr. Kapoor"],
}

# Clinical value distributions: (mean, std) for (normal, sepsis) groups
# Source: representative values from published sepsis literature
CLINICAL_PARAMS = {
    #            normal-mean  normal-std  sepsis-mean  sepsis-std
    "temperature_c":    (37.0,  0.4,  38.6,  0.6),
    "bp_systolic":      (118.0, 12.0, 100.0, 15.0),
    "bp_diastolic":     (75.0,   8.0,  62.0, 10.0),
    "heart_rate":       (78.0,  12.0, 112.0, 20.0),
    "wbc_count":        (7.5,   2.0,  15.0,  5.0),
    "lactate_mmol_l":   (1.2,   0.4,   3.8,  1.2),
}

# Fraction of records with deliberately out-of-range (invalid) values
# to test the cleaning pipeline
OUT_OF_RANGE_FRACTION = 0.012   # ~1.2 % of cells per column


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _clinical_value(
    col: str,
    is_sepsis: bool,
    rng: np.random.Generator,
    inject_invalid: bool,
) -> float | None:
    mu_n, sd_n, mu_s, sd_s = CLINICAL_PARAMS[col]
    if is_sepsis:
        value = rng.normal(mu_s, sd_s)
    else:
        value = rng.normal(mu_n, sd_n)

    # Hard valid ranges (same as VALID_RANGES in data_cleaning.py)
    valid = {
        "temperature_c":  (30.0, 45.0),
        "bp_systolic":    (50.0, 200.0),
        "bp_diastolic":   (30.0, 130.0),
        "heart_rate":     (20.0, 220.0),
        "wbc_count":      (0.0,  40.0),
        "lactate_mmol_l": (0.0,  10.0),
    }
    lo, hi = valid[col]

    if inject_invalid:
        # Inject a value outside the valid range
        return float(rng.choice([-5.0, hi + rng.uniform(10, 50)]))

    return round(_clamp(value, lo, hi), 2)


def _random_date(start: date, end: date, rng: random.Random) -> date:
    delta = (end - start).days
    return start + timedelta(days=rng.randint(0, delta))


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def generate_dataset(
    n_rows: int = DEFAULT_ROWS,
    seed: int = DEFAULT_SEED,
    output_path: Path = DEFAULT_OUTPUT,
) -> pd.DataFrame:
    """Generate a synthetic patient-level sepsis dataset and save it as CSV."""

    rng_np = np.random.default_rng(seed)
    rng_py = random.Random(seed)

    start_date = date(2022, 1, 1)
    end_date   = date(2025, 10, 31)

    rows = []
    for i in range(1, n_rows + 1):
        patient_id = f"PT{i:05d}"

        ward = rng_py.choices(
            list(WARD_SEPSIS_PROB.keys()),
            weights=[67, 60, 45, 50, 110, 170],   # rough proportion of beds
            k=1,
        )[0]

        is_sepsis = rng_np.random() < WARD_SEPSIS_PROB[ward]
        sepsis_flag = "Yes" if is_sepsis else "No"

        admission_date = _random_date(start_date, end_date, rng_py)

        doctor = rng_py.choice(WARD_DOCTORS[ward])

        # Decide which columns get an injected invalid value this row
        invalid_cols = {
            col
            for col in CLINICAL_PARAMS
            if rng_np.random() < OUT_OF_RANGE_FRACTION
        }

        row = {
            "patient_id":      patient_id,
            "admission_date":  admission_date.isoformat(),
            "temperature_c":   _clinical_value("temperature_c",   is_sepsis, rng_np, "temperature_c"   in invalid_cols),
            "bp_systolic":     _clinical_value("bp_systolic",     is_sepsis, rng_np, "bp_systolic"     in invalid_cols),
            "bp_diastolic":    _clinical_value("bp_diastolic",    is_sepsis, rng_np, "bp_diastolic"    in invalid_cols),
            "heart_rate":      _clinical_value("heart_rate",      is_sepsis, rng_np, "heart_rate"      in invalid_cols),
            "wbc_count":       _clinical_value("wbc_count",       is_sepsis, rng_np, "wbc_count"       in invalid_cols),
            "lactate_mmol_l":  _clinical_value("lactate_mmol_l",  is_sepsis, rng_np, "lactate_mmol_l"  in invalid_cols),
            "sepsis_flag":     sepsis_flag,
            "ward":            ward,
            "doctor_on_duty":  doctor,
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Randomly blank out ~2% of wbc_count and lactate (simulates missing lab values)
    for col in ["wbc_count", "lactate_mmol_l"]:
        mask = rng_np.random(len(df)) < 0.02
        df.loc[mask, col] = None

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    # Print a quick summary
    total      = len(df)
    n_sepsis   = int((df["sepsis_flag"] == "Yes").sum())
    n_no       = int((df["sepsis_flag"] == "No").sum())
    print(f"\n✅  Generated {total:,} patient records → {output_path}")
    print(f"    Sepsis-positive : {n_sepsis:,}  ({n_sepsis/total*100:.1f}%)")
    print(f"    Sepsis-negative : {n_no:,}  ({n_no/total*100:.1f}%)")
    print(f"    Date range      : {df['admission_date'].min()} → {df['admission_date'].max()}")
    print(f"    Wards           : {df['ward'].nunique()}")
    print(f"    Doctors         : {df['doctor_on_duty'].nunique()}")
    ward_counts = df["ward"].value_counts().to_dict()
    for ward, count in ward_counts.items():
        sep = int((df[df["ward"] == ward]["sepsis_flag"] == "Yes").sum())
        print(f"      {ward:<16}: {count:>5} patients  ({sep} sepsis-positive)")
    return df


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rows", type=int, default=DEFAULT_ROWS,
        help=f"Number of patient records to generate (default: {DEFAULT_ROWS})",
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help=f"Random seed for reproducibility (default: {DEFAULT_SEED})",
    )
    args = parser.parse_args()
    generate_dataset(n_rows=args.rows, seed=args.seed, output_path=args.output)
