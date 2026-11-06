# CareFlow Process Mining: Clinical Pathway Findings

**Infotact Solutions Internship (Batch 22.1) — Healthcare Operations Intelligence**

---

## 1. Executive Summary

Traditional BI reports reported an average emergency room dwell time of ~180 minutes but could not explain why patients experienced severe bottlenecks. Applying process mining (PM4Py) directly to chronological event logs revealed that **40.2% of patients receiving an X-Ray (1,217 patients) were redirected backwards to Triage due to missing intake paperwork**.

---

## 2. Ingestion & Process Discovery Metrics

- **Total Chronological Event Records:** 32,981
- **Total Unique Patient Cases:** 5,000
- **Average Event Sequence per Patient:** 6.6 steps
- **Unique Process Activities Discovered:** 8
- **Unique Process Transitions Discovered:** 12
- **Directly Follows Graph (DFG):** 100% discovered and mapped in SVG Spaghetti format.
- **Formal Petri Net:** 10 Places, 13 Transitions (8 visible, 5 silent), 26 Arcs (Inductive Miner WFN).

---

## 3. Transition Bottlenecks & Operational Friction

| Transition | Count | Mean Wait (min) | Median Wait (min) | P90 Wait (min) | Hours Lost | Friction Source |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Lab Tests $\rightarrow$ Doctor Consultation** | 3,456 | **68.48** | 67.62 | 97.79 | 3,944.4 | Lab Turnaround / Physician Availability |
| **X-Ray $\rightarrow$ Doctor Consultation** | 578 | **64.08** | 63.72 | 90.80 | 617.3 | Imaging Report Delay |
| **Triage $\rightarrow$ Doctor Consultation** | 966 | **54.50** | 53.80 | 80.57 | 877.4 | Acute Physician Waiting Queue |
| **X-Ray $\rightarrow$ Lab Tests** | 1,230 | **51.17** | 50.93 | 69.35 | 1,049.0 | Departmental Transfer Delay |
| **Doctor Consult $\rightarrow$ Doctor Review** | 283 | **44.81** | 44.55 | 61.35 | 211.4 | Rework / Senior Review Wait |
| **Triage $\rightarrow$ Lab Tests** | 2,226 | **43.64** | 43.28 | 60.89 | 1,619.0 | Phlebotomy Queue |
| **Treatment $\rightarrow$ Discharge** | 5,000 | **42.70** | 42.58 | 59.07 | 3,558.3 | Bed Clearance & Discharge Summary |
| **Doctor Consult $\rightarrow$ Treatment** | 4,717 | **35.52** | 35.23 | 48.31 | 2,792.5 | Medication & Nursing Orders |
| **Doctor Review $\rightarrow$ Treatment** | 283 | **31.40** | 31.47 | 43.03 | 148.1 | Post-Review Execution |
| **X-Ray $\rightarrow$ Triage (LOOPBACK)** | **1,217** | **29.29** | **28.92** | **39.44** | **594.1** | **Missing Paperwork Form (Key Bottleneck)** |
| **Triage $\rightarrow$ X-Ray** | 3,025 | **28.60** | 28.30 | 40.21 | 1,441.9 | Radiography Preparation |
| **Registration $\rightarrow$ Triage** | 5,000 | **17.12** | 17.00 | 24.52 | 1,426.7 | Initial Intake Registration |

---

## 4. Top Discovered Patient Variants

1. **Variant 1 (24.7%):** `Registration → Triage → Lab Tests → Doctor Consultation → Treatment → Discharge`
2. **Variant 2 (22.7%):** `Registration → Triage → X-Ray → Lab Tests → Doctor Consultation → Treatment → Discharge`
3. **Variant 3 (16.1% — Non-Compliant):** `Registration → Triage → X-Ray → Triage → Lab Tests → Doctor Consultation → Treatment → Discharge`
4. **Variant 4 (12.5%):** `Registration → Triage → Doctor Consultation → Treatment → Discharge`
5. **Variant 5 (11.6%):** `Registration → Triage → X-Ray → Doctor Consultation → Treatment → Discharge`
6. **Variant 6 (6.8% — Non-Compliant):** `Registration → Triage → X-Ray → Triage → Doctor Consultation → Treatment → Discharge`
7. **Variants 7–9 (5.7%):** Specialized pathways involving double physician review and rework.

---

## 5. Clinical Protocol Conformance

- **Institutional Compliance Rate:** **75.66%**
- **Average Patient Fitness Score:** **0.915 / 1.00**
- **Root Cause of Non-Conformance:** 100% of non-compliant traces were triggered by administrative loopbacks (missing intake paperwork).
- **Target Operational Benefit:** Automating electronic form completion upon triage eliminates the loopback, instantly saving **20 minutes per patient** and **594+ hours annually**.
