"""Exploratory data analysis of the patient-level Sepsis dataset."""
import pandas as pd

PATH = "data/processed/Sepsis_Dataset_cleaned.csv"
df = pd.read_csv(PATH)

lines = []
lines.append(f"Shape: {df.shape}")
lines.append(f"Missing values per column:\n{df.isnull().sum()}")
lines.append(f"Duplicate patient IDs: {df['patient_id'].duplicated().sum()}")
lines.append(f"Summary statistics:\n{df.describe()}")
lines.append(f"Patients per ward:\n{df['ward'].value_counts()}")
lines.append(f"Patients per doctor:\n{df['doctor_on_duty'].value_counts()}")
lines.append(f"Sepsis flag counts:\n{df['sepsis_flag'].value_counts()}")
months = pd.to_datetime(df["admission_date"]).dt.to_period("M")
lines.append(f"Admissions per month:\n{months.value_counts().sort_index()}")

report = "\n\n".join(lines)
print(report)
with open("outputs/eda_summary.txt", "w") as f:
    f.write(report)
