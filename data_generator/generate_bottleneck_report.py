import pandas as pd
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_DIR / "outputs" / "process_mining"
OUTPUT_DIR = PROJECT_DIR / "documentation"

VISIT_FILE = INPUT_DIR / "patient_visit_duration.csv"
TRANSITION_FILE = INPUT_DIR / "transition_performance.csv"
ACTIVITY_FILE = INPUT_DIR / "activity_frequency.csv"

REPORT_FILE = OUTPUT_DIR / "bottleneck_analysis_report.txt"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    visits = pd.read_csv(VISIT_FILE)
    transitions = pd.read_csv(TRANSITION_FILE)
    activities = pd.read_csv(ACTIVITY_FILE)

    required_transition_columns = {
        "from_activity",
        "to_activity",
        "transition_count",
        "average_wait_minutes",
        "median_wait_minutes",
        "maximum_wait_minutes",
    }

    if not required_transition_columns.issubset(transitions.columns):
        raise ValueError("Transition CSV is missing required columns.")

    report = []

    report.append("=" * 65)
    report.append("CAREFLOW: CLINICAL PATHWAY PROCESS MINING")
    report.append("BOTTLENECK ANALYSIS REPORT")
    report.append("=" * 65)
    report.append(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    report.append("")

    # Patient visit statistics
    report.append("1. PATIENT VISIT DURATION")
    report.append("-" * 65)

    if not visits.empty:
        durations = visits["duration_minutes"].dropna()

        report.append(f"Total patient visits: {len(visits)}")

        if not durations.empty:
            report.append(
                f"Average visit duration: {durations.mean():.2f} minutes"
            )
            report.append(
                f"Median visit duration: {durations.median():.2f} minutes"
            )
            report.append(
                f"Longest visit duration: {durations.max():.2f} minutes"
            )
            report.append(
                f"Shortest visit duration: {durations.min():.2f} minutes"
            )
    else:
        report.append("No patient visit records were found.")

    report.append("")

    # Slowest transitions
    report.append("2. SLOWEST ACTIVITY TRANSITIONS")
    report.append("-" * 65)

    if not transitions.empty:
        slowest = transitions.sort_values(
            "average_wait_minutes", ascending=False
        ).head(10)

        for rank, (_, row) in enumerate(slowest.iterrows(), start=1):
            report.append(
                f"{rank}. {row['from_activity']} -> {row['to_activity']}"
            )
            report.append(
                f"   Average: {row['average_wait_minutes']:.2f} minutes"
            )
            report.append(
                f"   Median: {row['median_wait_minutes']:.2f} minutes"
            )
            report.append(
                f"   Maximum: {row['maximum_wait_minutes']:.2f} minutes"
            )
            report.append(
                f"   Observed transitions: {int(row['transition_count'])}"
            )
            report.append("")
    else:
        report.append("No valid transitions were found.")
        report.append("")

    # Most frequent activities
    report.append("3. MOST FREQUENT ACTIVITIES")
    report.append("-" * 65)

    if not activities.empty:
        for _, row in activities.sort_values(
            "event_count", ascending=False
        ).head(10).iterrows():
            report.append(
                f"{row['activity']}: {int(row['event_count'])} events "
                f"across {int(row['patient_visits'])} visits"
            )
    else:
        report.append("No activity frequency records were found.")

    report.append("")

    # Interpretation guidance
    report.append("4. INTERPRETATION AND RECOMMENDATIONS")
    report.append("-" * 65)
    report.append(
        "• Long average transition times indicate candidate areas for review."
    )
    report.append(
        "• Check the median alongside the average to identify the effect "
        "of unusually long waits."
    )
    report.append(
        "• Review transition counts before prioritizing a bottleneck."
    )
    report.append(
        "• Frequent activities are not necessarily bottlenecks."
    )
    report.append(
        "• Validate findings with clinical workflow experts before "
        "recommending operational changes."
    )
    report.append(
        "• This report uses synthetic or project-provided event data; "
        "findings should not be treated as verified hospital outcomes."
    )

    REPORT_FILE.write_text("\n".join(report), encoding="utf-8")

    print("Bottleneck report generated successfully!")
    print(f"Report location: {REPORT_FILE}")


if __name__ == "__main__":
    main()
