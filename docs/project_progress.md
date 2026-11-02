\# CareFlow – Project Progress Report



\## Project Overview

CareFlow is a Clinical Pathway Process Mining project that analyzes simulated Electronic Health Record (EHR) event logs to identify patient flow patterns, waiting times, and process bottlenecks.



\## Completed Work



\### 1. Data Generation

\- Generated 3,058 raw event records.

\- Created 500 unique patient visits.

\- Introduced sample data-quality issues for validation testing.



\### 2. Data Cleaning and Validation

\- Cleaned the generated event log.

\- Removed duplicate records.

\- Handled missing department values and invalid timestamps.

\- Prepared 3,055 cleaned records for BigQuery loading.



\### 3. BigQuery Integration

\- Connected the Python pipeline to Google BigQuery.

\- Created and verified the CareFlow dataset.

\- Loaded 3,055 cleaned records into the raw\_ehr\_events table.

\- Verified the loaded row count.



\### 4. Pipeline Automation

\- Implemented pipeline/run\_pipeline.py.

\- Automated event generation and BigQuery loading.

\- Added execution logs, timing information, and error handling.

\- Added options for selective pipeline execution.



\### 5. Results Export

\- Implemented pipeline/export\_results.py.

\- Implemented BigQuery mart creation.

\- Generated CSV exports for KPI summary, loopbacks, transition times, and combined CareFlow results.



\### 6. Dashboard Development

\- Developed a Streamlit dashboard in dashboard/app.py.

\- Added Docker setup for application deployment.



\## Current Verification Status

\- Event generation: Successful.

\- BigQuery loading: Successful.

\- Dashboard implementation: Completed; runtime verification pending.

\- dbt integration: Pending directory and teammate contribution verification.

\- Process mining integration: Pending directory and teammate contribution verification.

\- Automated tests and documentation: Further verification required.



\## Next Steps

1\. Verify dashboard execution and visualizations.

2\. Integrate dbt transformations.

3\. Integrate process mining analysis.

4\. Verify BigQuery analytical tables.

5\. Complete automated testing.

6\. Perform end-to-end pipeline validation.



\## Conclusion

The data generation, validation, BigQuery loading, pipeline automation, results export implementation, and dashboard development have been completed. Remaining work focuses on integrating team components and final project validation.

