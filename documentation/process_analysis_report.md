# CareFlow: Clinical Pathway Process Mining

## 1. Project Overview

CareFlow uses a synthetic hospital event log to examine patient pathways, event transitions, elapsed time between activities, and potential process bottlenecks.

## 2. Dataset Summary

- Patient visits: 7,000
- Cleaned event records: 54,497
- Visits containing X-Ray: 2,794

## 3. X-Ray-to-Triage Loop-Back Analysis

- Visits containing X-Ray: 2,794
- Visits with Triage after X-Ray: 1,131
- Loop-back rate among X-Ray visits: 40.48%

Interpretation: the synthetic dataset models a repeated Triage step after X-Ray for a subset of visits. In a real hospital, this pattern could be investigated for causes such as missing paperwork, incomplete documentation, or clinical reassessment. The synthetic data does not establish the actual cause of a loop-back.

## 4. Transitions With the Highest Average Elapsed Time

The following transitions have the highest average elapsed time between consecutive recorded activities.

| Transition | Event count | Average elapsed minutes | Median elapsed minutes |
|---|---:|---:|---:|
| Doctor Consultation -> Doctor Review | 448 | 49.53 | 53.00 |
| Doctor Consultation -> Diagnosis | 1049 | 48.27 | 49.00 |
| Doctor Consultation -> Blood Test | 4509 | 48.03 | 48.00 |
| Treatment -> Discharge | 7000 | 47.95 | 48.00 |
| Doctor Review -> Diagnosis | 4065 | 47.87 | 48.00 |

## 5. Interpretation and Limitations

Elapsed time between consecutive event timestamps is not necessarily queue waiting time. It can include service time, waiting time, and other delays. The current dataset does not record separate activity start and completion timestamps.

The data is synthetic and is intended for process-mining practice. The results should not be interpreted as findings about a real hospital.

## 6. Recommended Next Steps

- Load the cleaned event log into BigQuery.
- Build standardized event-log models using dbt.
- Discover the process model using PM4Py.
- Build a dashboard to explore transitions and elapsed times.
- Add tests for data quality and process conformance.
