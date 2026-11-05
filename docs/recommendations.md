# CareFlow Recommendations

Based on the analysis pipeline run on `clean_log.csv`. The event log is simulated
from the 250 real patient records (generate_events.py, seed 42), so these
recommendations show how the method turns findings into actions. They are not
clinical conclusions.

## 1. Reduce waiting before Ward Admission
- Finding: Ward Admission → Discharge and Observation → Discharge are the slowest transitions.
- Action: review bed-turnover and discharge-paperwork steps; set a target wait per step.

## 2. Cut repeated Lab Tests and Doctor Review
- Finding: about 7.6% of cases repeat these steps, mostly after high lactate.
- Action: agree a repeat-test protocol so the repeat is done on schedule, not ad hoc.

## 3. Speed up sepsis-screen patients
- Finding: screen-positive patients take longer end to end than screen-negative ones.
- Action: monitor time from ER Sepsis Triage to IV Antibiotics as a standing KPI.

## 4. Improve conformance to the expected pathway
- Finding: about 88% of cases follow Registration → Triage → Lab Tests → Doctor Review → Discharge.
- Action: investigate the deviating cases, such as skipped labs or no doctor review.

## 5. Fix data quality
- Finding: sepsis_flag is "No" for all 250 patients, though 89 meet a vitals screen.
- Action: validate how the flag is recorded before relying on it.

## Limitations
- Event log is simulated; conformance is a simplified order check, not token replay.
- Replace the simulated log with a real event log when one is available.

## Next Steps
- Re-run all analysis scripts after any change to the event log.
- Run python -m pytest tests -v before every submission.
- Compare dashboard figures with the exported CSV files to confirm they match.
