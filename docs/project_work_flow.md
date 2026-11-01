## Project Workflow

```mermaid
flowchart TD
    A[Raw data: Sepsis_Dataset.xlsx] --> B[data_cleaning.py<br/>remove nulls and duplicates]
    B --> C[Cleaned data in data/processed]
    C --> D[Event log: case_id, activity, timestamp<br/>clean_log.csv]
    D --> E[variants_analysis.py<br/>common pathways]
    D --> F[case_duration.py<br/>time per case]
    D --> G[Waiting_time.py<br/>wait between steps]
    D --> H[rework_analysis.py<br/>repeated steps]
    D --> I[conformance_check.py<br/>expected order]
    E --> J[export_findings.py<br/>CSV outputs]
    F --> J
    G --> J
    H --> J
    I --> J
    J --> K[dashboard/app.py<br/>Streamlit dashboard]
    J --> L[tests/<br/>pytest checks]
    K --> M[Recommendations and final report]
```

### Steps in words
1. **Collect and clean**: load the dataset, check nulls and duplicates, save the cleaned file.
2. **Build the event log**: each row needs a case ID, an activity and a timestamp.
3. **Analyse**: variants, case duration, waiting time, rework and conformance.
4. **Export**: save the results as CSV files.
5. **Visualise**: the Streamlit dashboard shows KPIs, charts and filters.
6. **Test**: pytest checks missing values, ordering and negative times.
7. **Report**: write recommendations, the final report and the presentation.

### Weekly timeline
| Week | Focus |
|------|-------|
| 1 | Setup, data collection, cleaning |
| 2 | Event log, variants, case duration |
| 3 | Waiting time, rework, conformance, dashboard |
| 4 | Tests, recommendations, final report, presentation |
