from pathlib import Path
import pandas as pd


# ==========================================
# STEP 1: SET UP FILE PATHS
# ==========================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = (
    PROJECT_DIR
    / "data"
    / "raw"
    / "hospital_event_log_raw.csv"
)

PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

CLEAN_FILE = (
    PROCESSED_DIR
    / "hospital_event_log_clean.csv"
)

DOCUMENTATION_DIR = PROJECT_DIR / "documentation"
DOCUMENTATION_DIR.mkdir(parents=True, exist_ok=True)

REPORT_FILE = (
    DOCUMENTATION_DIR
    / "data_quality_report.txt"
)


# ==========================================
# STEP 2: LOAD RAW DATA
# ==========================================

if not RAW_FILE.exists():
    raise FileNotFoundError(
        f"Raw dataset not found: {RAW_FILE}\n"
        "Run generate_event_log.py first."
    )

df = pd.read_csv(RAW_FILE)

initial_rows = len(df)

print("=" * 55)
print("CAREFLOW - EVENT LOG DATA CLEANING")
print("=" * 55)

print("\nRaw dataset loaded successfully.")
print("Initial event records:", initial_rows)


# ==========================================
# STEP 3: CHECK REQUIRED COLUMNS
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

if missing_columns:
    raise ValueError(
        f"Required columns are missing: {missing_columns}"
    )

# Keep only the columns required by this project
df = df[required_columns].copy()


# ==========================================
# STEP 4: CLEAN TEXT COLUMNS
# ==========================================

text_columns = [
    "case_id",
    "activity",
    "department",
    "resource"
]

for column in text_columns:
    df[column] = df[column].astype("string").str.strip()

# Convert empty strings and whitespace-only values to missing
df[text_columns] = df[text_columns].replace(
    r"^\s*$",
    pd.NA,
    regex=True
)


# ==========================================
# STEP 5: CLEAN TIMESTAMPS
# ==========================================

# Invalid timestamp strings become NaT (missing datetime)
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

invalid_timestamps = int(df["timestamp"].isna().sum())

print("\nInvalid timestamps detected:", invalid_timestamps)


# ==========================================
# STEP 6: DETECT DUPLICATE EVENTS
# ==========================================

event_columns = [
    "case_id",
    "activity",
    "timestamp",
    "department",
    "resource"
]

duplicate_events = int(
    df.duplicated(subset=event_columns).sum()
)

print("Duplicate events detected:", duplicate_events)


# ==========================================
# STEP 7: CHECK MISSING VALUES
# ==========================================

missing_values_before = int(df.isna().sum().sum())

print(
    "Missing values detected before cleaning:",
    missing_values_before
)


# ==========================================
# STEP 8: REMOVE EXACT DUPLICATE EVENTS
# ==========================================

df = df.drop_duplicates(
    subset=event_columns,
    keep="first"
)


# ==========================================
# STEP 9: REMOVE INCOMPLETE RECORDS
# ==========================================

# These fields are essential for process mining
df = df.dropna(
    subset=[
        "case_id",
        "activity",
        "timestamp",
        "department",
        "resource"
    ]
)


# ==========================================
# STEP 10: SORT EVENTS CHRONOLOGICALLY
# ==========================================

df = df.sort_values(
    by=["case_id", "timestamp"]
).reset_index(drop=True)


# ==========================================
# STEP 11: SAVE CLEANED DATASET
# ==========================================

df.to_csv(
    CLEAN_FILE,
    index=False
)

final_rows = len(df)

removed_rows = initial_rows - final_rows

missing_values_after = int(df.isna().sum().sum())


# ==========================================
# STEP 12: GENERATE DATA QUALITY REPORT
# ==========================================

report = f"""
CAREFLOW: CLINICAL PATHWAY PROCESS MINING
DATA QUALITY REPORT
=======================================================

Input file:
{RAW_FILE}

Output file:
{CLEAN_FILE}

Initial event records: {initial_rows}
Final event records: {final_rows}
Records removed: {removed_rows}

Unique patient visits remaining: {df['case_id'].nunique()}

Invalid timestamps detected: {invalid_timestamps}
Exact duplicate events detected: {duplicate_events}

Missing values before cleaning: {missing_values_before}
Missing values after cleaning: {missing_values_after}

Cleaning operations:
1. Standardized text fields.
2. Converted timestamps into datetime values.
3. Removed exact duplicate event records.
4. Removed records with missing required fields.
5. Sorted events by case ID and timestamp.

Final checks:
No missing values: {missing_values_after == 0}
No duplicate events: {df.duplicated(subset=event_columns).sum() == 0}
All timestamps valid: {df['timestamp'].notna().all()}
Required columns present: {all(c in df.columns for c in required_columns)}

Note:
Records with missing required fields or invalid timestamps
were removed rather than assigned invented values.

=======================================================
"""

REPORT_FILE.write_text(
    report,
    encoding="utf-8"
)


# ==========================================
# STEP 13: DISPLAY RESULTS
# ==========================================

print("\nCleaning completed successfully!")

print("\nInitial records:", initial_rows)
print("Final records:", final_rows)
print("Records removed:", removed_rows)

print(
    "Unique patient visits remaining:",
    df["case_id"].nunique()
)

print(
    "\nMissing values after cleaning:",
    missing_values_after
)

print("\nCleaned dataset saved to:")
print(CLEAN_FILE)

print("\nData quality report saved to:")
print(REPORT_FILE)

print("\n" + "=" * 55)
print("DATA CLEANING FINISHED")
print("=" * 55)
