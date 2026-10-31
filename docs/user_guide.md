# CareFlow User Guide

CareFlow analyzes a hospital event log to show common patient pathways,
waiting times, repeated steps and how closely cases follow an expected order.

## 1. Setup
```bash
git clone https://github.com/AP24110011714/infotact-internship.git
cd infotact-internship
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Run the analysis (in this order)
| Step | Command | Result |
| --- | --- | --- |
| 1 | `python data_cleaning.py` | Cleaned event log in `data/processed/` |
| 2 | `python variants_analysis.py` | `variants.csv` |
| 3 | `python main.py` | Directly-follows graph |
| 4 | `python case_duration.py` | `case_durations.csv` |
| 5 | `python Waiting_time.py` | `transition_waiting_times.csv` |
| 6 | `python rework_analysis.py` | `rework_summary.csv` |
| 7 | `python conformance_check.py` | `conformance_results.csv` |
| 8 | `python export_findings.py` | `docs/findings.md` |

## 3. Open the dashboard
```bash
streamlit run dashboard/app.py
```
The dashboard opens in your browser at http://localhost:8501.
Press Ctrl + C in the terminal to stop it.

## 4. Using the dashboard
- **KPI cards:** total cases, median case duration, unique variants and the
  share of cases with repeated activities.
- **Variants chart:** the most common patient pathways. Use the slider to
  choose how many to show.
- **Slowest transitions:** average waiting time between two consecutive steps.
  Raise the minimum-cases number to hide rare transitions.
- **Conformance:** how many cases follow the expected order of key steps, and
  the most common deviations.
- **Sidebar filters:** limit cases by duration and transitions by activity.
  The variants chart is not affected by the duration filter because it is
  already summarized.

## 5. Reading the results
Long waits and repeated steps are signals to examine, not proof of poor
care. Some repeats are clinically needed.

## 6. Run the tests
```bash
python -m pytest tests -v
```

## 7. Troubleshooting
- **File not found:** run commands from the repository's main folder.
- **Module not found:** run `pip install -r requirements.txt`.
- **Empty dashboard tables:** run the analysis scripts first so the CSV files exist.
