# CareFlow: Clinical Pathway Process Mining

**An Internship Project at Infotact Solutions | Data Analytics**

## Project Overview

CareFlow is a process mining project that analyzes patient-care pathways in a hospital using an event log. It cleans the data, discovers the most common pathways, measures how long cases and individual steps take, and flags repeated activities that may point to workflow inefficiencies. Results are shown in a Streamlit dashboard.

## Objectives

- Clean, preprocess, and validate the hospital event log.
- Discover common clinical pathways (process variants).
- Calculate total case duration and the waiting time between activities.
- Identify transitions with long delays (potential bottlenecks).
- Detect repeated activities and process loops.
- Present the results in an interactive dashboard.

## Technologies Used

| Technology | Purpose |
| --- | --- |
| Python | Data processing and analysis |
| Pandas | Data cleaning and manipulation |
| PM4Py | Process mining (directly-follows graph) |
| Streamlit | Interactive dashboard |
| Git and GitHub | Version control |

## Dataset

The project uses the **Sepsis Cases event log**, a public, de-identified hospital event log. Each case is one patient's pathway, and each row is one recorded activity.

The cleaned log in `data/processed/` uses these core fields:

| Column | Description |
| --- | --- |
| `case_id` | Unique identifier for a patient case |
| `activity` | Clinical or administrative activity |
| `timestamp` | Date and time the activity occurred |

> Check the exact column names in your cleaned file and update this table if they differ.

**Data privacy:** The dataset is public and de-identified. No personally identifiable patient information is included in this repository.

## Project Structure

```
infotact-internship/
├── data/
│   └── processed/                 # Cleaned data and analysis outputs (CSV)
├── dashboard/
│   └── app.py                     # Streamlit dashboard
├── docs/
│   └── findings.md                # Key findings generated from the results
├── Sepsis_Dataset ....xlsx        # Original dataset
├── data_cleaning.py               # Clean and validate the event log
├── variants_analysis.py           # Most common patient pathways
├── main.py                        # Directly-follows graph with PM4Py
├── case_duration.py               # Total duration of each case
├── Waiting_time.py                # Waiting time between activities
├── rework_analysis.py             # Repeated activities and loops
├── export_findings.py             # Generate docs/findings.md
├── Member1_Data_Collection_and_Data_Cleaning_Report.md
├── requirements.txt
└── README.md
```

## Installation and Setup

**Prerequisites:** Python 3.10 or newer, and Git.

```bash
git clone https://github.com/AP24110011714/infotact-internship.git
cd infotact-internship
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## How to Run

Run the scripts from the repository's main folder, in this order:

| Step | Command | What it does |
| --- | --- | --- |
| 1 | `python data_cleaning.py` | Cleans the dataset and saves it to `data/processed/` |
| 2 | `python variants_analysis.py` | Finds the most common pathways |
| 3 | `python main.py` | Builds the directly-follows graph |
| 4 | `python case_duration.py` | Calculates the duration of each case |
| 5 | `python Waiting_time.py` | Calculates waiting time between activities |
| 6 | `python rework_analysis.py` | Detects repeated activities |
| 7 | `python export_findings.py` | Writes `docs/findings.md` |
| 8 | `streamlit run dashboard/app.py` | Opens the dashboard |

Each script saves its results as CSV files in `data/processed/`. Check the script's code for the exact output file names.

## Analysis Overview

1. **Data cleaning:** handles duplicates, missing values, and timestamp formats, and orders events by case and time.
2. **Process variants:** groups each case's activity sequence and counts how often each pathway occurs.
3. **Directly-follows graph:** shows which activity directly follows which, and how often.
4. **Case duration:** time from the first to the last event of each case.
5. **Waiting times:** time between consecutive activities, summarized per transition (mean, median, 90th percentile).
6. **Rework detection:** finds activities that occur more than once in a case.

Key numbers from the analysis are written to `docs/findings.md`.

## Dashboard

The Streamlit dashboard (`dashboard/app.py`) shows KPI cards (total cases, median duration, number of variants, share of cases with rework) and tables of the longest cases and slowest transitions. More charts are being added.

## Project Status

| Phase | Status |
| --- | --- |
| Data collection and cleaning | Done |
| Pathway, duration, waiting-time and rework analysis | Done |
| Dashboard skeleton | Done |
| Dashboard charts and filters | In progress |
| Final report and presentation | Planned |

## Notes

Long waits and repeated activities are signals to examine, not proof of poor clinical care. This project is for educational and analytics purposes and does not provide medical advice.

## Internship Information

- **Organization:** Infotact Solutions
- **Domain:** Data Analytics
- **Project:** CareFlow: Clinical Pathway Process Mining
- **Project start date:** 10 October 2026

## Author

## Authors

- **Sravana Bandi**, GitHub: [AP24110011714](https://github.com/AP24110011714)
- **Abhinandan Naik**, GitHub: [abhi07-sr](https://github.com/abhi07-sr)
