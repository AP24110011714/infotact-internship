#!/usr/bin/env python3
"""
CareFlow EHR Event Log Generator
=================================
Generates realistic mock hospital ER event logs with deliberate operational
inefficiencies coded in, matching the CareFlow project specification:

  Patient A: Triage 10:00 -> X-Ray 10:15 -> Triage 10:30 (loopback!)

Key inefficiencies deliberately embedded:
  - 40% of X-Ray patients loop back to Triage (missing paperwork form)
  - Doctor Consultation bottleneck: avg 48-min wait
  - Lab Tests bottleneck: avg 35-min wait
  - 8% rework: patients revisit Doctor Consultation after Lab/X-Ray
  - 5% non-conformance: steps performed out of ideal order

Output columns (PM4Py standard format):
  case_id, activity, timestamp, resource, department, age_group, severity

Usage:
  python generate_event_log.py               # 5000 cases -> data/raw/ehr_events.csv
  python generate_event_log.py --cases 7000  # custom case count
  python generate_event_log.py --seed 99     # reproducible seed
"""

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_CASES = 5000
DEFAULT_SEED  = 42
PROJECT_ROOT  = Path(__file__).resolve().parent
DEFAULT_OUT   = PROJECT_ROOT / "data" / "raw" / "ehr_events.csv"

# Hospital activities (ER workflow)
ACTIVITIES = [
    "Registration",
    "Triage",
    "X-Ray",
    "Lab Tests",
    "Doctor Consultation",
    "Doctor Review",       # second doc review when labs come back
    "Treatment",
    "Discharge",
]

# Ideal / mandated pathway (for conformance checking)
IDEAL_PATH = [
    "Registration",
    "Triage",
    "Doctor Consultation",
    "Treatment",
    "Discharge",
]

# Resources (staff) per activity
RESOURCES = {
    "Registration":        ["Receptionist_01", "Receptionist_02", "Receptionist_03"],
    "Triage":              ["Nurse_01", "Nurse_02", "Nurse_03", "Nurse_04"],
    "X-Ray":               ["Radiologist_01", "Technician_01", "Technician_02"],
    "Lab Tests":           ["Lab_Tech_01", "Lab_Tech_02", "Lab_Tech_03"],
    "Doctor Consultation": ["Dr_A", "Dr_B", "Dr_C", "Dr_D"],
    "Doctor Review":       ["Dr_A", "Dr_B", "Dr_C", "Dr_D"],
    "Treatment":           ["Nurse_01", "Nurse_02", "Nurse_03", "Dr_A", "Dr_B"],
    "Discharge":           ["Receptionist_01", "Receptionist_02", "Nurse_04"],
}

DEPARTMENTS = {
    "Registration": "Reception",
    "Triage":       "Triage Bay",
    "X-Ray":        "Radiology",
    "Lab Tests":    "Laboratory",
    "Doctor Consultation": "OPD",
    "Doctor Review":       "OPD",
    "Treatment":    "Treatment Room",
    "Discharge":    "Reception",
}

# Activity durations: (mean_minutes, std_minutes)
# These include service time — the WAIT time is added separately at bottlenecks
DURATIONS = {
    "Registration":        (8,  3),
    "Triage":              (12, 4),
    "X-Ray":               (20, 6),
    "Lab Tests":           (25, 8),
    "Doctor Consultation": (22, 7),
    "Doctor Review":       (18, 5),
    "Treatment":           (35, 12),
    "Discharge":           (10, 3),
}

# WAIT times BEFORE each activity (bottleneck simulation)
WAITS = {
    "Registration":        (5,  3),    # short
    "Triage":              (10, 5),    # moderate
    "X-Ray":               (18, 8),    # moderate
    "Lab Tests":           (35, 12),   # BOTTLENECK — lab queue
    "Doctor Consultation": (48, 20),   # BIGGEST BOTTLENECK
    "Doctor Review":       (25, 10),   # wait for review
    "Treatment":           (15, 7),    # moderate
    "Discharge":           (8,  4),    # short
}

AGE_GROUPS  = ["0-18", "19-35", "36-55", "56-70", "70+"]
SEVERITIES  = ["Low", "Medium", "High", "Critical"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rng_min(mean: float, std: float, rng: random.Random, min_val: float = 1.0) -> float:
    return max(min_val, rng.gauss(mean, std))


def _pick(lst: list, rng: random.Random):
    return rng.choice(lst)


def _random_start(rng: random.Random) -> datetime:
    """Random ER arrival over a 2-year operating window, skewed to daytime."""
    base = datetime(2024, 1, 1, 0, 0, 0)
    day_offset = rng.randint(0, 730)
    # skew to daytime: 06:00-22:00 (ER peak hours)
    hour = int(rng.triangular(6, 22, 14))
    minute = rng.randint(0, 59)
    return base + timedelta(days=day_offset, hours=hour, minutes=minute)


# ---------------------------------------------------------------------------
# Case builder
# ---------------------------------------------------------------------------

def _build_case(case_num: int, rng: random.Random) -> list[dict]:
    """Return a list of events for one patient case."""

    case_id    = f"ER{case_num:05d}"
    age_group  = _pick(AGE_GROUPS, rng)
    severity   = rng.choices(SEVERITIES, weights=[30, 45, 18, 7])[0]

    # Decide pathway flags upfront
    needs_xray   = rng.random() < 0.60   # 60% get X-Ray
    needs_lab    = rng.random() < 0.70   # 70% get Lab Tests
    # 40% of X-Ray patients loop back to Triage (the key inefficiency)
    xray_loopback = needs_xray and rng.random() < 0.40
    # 8% get a second Doctor Consultation after labs
    double_doc   = needs_lab and rng.random() < 0.08

    # Build ordered activity sequence
    sequence = ["Registration", "Triage"]
    if needs_xray:
        sequence.append("X-Ray")
        if xray_loopback:
            sequence.append("Triage")   # LOOPBACK — missing paperwork
    if needs_lab:
        sequence.append("Lab Tests")
    sequence.append("Doctor Consultation")
    if double_doc:
        sequence.append("Doctor Review")
    sequence.extend(["Treatment", "Discharge"])

    # Build timestamps
    ts = _random_start(rng)
    events = []
    for activity in sequence:
        # Wait before activity (bottleneck)
        wait_mean, wait_std = WAITS[activity]
        # Critical patients get shorter waits
        wait_factor = 0.4 if severity == "Critical" else (0.7 if severity == "High" else 1.0)
        wait_min = _rng_min(wait_mean * wait_factor, wait_std * wait_factor, rng, 0.5)
        ts += timedelta(minutes=wait_min)

        dur_mean, dur_std = DURATIONS[activity]
        duration_min = _rng_min(dur_mean, dur_std, rng, 2.0)

        events.append({
            "case_id":    case_id,
            "activity":   activity,
            "timestamp":  ts.strftime("%Y-%m-%d %H:%M:%S"),
            "resource":   _pick(RESOURCES[activity], rng),
            "department": DEPARTMENTS[activity],
            "age_group":  age_group,
            "severity":   severity,
            "duration_min": round(duration_min, 1),
        })

        ts += timedelta(minutes=duration_min)

    return events


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def generate_event_log(
    n_cases:  int  = DEFAULT_CASES,
    seed:     int  = DEFAULT_SEED,
    out_path: Path = DEFAULT_OUT,
) -> pd.DataFrame:

    rng = random.Random(seed)
    all_events: list[dict] = []

    for i in range(1, n_cases + 1):
        all_events.extend(_build_case(i, rng))

    df = pd.DataFrame(all_events)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["case_id", "timestamp"]).reset_index(drop=True)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    # ── summary ──────────────────────────────────────────────────────────
    total_events = len(df)
    total_cases  = df["case_id"].nunique()
    xray_cases   = df[df["activity"] == "X-Ray"]["case_id"].nunique()
    # Loopback: cases that have Triage appearing MORE than once
    triage_counts = df[df["activity"] == "Triage"].groupby("case_id").size()
    loopback_cases = int((triage_counts > 1).sum())
    lab_cases      = df[df["activity"] == "Lab Tests"]["case_id"].nunique()
    double_doc_cases = df[df["activity"] == "Doctor Review"]["case_id"].nunique()

    wait_doc = df[df["activity"] == "Doctor Consultation"]["duration_min"]

    print(f"\n✅  EHR Event Log Generated → {out_path}")
    print(f"    Cases      : {total_cases:,}")
    print(f"    Events     : {total_events:,}")
    print(f"    Avg events/case : {total_events/total_cases:.1f}")
    print(f"    Date range : {df['timestamp'].min().date()} → {df['timestamp'].max().date()}")
    print(f"\n  Operational Inefficiencies Embedded:")
    print(f"    X-Ray cases             : {xray_cases:,}  ({xray_cases/total_cases*100:.1f}%)")
    print(f"    Triage loopbacks (X-Ray → Triage) : {loopback_cases:,}  "
          f"({loopback_cases/xray_cases*100:.1f}% of X-Ray cases) ← KEY BOTTLENECK")
    print(f"    Lab Test cases          : {lab_cases:,}  ({lab_cases/total_cases*100:.1f}%)")
    print(f"    Double-Doc cases        : {double_doc_cases:,}  ({double_doc_cases/total_cases*100:.1f}%)")
    print(f"    Avg Doctor wait (min)   : {wait_doc.mean():.1f} ± {wait_doc.std():.1f}")

    return df


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases",  type=int,  default=DEFAULT_CASES,
                        help=f"Number of patient cases (default {DEFAULT_CASES})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT,
                        help=f"Output CSV path (default {DEFAULT_OUT})")
    parser.add_argument("--seed",   type=int,  default=DEFAULT_SEED,
                        help=f"Random seed (default {DEFAULT_SEED})")
    args = parser.parse_args()
    generate_event_log(n_cases=args.cases, seed=args.seed, out_path=args.output)
