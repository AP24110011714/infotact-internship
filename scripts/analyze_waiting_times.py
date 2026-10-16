from pathlib import Path

import pandas as pd


# --------------------------------------------------
# STEP 1: DEFINE PROJECT PATHS
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "hospital_event_log_clean.csv"
)

OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TRANSITIONS_FILE = OUTPUT_DIR / "activity_transitions.csv"
WAITING_TIMES_FILE = OUTPUT_DIR / "waiting_time_summary.csv"


# --------------------------------------------------
# STEP 2: LOAD THE CLEANED EVENT LOG
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="raise"
)

df = df.sort_values(
    ["case_id", "timestamp"]
).reset_index(drop=True)

print("=" * 60)
print("CAREFLOW - HOSPITAL PROCESS ANALYSIS")
print("=" * 60)

print("\nEvent records:", len(df))
print("Patient visits:", df["case_id"].nunique())


# --------------------------------------------------
# STEP 3: CALCULATE TIME BETWEEN EVENTS
# --------------------------------------------------

df["next_activity"] = (
    df.groupby("case_id")["activity"].shift(-1)
)

df["next_timestamp"] = (
    df.groupby("case_id")["timestamp"].shift(-1)
)

df["waiting_time_minutes"] = (
    df["next_timestamp"] - df["timestamp"]
).dt.total_seconds() / 60

transitions = df.dropna(
    subset=["next_activity", "waiting_time_minutes"]
).copy()

transitions = transitions.rename(
    columns={"activity": "current_activity"}
)

transitions["transition"] = (
    transitions["current_activity"]
    + " -> "
    + transitions["next_activity"]
)


# --------------------------------------------------
# STEP 4: SUMMARIZE ACTIVITY TRANSITIONS
# --------------------------------------------------

transition_summary = (
    transitions.groupby(
        ["current_activity", "next_activity", "transition"],
        as_index=False
    )
    .agg(
        case_count=("case_id", "count"),
        average_waiting_minutes=("waiting_time_minutes", "mean"),
        median_waiting_minutes=("waiting_time_minutes", "median"),
        maximum_waiting_minutes=("waiting_time_minutes", "max")
    )
    .sort_values(
        "average_waiting_minutes",
        ascending=False
    )
)

transition_summary.to_csv(
    TRANSITIONS_FILE,
    index=False
)


# --------------------------------------------------
# STEP 5: SUMMARIZE WAITING TIMES
# --------------------------------------------------

waiting_summary = (
    transitions.groupby(
        "current_activity",
        as_index=False
    )
    .agg(
        event_count=("case_id", "count"),
        average_waiting_minutes=("waiting_time_minutes", "mean"),
        median_waiting_minutes=("waiting_time_minutes", "median"),
        maximum_waiting_minutes=("waiting_time_minutes", "max")
    )
    .sort_values(
        "average_waiting_minutes",
        ascending=False
    )
)

waiting_summary.to_csv(
    WAITING_TIMES_FILE,
    index=False
)


# --------------------------------------------------
# STEP 6: ANALYZE X-RAY TO TRIAGE LOOP-BACKS
# --------------------------------------------------

xray_cases = set(
    df.loc[df["activity"] == "X-Ray", "case_id"]
)

triage_after_xray = transitions[
    (transitions["current_activity"] == "X-Ray")
    & (transitions["next_activity"] == "Triage")
]

loopback_cases = set(triage_after_xray["case_id"])

loopback_percentage = (
    len(loopback_cases) / len(xray_cases) * 100
    if xray_cases
    else 0
)


# --------------------------------------------------
# STEP 7: DISPLAY RESULTS
# --------------------------------------------------

print("\nTOP 10 TRANSITIONS BY AVERAGE WAITING TIME")
print("-" * 60)

print(
    transition_summary.head(10).to_string(index=False)
)

print("\nWAITING TIME SUMMARY BY ACTIVITY")
print("-" * 60)

print(
    waiting_summary.to_string(index=False)
)

print("\nX-RAY TO TRIAGE ANALYSIS")
print("-" * 60)

print("Patient visits containing X-Ray:", len(xray_cases))
print("X-Ray-to-Triage loop-back visits:", len(loopback_cases))
print(f"Loop-back percentage: {loopback_percentage:.2f}%")

print("\nOUTPUT FILES")
print("-" * 60)
print("Activity transitions:", TRANSITIONS_FILE)
print("Waiting-time summary:", WAITING_TIMES_FILE)

print("\nProcess analysis completed successfully!")
print("=" * 60)