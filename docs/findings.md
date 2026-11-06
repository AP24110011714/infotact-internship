# CareFlow Clinical Data Findings

## Dataset overview
- Unique patients: 5000
- Admission date range: 2022-01-01 to 2025-10-31
- Sepsis-positive records: 903
- Sepsis-negative records: 4097
- Records with unknown sepsis status: 0
- Sepsis rate among records with a known status: 18.1%

## Clinical measurements

| Measurement | Unit | Valid values | Missing values | Mean | Median |
| --- | --- | ---: | ---: | ---: | ---: |
| Temperature | °C | 4931 | 69 | 37.29 | 37.10 |
| Systolic blood pressure | mmHg | 4930 | 70 | 114.90 | 115.79 |
| Diastolic blood pressure | mmHg | 4932 | 68 | 72.70 | 73.46 |
| Heart rate | bpm | 4950 | 50 | 84.27 | 80.87 |
| White blood cell count | 10^9/L | 4828 | 172 | 8.81 | 7.93 |
| Lactate | mmol/L | 4840 | 160 | 1.67 | 1.29 |

## Patients by ward

| Ward | Patients | Sepsis-positive |
| --- | ---: | ---: |
| Ward-X | 1669 | 114 |
| ER | 1109 | 139 |
| ICU-A | 702 | 252 |
| ICU-B | 583 | 181 |
| Surgical-ICU | 491 | 127 |
| HDU | 446 | 90 |

## Data quality
- Rows removed for missing patient ID or admission date: 0
- Duplicate patient records removed: 0
- Out-of-range numeric measurements set to missing: 396

## Interpretation
These are descriptive summaries of the supplied patient-level records. They do not establish causes, diagnose sepsis, or measure care pathways. Sepsis-positive patients show markedly higher temperature, heart rate, WBC count and lactate than sepsis-negative patients, consistent with the ward-stratified distributions used to generate the data. These patterns demonstrate the analytical method; they are not clinical findings.
