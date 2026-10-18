from pathlib import Path
import pandas as pd


# ==========================================
# STEP 1: SET UP FILE PATHS
# ==========================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

CLEAN_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "hospital_event_log_clean.csv"
)

DOCUMENTATION_DIR = PROJECT_DIR / "documentation"
DOCUMENTATION_DIR.mkdir(parents=True, exist_ok=True)

REPORT_FILE = (
    DOCUMENTATION_DIR
    / "validation_report.txt"
)


# ==========================================
# STEP 2: LOAD CLEANED DATASET
# ==========================================

if not CLEAN_FILE.exists():
    raise FileNotFoundError(
        "Cleaned dataset not found.\n"
        "Run this command first:\n"
        "python scripts/clean_event_log.py"
    )

df = pd.read_csv(CLEAN_FILE)

print("=" * 60)
print("CAREFLOW - EVENT LOG VALIDATION")
print("=" * 60)

print("\nDataset loaded successfully.")
print("Total event records:", len(df))


# ==========================================
# STEP 3: DEFINE REQUIRED COLUMNS
# ==========================================

required_columns = [
    "case_id",
    "activity",
    "timestamp",
    "department",
    "resource"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

checks = {}

checks["Required columns present"] = (
    len(missing_columns) == 0
)

if missing_columns:
    print("\nMissing columns:", missing_columns)
    raise ValueError(
        "Validation cannot continue because required columns are missing."
    )


# ==========================================
# STEP 4: VALIDATE TIMESTAMPS
# ==========================================

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

checks["No invalid timestamps"] = (
    df["timestamp"].notna().all()
)


# ==========================================
# STEP 5: CHECK MISSING VALUES
# ==========================================

missing_values = int(
    df[required_columns].isna().sum().sum()
)

checks["No missing required values"] = (
    missing_values == 0
)


# ==========================================
# STEP 6: CHECK DUPLICATE EVENTS
# ==========================================

duplicate_events = int(
    df.duplicated(
        subset=required_columns
    ).sum()
)

checks["No exact duplicate events"] = (
    duplicate_events == 0
)


# ==========================================
# STEP 7: CHECK CASE IDENTIFIERS
# ==========================================

checks["Every event has a case ID"] = (
    df["case_id"].notna().all()
    and df["case_id"].astype(str).str.strip().ne("").all()
)


# ==========================================
# STEP 8: CHECK ACTIVITY VALUES
# ==========================================

checks["Every event has an activity"] = (
    df["activity"].notna().all()
    and df["activity"].astype(str).str.strip().ne("").all()
)


# ==========================================
# STEP 9: CHECK CHRONOLOGICAL ORDER
# ==========================================

# Sort the dataset by case ID and timestamp.
# Then verify that timestamps never decrease within a case.

ordered_df = df.sort_values(
    ["case_id", "timestamp"]
).copy()

time_differences = (
    ordered_df.groupby("case_id")["timestamp"]
    .diff()
)

checks["Timestamps ordered within each case"] = (
    time_differences.dropna().ge(pd.Timedelta(0)).all()
)


# ==========================================
# STEP 10: CHECK PATIENT VISITS
# ==========================================

unique_cases = int(df["case_id"].nunique())

checks["At least one patient visit exists"] = (
    unique_cases > 0
)

events_per_case = df.groupby("case_id").size()

checks["Every case has at least one event"] = (
    len(events_per_case) > 0
    and events_per_case.gt(0).all()
)


# ==========================================
# STEP 11: CHECK HOSPITAL ACTIVITIES
# ==========================================

allowed_activities = {
    "Registration",
    "Doctor Consultation",
    "Blood Test",
    "X-Ray",
    "Diagnosis",
    "Treatment",
    "Discharge"
}

unexpected_activities = sorted(
    set(df["activity"].dropna().unique())
    - allowed_activities
)

checks["Activities belong to the allowed list"] = (
    len(unexpected_activities) == 0
)


# ==========================================
# STEP 12: DISPLAY VALIDATION RESULTS
# ==========================================

print("\nVALIDATION RESULTS")
print("-" * 60)

for check_name, passed in checks.items():

    status = "PASS" if passed else "FAIL"

    print(f"{check_name}: {status}")


print("\nDATASET SUMMARY")
print("-" * 60)

print("Total event records:", len(df))
print("Unique patient visits:", unique_cases)
print("Missing required values:", missing_values)
print("Duplicate events:", duplicate_events)
print("Invalid timestamps:", int(df["timestamp"].isna().sum()))

if unexpected_activities:
    print("Unexpected activities:", unexpected_activities)


# ==========================================
# STEP 13: SAVE VALIDATION REPORT
# ==========================================

overall_status = (
    "PASS" if all(checks.values()) else "FAIL"
)

report_lines = [
    "CAREFLOW: CLINICAL PATHWAY PROCESS MINING",
    "EVENT LOG VALIDATION REPORT",
    "=" * 60,
    "",
    f"Dataset: {CLEAN_FILE.name}",
    f"Total event records: {len(df)}",
    f"Unique patient visits: {unique_cases}",
    f"Missing required values: {missing_values}",
    f"Duplicate events: {duplicate_events}",
    f"Invalid timestamps: {int(df['timestamp'].isna().sum())}",
    "",
    "VALIDATION CHECKS",
    "-" * 60
]

for check_name, passed in checks.items():

    status = "PASS" if passed else "FAIL"

    report_lines.append(
        f"{check_name}: {status}"
    )

report_lines.extend([
    "",
    f"OVERALL VALIDATION STATUS: {overall_status}",
    ""
])

REPORT_FILE.write_text(
    "\n".join(report_lines),
    encoding="utf-8"
)


# ==========================================
# STEP 14: FINAL RESULT
# ==========================================

print("\n" + "=" * 60)
print("OVERALL VALIDATION STATUS:", overall_status)
print("=" * 60)

print("\nValidation report saved to:")
print(REPORT_FILE)

if overall_status == "PASS":
    print("\nSUCCESS: The dataset passed all implemented checks.")
else:
    print("\nACTION REQUIRED: Review the failed validation checks.")
