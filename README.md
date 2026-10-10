# CareFlow: Clinical Pathway Process Mining

**An Internship Project at Infotact Solutions | Data Analytics**

## 📌 Project Overview

CareFlow is a data analytics and process mining project designed to analyze clinical workflows and patient-care pathways in hospital emergency departments (ERs).

The project uses hospital event logs to understand the sequence of activities involved in patient visits, measure waiting times, identify process bottlenecks, and detect repeated activities that may indicate workflow inefficiencies.

The goal is to transform event data into meaningful insights that can help healthcare teams understand clinical processes and identify opportunities to improve operational efficiency.

## 🎯 Objectives

* Analyze patient-care pathways using event log data.
* Clean, preprocess, and validate hospital workflow data.
* Calculate patient waiting times and total visit durations.
* Identify bottlenecks and delays between clinical activities.
* Detect repeated activities and process loops.
* Discover common clinical pathways using process mining techniques.
* Develop an interactive dashboard to visualize analytical results.
* Generate reports and actionable insights from the analysis.

## 🛠️ Technologies Used

| Technology          | Purpose                                |
| ------------------- | -------------------------------------- |
| Python              | Data processing and analysis           |
| Pandas              | Data cleaning and manipulation         |
| NumPy               | Numerical computations                 |
| PM4Py               | Process mining and process discovery   |
| SQLite              | Local data storage, if required        |
| Streamlit           | Interactive dashboard development      |
| Matplotlib / Plotly | Data visualization                     |
| Git and GitHub      | Version control and project management |

*The technology stack may be adjusted based on project requirements and implementation progress.*

## 📂 Project Structure

```text
careflow-clinical-process-mining/
│
├── data/
│   ├── raw/                   # Original event log data
│   └── processed/             # Cleaned and processed data
│
├── notebooks/
│   └── exploratory_analysis.ipynb
│
├── src/
│   ├── generate_data.py       # Generate synthetic event data
│   ├── clean_data.py          # Clean and validate event logs
│   ├── analyze_process.py     # Process discovery and pathway analysis
│   └── bottleneck_analysis.py # Waiting-time and bottleneck analysis
│
├── dashboard/
│   └── app.py                 # Streamlit dashboard
│
├── reports/                   # Project reports and findings
│
├── tests/                     # Project tests
│
├── requirements.txt           # Python dependencies
├── README.md
└── .gitignore
```

*This is the proposed project structure. Files and folders will be added as development progresses.*

## 📊 Dataset Description

CareFlow works with event log data that records the activities associated with each patient visit.

The dataset can contain the following fields:

| Column      | Description                                                            |
| ----------- | ---------------------------------------------------------------------- |
| `case_id`   | Unique identifier for a patient visit                                  |
| `activity`  | Clinical or administrative activity                                    |
| `timestamp` | Date and time when an activity occurred                                |
| `resource`  | Department or staff category associated with an activity, if available |

### Example Event Log

| case_id | activity            | timestamp           |
| ------- | ------------------- | ------------------- |
| CASE001 | Registration        | 2026-10-10 09:00:00 |
| CASE001 | Triage              | 2026-10-10 09:10:00 |
| CASE001 | Doctor Consultation | 2026-10-10 09:30:00 |
| CASE001 | Laboratory Test     | 2026-10-10 09:45:00 |
| CASE001 | Doctor Consultation | 2026-10-10 10:15:00 |
| CASE001 | Discharge           | 2026-10-10 10:30:00 |

This example illustrates a possible patient pathway. The repeated consultation activity can be examined to understand the sequence of care, but repetition alone does not establish that a clinical process is inefficient.

**Data privacy:** Development and testing will use synthetic data or properly authorized, de-identified data. Personally identifiable patient information will not be included in the public repository.

## 🔍 Key Analytical Features

### 1. Data Preprocessing

* Handle missing values and duplicate records.
* Standardize activity names and timestamps.
* Validate event sequences.
* Organize records by case identifier and timestamp.

### 2. Clinical Pathway Analysis

* Identify common sequences of clinical activities.
* Compare pathways across patient visits.
* Examine repeated activities and process loops.

### 3. Waiting-Time Analysis

* Calculate time differences between consecutive activities.
* Estimate total visit duration.
* Identify transitions with comparatively long delays.

### 4. Process Mining

* Discover process models from event logs.
* Visualize activity transitions.
* Explore deviations from a defined reference pathway, when one is available.

### 5. Interactive Dashboard

The planned dashboard may include:

* Total patient visits.
* Average and median waiting times.
* Average total visit duration.
* Most frequent clinical pathways.
* Activity-transition analysis.
* Repeated-activity and process-loop analysis.
* Potential bottlenecks and workflow deviations.

The dashboard features will be implemented and documented as development progresses.

## 🚀 Implementation Plan

| Phase   | Activities                                                                 |
| ------- | -------------------------------------------------------------------------- |
| Phase 1 | Repository setup, synthetic data generation, and exploratory data analysis |
| Phase 2 | Data cleaning, validation, and event log preparation                       |
| Phase 3 | Process discovery, pathway analysis, and waiting-time calculations         |
| Phase 4 | Bottleneck analysis and dashboard development                              |
| Phase 5 | Testing, documentation, final report, and project presentation             |

## ⚙️ Installation and Setup

### Prerequisites

* Python 3.10 or a compatible version supported by the selected dependencies
* Git
* A code editor such as Visual Studio Code

### Step 1: Clone the Repository

```bash
git clone https://github.com/AP24110011714/careflow-clinical-process-mining.git
```

### Step 2: Open the Project Directory

```bash
cd careflow-clinical-process-mining
```

### Step 3: Create a Virtual Environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

### Step 4: Install Dependencies

Once `requirements.txt` has been created and populated:

```bash
pip install -r requirements.txt
```

### Step 5: Run the Application

After the Streamlit dashboard has been implemented:

```bash
streamlit run dashboard/app.py
```

*These are the planned setup instructions. The commands will be fully usable once the corresponding repository files and dependencies are in place.*

## 📈 Expected Outcomes

The project aims to produce:

* A clean and validated clinical event log.
* An analysis of common patient-care pathways.
* Waiting-time and visit-duration statistics.
* Identification of potential workflow bottlenecks.
* Visual representations of discovered processes.
* An interactive dashboard for exploring analytical results.
* Technical documentation, a final report, and a project presentation.

The findings will depend on the quality of the data and the analyses performed. Identified delays or deviations will require appropriate interpretation rather than being treated automatically as evidence of poor clinical care.

## 🎓 Internship Information

* **Organization:** Infotact Solutions
* **Role:** Data Associate L1 Intern
* **Domain:** Data Analytics
* **Project Title:** CareFlow: Clinical Pathway Process Mining
* **Project Start Date:** 10 October 2026

## 🔮 Future Enhancements

* Integrate additional authorized healthcare event datasets.
* Add interactive process maps and pathway comparisons.
* Implement conformance checking against a defined reference process.
* Add configurable filters for activities and visit durations.
* Improve dashboard usability and reporting.
* Explore additional process performance indicators.

## 👩‍💻 Author

**Sravana Bandi**

B.Tech Computer Science and Engineering Student
SRM University–AP

GitHub: [AP24110011714](https://github.com/AP24110011714)

## 📄 Disclaimer

This project is developed for educational and data analytics purposes as part of an internship project. It is intended to analyze operational workflows and does not provide medical diagnoses or treatment recommendations.

---

**Project Status:** In Development
**Last Updated:** October 2026
