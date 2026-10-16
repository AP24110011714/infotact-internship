import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# STEP 1: PROJECT DIRECTORIES AND CONFIGURATION
# --------------------------------------------------

random.seed(42)

PROJECT_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = RAW_DIR / "hospital_event_log_raw.csv"

NUMBER_OF_VISITS = 7000

START_DATE = datetime(2026, 10, 1, 8, 0, 0)


# --------------------------------------------------
# STEP 2: HOSPITAL ACTIVITIES AND DEPARTMENTS
# --------------------------------------------------

ACTIVITIES = {
    "Registration": "Reception",
    "Triage": "Emergency",
    "Doctor Consultation": "OPD",
    "Blood Test": "Laboratory",
    "X-Ray": "Radiology",
    "Diagnosis": "OPD",
    "Treatment": "Treatment",
    "Doctor Review": "OPD",
    "Discharge": "Reception"
}


# --------------------------------------------------
# STEP 3: HOSPITAL STAFF
# --------------------------------------------------

RESOURCES = {
    "Reception": ["Staff_01", "Staff_02", "Staff_03"],
    "Emergency": ["Nurse_01", "Nurse_02", "Nurse_03"],
    "OPD": [
        "Doctor_01",
        "Doctor_02",
        "Doctor_03",
        "Doctor_04",
        "Doctor_05",
        "Doctor_06"
    ],
    "Laboratory": ["Technician_01", "Technician_02"],
    "Radiology": ["Technician_03", "Technician_04"],
    "Treatment": ["Doctor_01", "Nurse_01", "Nurse_02"]
}


# --------------------------------------------------
# STEP 4: GENERATE PATIENT VISITS
# --------------------------------------------------

events = []

loop_back_cases = 0

for case_number in range(1, NUMBER_OF_VISITS + 1):

    case_id = f"P{case_number:05d}"

    # Spread arrivals over 30 days.
    current_time = START_DATE + timedelta(
        minutes=random.randint(0, 60 * 24 * 30)
    )

    patient_activities = [
        "Registration",
        "Triage",
        "Doctor Consultation"
    ]

    # Some patients need a blood test.
    needs_blood_test = random.random() < 0.65

    if needs_blood_test:
        patient_activities.append("Blood Test")

    # Some patients need an X-Ray.
    needs_xray = random.random() < 0.40

    if needs_xray:
        patient_activities.append("X-Ray")

        # Simulate a missing-paperwork bottleneck.
        # Approximately 40% of X-Ray patients return to Triage.
        if random.random() < 0.40:
            patient_activities.append("Triage")
            loop_back_cases += 1

        patient_activities.append("Doctor Review")

    # Patients who do not need an X-Ray may still need
    # another doctor review.
    elif random.random() < 0.30:
        patient_activities.append("Doctor Review")

    patient_activities.extend([
        "Diagnosis",
        "Treatment",
        "Discharge"
    ])

    # Generate timestamped event records.
    for activity in patient_activities:

        department = ACTIVITIES[activity]

        resource = random.choice(RESOURCES[department])

        events.append({
            "case_id": case_id,
            "activity": activity,
            "timestamp": current_time,
            "department": department,
            "resource": resource
        })

        # Activity duration and waiting time.
        # Random intervals produce variable process performance.
        current_time += timedelta(
            minutes=random.randint(5, 90)
        )


# --------------------------------------------------
# STEP 5: CREATE DATAFRAME AND SORT EVENTS
# --------------------------------------------------

df = pd.DataFrame(events)

df = df.sort_values(
    by=["case_id", "timestamp"]
).reset_index(drop=True)


# --------------------------------------------------
# STEP 6: INTRODUCE DATA-QUALITY ISSUES
# --------------------------------------------------

# One missing department.
df.loc[0, "department"] = None

# One invalid timestamp.
df["timestamp"] = df["timestamp"].astype(str)
df.loc[1, "timestamp"] = "invalid_timestamp"

# One exact duplicate event.
df = pd.concat(
    [df, df.iloc[[2]]],
    ignore_index=True
)


# --------------------------------------------------
# STEP 7: SAVE RAW EVENT LOG
# --------------------------------------------------

df.to_csv(OUTPUT_FILE, index=False)


# --------------------------------------------------
# STEP 8: DISPLAY GENERATION RESULTS
# --------------------------------------------------

print("=" * 60)
print("CAREFLOW: CLINICAL PATHWAY PROCESS MINING")
print("=" * 60)

print("\nRaw event log generated successfully!")

print("\nOutput file:")
print(OUTPUT_FILE)

print("\nTotal event records:", len(df))

print("Unique patient visits:", df["case_id"].nunique())

print(
    "X-Ray-to-Triage loop-back cases:",
    loop_back_cases
)

print(
    "Loop-back percentage among X-Ray patients: "
    f"{(loop_back_cases / max(1, sum(1 for _ in []))):.2f}%"
    if False else
    "See loop-back calculation below."
)

print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst five records:")
print(df.head().to_string(index=False))

print("\nData-quality issues introduced:")
print("- One missing department")
print("- One invalid timestamp")
print("- One duplicate event")

print("\nGeneration completed successfully!")
print("=" * 60)