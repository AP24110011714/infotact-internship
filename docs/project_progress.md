# CareFlow – Project Progress Report

## 1. Project Overview

CareFlow is a Clinical Pathway Process Mining project that analyzes simulated Electronic Health Record (EHR) event logs to identify patient flow patterns, waiting times, and process bottlenecks.

## 2. Completed Work

### 2.1 Data Generation
- Generated 3,058 raw event records.
- Created 500 unique patient visits.
- Introduced sample data-quality issues for validation testing.

### 2.2 Data Cleaning and Validation
- Cleaned the generated event log.
- Removed duplicate records.
- Handled missing department values and invalid timestamps.
- Prepared 3,055 cleaned records.
- Successfully passed all 10 event-log validation checks.

### 2.3 BigQuery Integration
- Connected the Python pipeline to Google BigQuery.
- Configured the CareFlow dataset.
- Loaded 3,055 cleaned records into the `raw_ehr_events` table.
- Verified that the BigQuery table contains all 3,055 records.

### 2.4 Pipeline Automation
- Implemented `pipeline/run_pipeline.py`.
- Automated event generation and BigQuery loading.
- Added execution logs, timing information, and error handling.
- Added options for selective pipeline execution and dry-run testing.

### 2.5 Process Performance Analysis
- Analyzed 3,055 event records across 500 patient visits.
- Calculated patient visit durations and transition waiting times.
- Identified frequently occurring activities and slower process transitions.
- Generated activity frequency and visit duration visualizations.
- Created a bottleneck analysis report.

### 2.6 BigQuery Results Export
- Implemented `pipeline/export_results.py`.
- Exported 12 transition records.
- Exported 63 loopback records.
- Exported the KPI summary.
- Generated a combined CareFlow summary containing 76 rows.
- Successfully uploaded the combined summary to BigQuery.

### 2.7 Dashboard Development
- Developed a Streamlit dashboard in `dashboard/app.py`.
- Added KPI cards, charts, filters, and CSV download functionality.
- Created Docker configuration files.
- Deployed the dashboard using Streamlit Community Cloud.

### 2.8 Testing
- Installed and configured pytest.
- Executed the automated test suite.
- Successfully passed all 5 tests:
  - CareFlow summary existence.
  - CSV readability.
  - KPI summary existence.
  - Loopbacks file existence.
  - Transition times file existence.

## 3. Current Verification Status

| Component | Status |
|---|---|
| Data generation | Completed |
| Data cleaning | Completed |
| Event-log validation | 10 checks passed |
| BigQuery integration | Verified |
| Process performance analysis | Completed |
| Bottleneck report | Generated |
| BigQuery results export | Successful |
| Streamlit dashboard | Deployed |
| Automated tests | 5 tests passed |
| Pipeline dry-run | Tested |
| dbt integration | Pending |
| Separate process-mining pipeline integration | Pending |
| Complete end-to-end pipeline | Pending |

## 4. Remaining Work

1. Improve the automated pipeline to include process analysis and results export.
2. Verify and integrate the dbt component when the team implementation is available.
3. Verify and integrate the separate process-mining component when available.
4. Perform final dashboard and deployment checks.
5. Complete end-to-end pipeline testing without unnecessarily overwriting existing BigQuery data.
6. Update the final project documentation and GitHub repository.

## 5. Conclusion

The CareFlow data generation, cleaning, validation, BigQuery integration, process performance analysis, results export, and dashboard development have been completed.

The latest verification confirms that 3,055 cleaned records were successfully loaded into BigQuery, analytical results were exported, and all five automated tests passed.

The remaining work focuses on pipeline integration, team component verification, and final project validation.