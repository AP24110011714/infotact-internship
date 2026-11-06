# CareFlow: Clinical Pathway Process Mining

**Infotact Solutions Internship — Project 3: Clinical Process Mining**  
*Healthcare Operations & Process Analytics • Batch 22.1*

[![PM4Py](https://img.shields.io/badge/PM4Py-2.7.23-blue.svg)](https://pm4py.fit.fraunhofer.de/)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Modern Data Stack](https://img.shields.io/badge/MDS-BigQuery%20%7C%20dbt-orange.svg)](https://cloud.google.com/bigquery)
[![Tests](https://img.shields.io/badge/tests-7%20passed-brightgreen.svg)]()

---

## 🎯 Problem Statement & Executive Summary

Hospital administrators often struggle to identify why Emergency Room (ER) wait times are so severe. Standard BI dashboards only display high-level "average wait times," but they fail to map the chaotic, real-world sequence of events patients actually experience.

**CareFlow** applies **Process Mining algorithms (PM4Py)** directly to raw, chronological Electronic Health Record (EHR) event logs. By visualizing the hospital's actual "As-Is" flow via **Directly Follows Graphs (DFG / Spaghetti Diagrams)**, CareFlow exposed a major hidden bottleneck:

> ⚠️ **Key Finding:** **40.2% of patients receiving X-Rays (1,217 patients)** are sent backwards to **Triage** due to an incomplete intake paperwork form. This administrative rework costs **594.1 lost operational hours** and inflates ER wait times. Fixing the intake form instantly recovers **~20 minutes per patient**.

---

## 🏗️ Architecture & Technology Stack

CareFlow adheres strictly to the **Modern Data Stack (MDS)** for healthcare operations:

```
[ Raw EHR System ]
        │
        ▼ (Simulated 5,000 Cases, 32,981 Events)
[ Google BigQuery Warehouse ]  (Partitioned by DATE, Clustered by case_id)
        │
        ▼
[ dbt Transformation Layer ]   (Strict Schema: Case_ID, Activity, Timestamp, Resource)
        │
        ▼
[ PM4Py Mining Engine ]         (DFG Discovery, Transition Bottlenecks, Conformance)
        │
        ▼
[ Process Dashboard ]          (Spaghetti Diagram, Bottleneck Heatmap, Variants)
```

- **Data Warehouse (Google BigQuery):** Highly performant chronological storage, partitioned by event timestamp and clustered by `case_id` and `activity` (`mining/bigquery_loader.py`, `data/processed/bigquery_schema.sql`).
- **Data Transformation (dbt):** Ingestion and standardization layer cleaning raw logs into standard event log format (`dbt_transform/clean_event_log.py`).
- **Process Mining Engine (PM4Py):** Algorithmic discovery of the hospital Directed Follows Graph, transition matrices, variants, and conformance checking (`mining/`).
- **Process Dashboard:** 
  1. Standalone interactive model with animated SVG Spaghetti Diagram (`careflow_prototype.html`).
  2. Streamlit interactive operations dashboard (`dashboard/app.py`).

---

## 📅 4-Week Development Plan & Milestones

| Week | Phase | Module & Deliverable | Status |
|:---:|:---|:---|:---:|
| **Week 1** | **Event Log Simulation & Warehouse** | Python script generating 5,000 mock cases (32,981 events) with deliberate loopbacks; BigQuery DDL & local warehouse loader. | ✅ **Complete** |
| **Week 2** | **Normalization & Process Discovery** | dbt models standardizing schema (`case_id`, `activity`, `timestamp`); PM4Py algorithmic discovery of the As-Is DFG. | ✅ **Complete** |
| **Week 3** | **Bottleneck Calculations & BI** | Transition time calculation (mean, median, P90 wait times between all 12 nodes); interactive Spaghetti Diagram with bottleneck highlight. | ✅ **Complete** |
| **Week 4** | **Conformance Checking & Polish** | Algorithmic trace conformance checking against ideal hospital journey; variant frequency analysis; multi-modal drilldowns. | ✅ **Complete** |

---

## 📊 Key Operational Findings

1. **Volume:** 5,000 patient admissions, 32,981 total chronological events.
2. **Missing Paperwork Bottleneck:** 
   - 3,025 patients underwent X-Ray examination.
   - **1,217 patients (40.2%)** were routed back to Triage instead of advancing to Doctor Consultation.
   - Delay per loopback: **29.3 minutes average wait** (594.1 total hours lost).
3. **Doctor Consultation Bottlenecks:**
   - Waiting for Doctor Consultation following Lab Tests averaged **68.5 minutes** (3,456 cases, 3,944 hours lost).
   - Waiting for Doctor Consultation after X-Ray averaged **64.1 minutes** (578 cases, 617 hours lost).
4. **Institutional Compliance:**
   - Overall compliance rate: **75.66%**.
   - Average trace fitness score: **0.915 / 1.00**.

---

## 🚀 Quickstart & Execution

### 1. Installation
```powershell
# Clone the repository
git clone https://github.com/AP24110011714/infotact-internship.git
cd infotact-internship

# Install dependencies
python -m pip install -r requirements.txt
```

### 2. Run the Full Process Mining Pipeline
Run the master orchestrator to execute all 4 weeks of the pipeline:
```powershell
python run_pipeline.py
```

### 3. Open the Interactive Process Mining Dashboard
- **Web Prototype (Spaghetti Diagram):** Open `careflow_prototype.html` directly in any web browser.
- **Streamlit App:**
```powershell
streamlit run dashboard/app.py
```

### 4. Run Unit Tests
```powershell
python -m pytest -v
```

---

## 📂 Project Structure

```
infotact-internship/
├── careflow_prototype.html       # Real-world interactive Process Mining Dashboard (SVG Spaghetti Diagram)
├── generate_event_log.py         # Week 1: 5,000-case EHR chronological event generator
├── run_pipeline.py               # Master end-to-end 4-week pipeline orchestrator
├── build_process_dashboard.py    # Process Mining HTML dashboard generator
│
├── dbt_transform/                # Week 2: dbt Transformation Layer
│   └── clean_event_log.py        # Normalizes raw logs into standard PM4Py format
│
├── mining/                       # Weeks 2-4: PM4Py Process Mining Modules
│   ├── discover.py               # Discovers As-Is DFG, nodes, and transition counts
│   ├── bottlenecks.py            # Computes transition wait times (mean, median, P90, lost hours)
│   ├── variants.py               # Discovers all distinct patient pathways (variants)
│   ├── conformance.py            # Conformance checking against ideal clinical protocol
│   └── bigquery_loader.py        # BigQuery DDL schema generator and warehouse staging
│
├── dashboard/
│   └── app.py                    # Streamlit operational & clinical dashboard
│
├── data/
│   ├── raw/
│   │   └── ehr_events.csv        # 32,981 raw chronological EHR events
│   └── processed/
│       ├── ehr_events_clean.csv  # dbt normalized event log
│       ├── dfg_edges.csv         # DFG transition frequencies
│       ├── bottlenecks.csv       # Transition wait times & bottleneck analysis
│       ├── variants.csv          # Discovered process variants
│       ├── conformance.csv       # Case-by-case conformance scores
│       └── bigquery_schema.sql   # Production BigQuery partitioned DDL
│
└── tests/
    └── test_pipeline.py          # Comprehensive pytest test suite (7 passed)
```

---

## 👥 Contributors & Internship Details

- **Intern:** Abhinandan Naik
- **Role:** Data Engineering & Analytics Intern
- **Program:** Infotact Solutions Internship (Batch 22.1)
- **Domain:** Healthcare Operations & Clinical Process Mining
