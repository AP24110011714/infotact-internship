from pathlib import Path

import pandas as pd


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CLEANED_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "hospital_event_log_clean.csv"
)

TRANSITIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "activity_transitions.csv"
)

REPORT_PATH = (
    PROJECT_ROOT
    / "documentation"
    / "process_analysis_report.md"
)


def main():
    # Check input files
    if not CLEANED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found: {CLEANED_DATA_PATH}"
        )

    if not TRANSITIONS_PATH.exists():
        raise FileNotFoundError(
            f"Transitions file not found: {TRANSITIONS_PATH}"
        )

    # Load datasets
    events = pd.read_csv(CLEANED_DATA_PATH)
    transitions = pd.read_csv(TRANSITIONS_PATH)

    # Check required event-log columns
    required_event_columns = {
        "case_id",
        "activity",
        "timestamp",
    }

    missing_event_columns = (
        required_event_columns - set(events.columns)
    )

    if missing_event_columns:
        raise ValueError(
            f"Missing event-log columns: {missing_event_columns}"
        )

    # Check columns used by the existing transition CSV
    required_transition_columns = {
        "current_activity",
        "next_activity",
        "transition",
        "case_count",
        "average_waiting_minutes",
        "median_waiting_minutes",
        "maximum_waiting_minutes",
    }

    missing_transition_columns = (
        required_transition_columns - set(transitions.columns)
    )

    if missing_transition_columns:
        raise ValueError(
            "Missing transition columns: "
            f"{missing_transition_columns}"
        )

    # Prepare the event log
    events["timestamp"] = pd.to_datetime(
        events["timestamp"],
        errors="coerce",
    )

    events = events.dropna(
        subset=["case_id", "activity", "timestamp"]
    )

    events = events.sort_values(
        ["case_id", "timestamp"]
    ).reset_index(drop=True)

    # Dataset summary
    total_visits = events["case_id"].nunique()
    total_events = len(events)

    # Find visits containing X-Ray
    xray_cases = set(
        events.loc[
            events["activity"] == "X-Ray",
            "case_id",
        ].unique()
    )

    # Find visits where Triage occurs after X-Ray
    loopback_cases = set()

    for case_id, group in events.groupby("case_id", sort=False):
        activities = group["activity"].tolist()

        xray_positions = [
            index
            for index, activity in enumerate(activities)
            if activity == "X-Ray"
        ]

        for position in xray_positions:
            later_activities = activities[position + 1:]

            if "Triage" in later_activities:
                loopback_cases.add(case_id)
                break

    xray_count = len(xray_cases)
    loopback_count = len(loopback_cases)

    loopback_percentage = (
        loopback_count / xray_count * 100
        if xray_count > 0
        else 0.0
    )

    # Select the five transitions with the highest average elapsed time
    top_transitions = transitions.sort_values(
        "average_waiting_minutes",
        ascending=False,
    ).head(5)

    # Build the report
    report_lines = [
        "# CareFlow: Clinical Pathway Process Mining",
        "",
        "## 1. Project Overview",
        "",
        (
            "CareFlow uses a synthetic hospital event log to examine "
            "patient pathways, event transitions, elapsed time between "
            "activities, and potential process bottlenecks."
        ),
        "",
        "## 2. Dataset Summary",
        "",
        f"- Patient visits: {total_visits:,}",
        f"- Cleaned event records: {total_events:,}",
        f"- Visits containing X-Ray: {xray_count:,}",
        "",
        "## 3. X-Ray-to-Triage Loop-Back Analysis",
        "",
        f"- Visits containing X-Ray: {xray_count:,}",
        f"- Visits with Triage after X-Ray: {loopback_count:,}",
        f"- Loop-back rate among X-Ray visits: {loopback_percentage:.2f}%",
        "",
        (
            "Interpretation: the synthetic dataset models a repeated "
            "Triage step after X-Ray for a subset of visits. In a real "
            "hospital, this pattern could be investigated for causes "
            "such as missing paperwork, incomplete documentation, or "
            "clinical reassessment. The synthetic data does not establish "
            "the actual cause of a loop-back."
        ),
        "",
        "## 4. Transitions With the Highest Average Elapsed Time",
        "",
        (
            "The following transitions have the highest average elapsed "
            "time between consecutive recorded activities."
        ),
        "",
        (
            "| Transition | Event count | Average elapsed minutes "
            "| Median elapsed minutes |"
        ),
        "|---|---:|---:|---:|",
    ]

    for _, row in top_transitions.iterrows():
        transition_name = row["transition"]
        event_count = int(row["case_count"])
        average_minutes = float(
            row["average_waiting_minutes"]
        )
        median_minutes = float(
            row["median_waiting_minutes"]
        )

        report_lines.append(
            f"| {transition_name} "
            f"| {event_count} "
            f"| {average_minutes:.2f} "
            f"| {median_minutes:.2f} |"
        )

    report_lines.extend(
        [
            "",
            "## 5. Interpretation and Limitations",
            "",
            (
                "Elapsed time between consecutive event timestamps is "
                "not necessarily queue waiting time. It can include "
                "service time, waiting time, and other delays. The current "
                "dataset does not record separate activity start and "
                "completion timestamps."
            ),
            "",
            (
                "The data is synthetic and is intended for process-mining "
                "practice. The results should not be interpreted as "
                "findings about a real hospital."
            ),
            "",
            "## 6. Recommended Next Steps",
            "",
            "- Load the cleaned event log into BigQuery.",
            "- Build standardized event-log models using dbt.",
            "- Discover the process model using PM4Py.",
            "- Build a dashboard to explore transitions and elapsed times.",
            "- Add tests for data quality and process conformance.",
            "",
        ]
    )

    # Ensure the documentation folder exists
    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Save the report
    REPORT_PATH.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    # Display summary
    print("=" * 60)
    print("CAREFLOW - PROCESS ANALYSIS REPORT")
    print("=" * 60)
    print(f"Patient visits: {total_visits:,}")
    print(f"Cleaned events: {total_events:,}")
    print(f"Visits containing X-Ray: {xray_count:,}")
    print(f"Visits with Triage after X-Ray: {loopback_count:,}")
    print(f"X-Ray-to-Triage loop-back rate: {loopback_percentage:.2f}%")
    print()
    print(f"Report saved to: {REPORT_PATH}")
    print("Report generated successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()