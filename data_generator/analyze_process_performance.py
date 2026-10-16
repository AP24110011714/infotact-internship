import pandas as pd
from pathlib import Path

# --------------------------------------------------
# CareFlow: Process Performance Analysis
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "hospital_event_log_clean.csv"
)

OUTPUT_DIR = PROJECT_DIR / "outputs" / "process_mining"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 55)
    print("CAREFlow - PROCESS PERFORMANCE ANALYSIS")
    print("=" * 55)

    # 1. Load the cleaned event log
    df = pd.read_csv(INPUT_FILE)

    required_columns = ["case_id", "activity", "timestamp"]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # 2. Validate and prepare timestamps
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["case_id", "activity", "timestamp"]
    ).copy()

    df["case_id"] = df["case_id"].astype(str)
    df["activity"] = df["activity"].astype(str)

    df = df.sort_values(
        ["case_id", "timestamp"]
    ).reset_index(drop=True)

    print(f"\nValid events: {len(df):,}")
    print(f"Patient visits: {df['case_id'].nunique():,}")
    print(f"Unique activities: {df['activity'].nunique()}")

    # 3. Calculate patient visit duration
    visit_summary = (
        df.groupby("case_id")
        .agg(
            start_time=("timestamp", "min"),
            end_time=("timestamp", "max"),
            event_count=("activity", "size"),
            activity_count=("activity", "nunique")
        )
        .reset_index()
    )

    visit_summary["duration_minutes"] = (
        visit_summary["end_time"]
        - visit_summary["start_time"]
    ).dt.total_seconds() / 60

    visit_file = OUTPUT_DIR / "patient_visit_duration.csv"

    visit_summary.to_csv(visit_file, index=False)

    # 4. Calculate time between consecutive activities
    df["next_activity"] = (
        df.groupby("case_id")["activity"].shift(-1)
    )

    df["next_timestamp"] = (
        df.groupby("case_id")["timestamp"].shift(-1)
    )

    transitions = df.dropna(
        subset=["next_activity", "next_timestamp"]
    ).copy()

    transitions["transition_time_minutes"] = (
        transitions["next_timestamp"]
        - transitions["timestamp"]
    ).dt.total_seconds() / 60

    # Remove negative intervals, if any
    transitions = transitions[
        transitions["transition_time_minutes"] >= 0
    ].copy()

    transitions = transitions.rename(
        columns={
            "activity": "from_activity",
            "next_activity": "to_activity"
        }
    )

    # 5. Summarize transition performance
    transition_summary = (
        transitions.groupby(
            ["from_activity", "to_activity"]
        )
        .agg(
            transition_count=("case_id", "size"),
            patient_visits=("case_id", "nunique"),
            average_wait_minutes=(
                "transition_time_minutes", "mean"
            ),
            median_wait_minutes=(
                "transition_time_minutes", "median"
            ),
            maximum_wait_minutes=(
                "transition_time_minutes", "max"
            )
        )
        .reset_index()
    )

    transition_summary = transition_summary.sort_values(
        "average_wait_minutes",
        ascending=False
    )

    transition_file = (
        OUTPUT_DIR / "transition_performance.csv"
    )

    transition_summary.to_csv(
        transition_file,
        index=False
    )

    # 6. Calculate activity frequency
    activity_summary = (
        df.groupby("activity")
        .agg(
            event_count=("case_id", "size"),
            patient_visits=("case_id", "nunique")
        )
        .reset_index()
        .sort_values("event_count", ascending=False)
    )

    activity_file = OUTPUT_DIR / "activity_frequency.csv"

    activity_summary.to_csv(
        activity_file,
        index=False
    )

    # 7. Display key findings
    print("\n--- PATIENT VISIT DURATION ---")

    print(
        f"Average: "
        f"{visit_summary['duration_minutes'].mean():.2f} minutes"
    )

    print(
        f"Median: "
        f"{visit_summary['duration_minutes'].median():.2f} minutes"
    )

    print(
        f"Maximum: "
        f"{visit_summary['duration_minutes'].max():.2f} minutes"
    )

    print("\n--- TOP 10 SLOWEST TRANSITIONS ---")

    if not transition_summary.empty:
        print(
            transition_summary.head(10).to_string(
                index=False,
                formatters={
                    "average_wait_minutes": "{:.2f}".format,
                    "median_wait_minutes": "{:.2f}".format,
                    "maximum_wait_minutes": "{:.2f}".format
                }
            )
        )
    else:
        print("No valid consecutive activity transitions found.")

    print("\n--- OUTPUT FILES ---")
    print(visit_file)
    print(transition_file)
    print(activity_file)

    print("\nPerformance analysis completed successfully!")


if __name__ == "__main__":
    main()