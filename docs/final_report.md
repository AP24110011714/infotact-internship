# CareFlow: Clinical Pathway Process Mining - Final Report
Author: Abhinandan Naik | Infotact Solutions Data Analytics Internship, Batch 22.1

## 1. Introduction
Hospitals record each step of a patient's care, but delays and repeated steps stay hidden
in averages. CareFlow uses process mining to rebuild patient pathways from event logs and
to measure waiting time, rework and conformance.

## 2. Dataset
- Source: Sepsis_Dataset_cleaned.csv, a patient-level table of 250 patients.
- Columns: patient_id, admission_date, temperature_c, bp_systolic, bp_diastolic,
  heart_rate, wbc_count, lactate_mmol_l, sepsis_flag, ward, doctor_on_duty.
- Cleaning: checked for nulls (none) and duplicates (none); 250 unique patients.
- Event log: process mining needs case_id, activity and timestamp. The dataset has one
  row per patient, so the event log used for analysis is <<state exactly how clean_log.csv
  was created, and call it simulated if it was>>.

## 3. Method
1. Clean data with pandas.
2. Build the event log (case_id, activity, timestamp).
3. Variants: count the unique activity sequences.
4. Case duration: last timestamp minus first timestamp per case.
5. Waiting time: gap to the next event, using shift(-1).
6. Rework: activities repeated inside one case.
7. Conformance: check the expected order of key steps (a simplified subsequence check,
   not token-replay).

## 4. Results
- Cases: <<n>>; events: <<n>>; variants: <<n>>
- Median case duration: <<value>>
- Slowest transition: <<A -> B, value>>
- Cases with rework: <<value>>%
- Conformant cases: <<value>>%

## 5. Dashboard
A Streamlit dashboard (dashboard/app.py) shows KPI cards, variants, bottlenecks and
conformance, with a duration slider and activity filter.

## 6. Testing
pytest checks for missing values, duplicates, timestamp order, negative durations and that
variant counts add up. Run: python -m pytest tests -v

## 7. Recommendations
See docs/recommendations.md.

## 8. Limitations
- The real dataset is patient-level, not a native event log.
- sepsis_flag is "No" for all 250 patients, so it cannot be used as an outcome.
- Conformance is simplified.
- Results demonstrate the method and are not clinical conclusions.

## 9. Conclusion
CareFlow shows how event logs reveal pathways, delays and rework. With a real hospital
event log the same pipeline would give actionable findings.
