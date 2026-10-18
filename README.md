# CareFlow: Clinical Pathway Process Mining

## 1. Project Overview

CareFlow is a healthcare process-mining project that analyzes patient journeys using event-log data. The project aims to understand the sequence of hospital activities and prepare data for identifying process inefficiencies and bottlenecks.

## 2. Member 1 Responsibilities

Member 1 is responsible for:

* Generating the initial hospital event log.
* Cleaning and standardizing event data.
* Identifying missing values, invalid timestamps, and duplicate records.
* Validating the cleaned dataset.
* Preparing a data dictionary and data quality reports.

## 3. Technologies Used

* Python
* Pandas
* CSV
* Visual Studio Code

## 4. Dataset Description

The event log contains the following columns:

| Column     | Description                                      |
| ---------- | ------------------------------------------------ |
| case_id    | Unique identifier for a patient visit            |
| activity   | Hospital activity performed                      |
| timestamp  | Date and time of the activity                    |
| department | Hospital department associated with the activity |
| resource   | Staff member or resource performing the activity |

## 5. Project Folder Structure

* `data/raw/`: Stores the original generated event log.
* `data/processed/`: Stores the cleaned event log.
* `scripts/`: Contains Python programs for data generation, cleaning, and validation.
* `documentation/`: Contains the data dictionary and quality reports.

## 6. Execution Instructions

Run the following commands from the main project directory.

### Generate the raw event log

```bash
python scripts/generate_event_log.py
```

### Clean the event log

```bash
python scripts/clean_event_log.py
```

### Validate the cleaned event log

```bash
python scripts/validate_event_log.py
```

Run these commands in the specified order.

## 7. Data Cleaning

The cleaning program:

1. Standardizes text fields.
2. Converts timestamps into datetime values.
3. Detects and removes exact duplicate event records.
4. Removes records containing missing required fields or invalid timestamps.
5. Sorts events by case identifier and timestamp.
6. Saves the cleaned dataset.
7. Generates a data quality report.

## 8. Data Validation

The validation program checks:

* Required columns are present.
* Required fields contain no missing values.
* Timestamps are valid.
* Exact duplicate events are absent.
* Patient visit identifiers are present.
* Activities belong to the defined activity list.
* Events are chronologically ordered within each case.

## 9. Output Files

### Raw dataset

`data/raw/hospital_event_log_raw.csv`

### Cleaned dataset

`data/processed/hospital_event_log_clean.csv`

### Data quality report

`documentation/data_quality_report.txt`

### Validation report

`documentation/validation_report.txt`

### Data dictionary

`documentation/data_dictionary.csv`

## 10. Data Privacy

The initial dataset is synthetic demonstration data and does not represent actual patient records. Any replacement with real healthcare data must follow the project's authorization, privacy, and data-handling requirements.

## 11. Project Status

The data preparation stage is complete when the generation and cleaning programs run successfully, all required validation checks pass, and the documentation reflects the actual results.

## 12. Handover

The cleaned event log, data dictionary, and quality reports are intended for the next project stages, including data ingestion and clinical pathway process-mining analysis.
