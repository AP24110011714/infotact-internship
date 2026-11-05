# CareFlow Clinical Data Findings

## Dataset overview
- Unique patients: 250
- Admission date range: 2023-01-02 to 2024-01-01
- Sepsis-positive records: 0
- Sepsis-negative records: 250
- Records with unknown sepsis status: 0
- Sepsis rate among records with a known status: 0.0%

## Clinical measurements

| Measurement | Unit | Valid values | Missing values | Mean | Median |
| --- | --- | ---: | ---: | ---: | ---: |
| Temperature | °C | 250 | 0 | 36.99 | 37.10 |
| Systolic blood pressure | mmHg | 250 | 0 | 115.32 | 115.00 |
| Diastolic blood pressure | mmHg | 250 | 0 | 74.19 | 74.00 |
| Heart rate | bpm | 250 | 0 | 91.29 | 91.50 |
| White blood cell count | 10^9/L | 246 | 4 | 7.54 | 7.40 |
| Lactate | mmol/L | 244 | 6 | 1.96 | 1.95 |

## Patients by ward

| Ward | Patients | Sepsis-positive |
| --- | ---: | ---: |
| ICU-A | 67 | 0 |
| ICU-B | 67 | 0 |
| Ward-X | 61 | 0 |
| ER | 55 | 0 |

## Data quality
- Rows removed for missing patient ID or admission date: 0
- Duplicate patient records removed: 0
- Out-of-range numeric measurements set to missing: 10

## Interpretation
These are descriptive summaries of the supplied patient-level records. They do not establish causes, diagnose sepsis, or measure care pathways. The supplied workbook currently labels every record as sepsis-negative, so comparisons between positive and negative groups are not possible.
