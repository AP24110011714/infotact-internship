import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# STEP 1: SET UP PROJECT DIRECTORIES
# --------------------------------------------------

random.seed(42)

PROJECT_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = RAW_DIR / "hospital_event_log_raw.csv"


# --------------------------------------------------
# STEP 2: DEFINE HOSPITAL ACTIVITIES
# --------------------------------------------------

ACTIVITIES = {
    "Registration": "Reception",
    "Doctor Consultation": "OPD",
    "Blood Test": "Laboratory",
    "X-Ray": "Radiology",
    "Diagnosis": "OPD",
    "Treatment": "Treatment",
    "Discharge": "Reception"
}


# --------------------------------------------------
# STEP 3: DEFINE HOSPITAL STAFF
# --------------------------------------------------

RESOURCES = {
    "Reception": ["Staff_01", "Staff_02"],
    "OPD": ["Doctor_01", "Doctor_02"],
    "Laboratory": ["Technician_01", "Technician_02"],
    "Radiology": ["Technician_03"],
    "Treatment": ["Doctor_01", "Nurse_01"]
}


# --------------------------------------------------
# STEP 4: GENERATE SYNTHETIC PATIENT EVENTS
# --------------------------------------------------

number_of_cases = 500

start_date = datetime(2026, 10, 1, 8, 0, 0)

events = []

for case_number in range(1, number_of_cases + 1):

    # Generate a unique patient visit identifier
    case_id = f"P{case_number:04d}"

    # Assign a starting time to the patient visit
    current_time = start_date + timedelta(
        minutes=random.randint(0, 60 * 24 * 7)
    )

    # Every patient starts with registration and consultation
    patient_activities = [
        "Registration",
        "Doctor Consultation"
    ]

    # Some patients require a blood test
    if random.random() < 0.65:
        patient_activities.append("Blood Test")

    # Some patients require an X-ray
    if random.random() < 0.30:
        patient_activities.append("X-Ray")

    # Some patients return for another consultation
    if random.random() < 0.15:
        patient_activities.append("Doctor Consultation")

    # Complete the hospital visit
    patient_activities.extend([
        "Diagnosis",
        "Treatment",
        "Discharge"
    ])

    # Generate one event for each activity
    for activity in patient_activities:

        department = ACTIVITIES[activity]

        resource = random.choice(
            RESOURCES[department]
        )

        events.append({
            "case_id": case_id,
            "activity": activity,
            "timestamp": current_time,
            "department": department,
            "resource": resource
        })

        # Advance time before the next event
        current_time += timedelta(
            minutes=random.randint(5, 60)
        )


# --------------------------------------------------
# STEP 5: CREATE THE EVENT LOG DATAFRAME
# --------------------------------------------------

df = pd.DataFrame(events)


# --------------------------------------------------
# STEP 6: INTRODUCE DATA-QUALITY ISSUES
# --------------------------------------------------

# Introduce a missing department
df.loc[0, "department"] = None

# IMPORTANT:
# Convert datetime values to strings before inserting
# an invalid timestamp. This prevents the Pandas error.
df["timestamp"] = df["timestamp"].astype(str)

# Introduce an invalid timestamp
df.loc[1, "timestamp"] = "invalid_timestamp"

# Introduce one exact duplicate event
df = pd.concat(
    [df, df.iloc[[2]]],
    ignore_index=True
)


# --------------------------------------------------
# STEP 7: SAVE THE RAW EVENT LOG
# --------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# --------------------------------------------------
# STEP 8: DISPLAY GENERATION RESULTS
# --------------------------------------------------

print("=" * 55)
print("CAREFLOW: CLINICAL PATHWAY PROCESS MINING")
print("=" * 55)

print("\nRaw event log generated successfully!")

print("\nOutput file:")
print(OUTPUT_FILE)

print("\nTotal event records:", len(df))

print("Total unique patient visits:", df["case_id"].nunique())

print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst five records:")
print(df.head().to_string(index=False))

print("\nData-quality issues introduced for testing:")
print("- One missing department")
print("- One invalid timestamp")
print("- One duplicate event")

print("\nGeneration completed successfully!")
print("=" * 55)
