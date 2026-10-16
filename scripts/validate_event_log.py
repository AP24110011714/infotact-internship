from pathlib import Path

import pandas as pd


# --------------------------------------------------
# STEP 1: SET UP PROJECT PATHS
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "hospital_event_log_clean.csv"
)

REPORT_FILE = (
    PROJECT_DIR
    / "documentation"
    / "validation_report.txt"
)

REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# STEP 2: DEFINE VALIDATION RULES
# --------------------------------------------------

REQUIRED_COLUMNS = [
    "case_id",
    "activity",
    "timestamp",
    "department",
    "resource"
]

ALLOWED_ACTIVITIES = [
    "Registration",
    "Triage",
    "Doctor Consultation",
    "Blood Test",
    "X-Ray",
    "Diagnosis",
    "Treatment",
    "Doctor Review",
    "Discharge"
]


# --------------------------------------------------
# STEP 3: LOAD THE CLEANED DATASET
# --------------------------------------------------

print("=" * 60)
print("CAREFLOW - EVENT LOG VALIDATION")
print("=" * 60)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Cleaned dataset not found: {INPUT_FILE}\n"
        "Run scripts/clean_event_log.py first."
    )

df = pd.read_csv(INPUT_FILE)

print("\nDataset loaded successfully.")
print("Total event records:", len(df))


# --------------------------------------------------
# STEP 4: PREPARE VALIDATION RESULTS
# --------------------------------------------------

results = []


def record_result(description, passed):
    """Record and display an individual validation result."""
    status = "PASS" if passed else "FAIL"
    results.append((description, status))

    print(f"{description}: {status}")


# --------------------------------------------------
# STEP 5: VALIDATE REQUIRED COLUMNS
# --------------------------------------------------

print("\nVALIDATION RESULTS")
print("-" * 60)

missing_columns = [
    column
    for column in REQUIRED_COLUMNS
    if column not in df.columns
]

record_result(
    "Required columns present",
    len(missing_columns) == 0
)

if missing_columns:
    print("Missing columns:", missing_columns)

    # Remaining checks require the expected schema.
    overall_pass = False

else:

    # --------------------------------------------------
    # STEP 6: VALIDATE TIMESTAMPS
    # --------------------------------------------------

    timestamps = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    record_result(
        "No invalid timestamps",
        timestamps.notna().all()
    )

    # --------------------------------------------------
    # STEP 7: VALIDATE REQUIRED VALUES
    # --------------------------------------------------

    required_values_present = (
        df[REQUIRED_COLUMNS].notna().all().all()
        and df[REQUIRED_COLUMNS]
        .astype(str)
        .apply(lambda column: column.str.strip().ne(""))
        .all()
        .all()
    )

    record_result(
        "No missing required values",
        required_values_present
    )

    # --------------------------------------------------
    # STEP 8: CHECK DUPLICATE EVENTS
    # --------------------------------------------------

    duplicate_count = int(
        df.duplicated(subset=REQUIRED_COLUMNS).sum()
    )

    record_result(
        "No exact duplicate events",
        duplicate_count == 0
    )

    # --------------------------------------------------
    # STEP 9: CHECK CASE IDs
    # --------------------------------------------------

    record_result(
        "Every event has a case ID",
        df["case_id"].notna().all()
        and df["case_id"].astype(str).str.strip().ne("").all()
    )

    # --------------------------------------------------
    # STEP 10: CHECK ACTIVITY VALUES
    # --------------------------------------------------

    record_result(
        "Every event has an activity",
        df["activity"].notna().all()
        and df["activity"].astype(str).str.strip().ne("").all()
    )

    # --------------------------------------------------
    # STEP 11: CHECK TIMESTAMP ORDER WITHIN EACH CASE
    # --------------------------------------------------

    timestamp_order_pass = False

    if timestamps.notna().all():
        checked_df = df[["case_id"]].copy()
        checked_df["timestamp"] = timestamps

        ordered_df = checked_df.sort_values(
            ["case_id", "timestamp"],
            kind="stable"
        )

        # Compare the original sequence with chronological order.
        timestamp_order_pass = (
            ordered_df.index.to_list()
            == checked_df.index.to_list()
        )

    record_result(
        "Timestamps ordered within each case",
        timestamp_order_pass
    )

    # --------------------------------------------------
    # STEP 12: CHECK THAT PATIENT VISITS EXIST
    # --------------------------------------------------

    record_result(
        "At least one patient visit exists",
        df["case_id"].nunique() > 0
    )

    # --------------------------------------------------
    # STEP 13: CHECK EVERY CASE HAS AN EVENT
    # --------------------------------------------------

    record_result(
        "Every case has at least one event",
        not df.empty
        and df.groupby("case_id").size().gt(0).all()
    )

    # --------------------------------------------------
    # STEP 14: CHECK ALLOWED ACTIVITIES
    # --------------------------------------------------

    unexpected_activities = sorted(
        set(df["activity"].dropna().unique())
        - set(ALLOWED_ACTIVITIES)
    )

    record_result(
        "Activities belong to the allowed list",
        len(unexpected_activities) == 0
    )

    if unexpected_activities:
        print("Unexpected activities:", unexpected_activities)

    # --------------------------------------------------
    # STEP 15: DETERMINE OVERALL STATUS
    # --------------------------------------------------

    overall_pass = all(
        status == "PASS"
        for _, status in results
    )


# --------------------------------------------------
# STEP 16: DISPLAY DATASET SUMMARY
# --------------------------------------------------

print("\nDATASET SUMMARY")
print("-" * 60)

print("Total event records:", len(df))
print("Unique patient visits:", df["case_id"].nunique())

if all(column in df.columns for column in REQUIRED_COLUMNS):
    print(
        "Missing required values:",
        int(df[REQUIRED_COLUMNS].isna().any(axis=1).sum())
    )

    print(
        "Duplicate events:",
        int(df.duplicated(subset=REQUIRED_COLUMNS).sum())
    )

    parsed_timestamps = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    print(
        "Invalid timestamps:",
        int(parsed_timestamps.isna().sum())
    )

    unexpected_activities = sorted(
        set(df["activity"].dropna().unique())
        - set(ALLOWED_ACTIVITIES)
    )

    print("Unexpected activities:", unexpected_activities)


# --------------------------------------------------
# STEP 17: SAVE VALIDATION REPORT
# --------------------------------------------------

report_lines = [
    "CAREFLOW - EVENT LOG VALIDATION REPORT",
    "=" * 60,
    f"Input dataset: {INPUT_FILE}",
    f"Total event records: {len(df)}",
    f"Unique patient visits: {df['case_id'].nunique()}",
    "",
    "VALIDATION RESULTS",
    "-" * 60
]

for description, status in results:
    report_lines.append(f"{description}: {status}")

report_lines.extend([
    "",
    "=" * 60,
    "OVERALL VALIDATION STATUS: "
    + ("PASS" if overall_pass else "FAIL"),
    "=" * 60
])

REPORT_FILE.write_text(
    "\n".join(report_lines) + "\n",
    encoding="utf-8"
)

print("\n" + "=" * 60)
print(
    "OVERALL VALIDATION STATUS:",
    "PASS" if overall_pass else "FAIL"
)
print("=" * 60)

print("\nValidation report saved to:")
print(REPORT_FILE)

if not overall_pass:
    print("\nACTION REQUIRED: Review the failed validation checks.")
