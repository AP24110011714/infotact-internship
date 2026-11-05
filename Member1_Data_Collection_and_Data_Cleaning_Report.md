# Member 1 — Data Collection and Data Cleaning

## Dataset and scope

The supplied `Sepsis_Dataset ....xlsx` workbook contains 250 patient-level records with patient ID, admission date, clinical measurements, sepsis flag, ward, and doctor on duty. It is not a process-mining event log: it does not contain a sequence of activities or a timestamp for each activity. The analyses in this project therefore describe patient records; they do not claim to measure care pathways, waiting times, rework, or conformance.

## Cleaning workflow

The cleaning pipeline standardizes column names and maps known column aliases to a stable schema. Patient IDs are trimmed and uppercased, admission dates are parsed, and records missing either required field are removed. Duplicate patient IDs are reduced to the first valid record in source order. Sepsis flags are normalized for recognized Yes/No values; unrecognized and missing values remain missing.

Clinical fields are converted to numeric values. Values outside configured plausible bounds, including unparseable non-empty measurements, are set to missing rather than deleting the entire patient record. This retains valid information in other columns and the generated quality report counts invalid measurements by column.

## Validation and outputs

The pipeline records raw and final row counts, patients removed for missing required fields, duplicate records removed, invalid measurements, unique patients, and the admission date range. It writes the cleaned CSV and descriptive summaries to `data/processed/`, and generates `docs/findings.md`.

The supplied workbook currently labels every record as sepsis-negative. This is a property of the provided data, not evidence that the broader patient population has no sepsis. Group comparisons should not be interpreted when positive examples are absent.

## Reproducibility

From the project directory, run:

```powershell
python main.py
python -m pytest -q
```

The dashboard can be launched with `python -m streamlit run dashboard/app.py` after generating outputs. Findings are descriptive and educational, not medical advice or an assessment of clinical care.
