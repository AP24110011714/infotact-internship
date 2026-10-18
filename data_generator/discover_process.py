from pathlib import Path

import pandas as pd
import pm4py


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "processed" / "hospital_event_log_clean.csv"
OUTPUT_DIR = BASE_DIR / "outputs" / "process_mining"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("CareFlow - Patient Process Discovery")
    print("-" * 40)

    # 1. Check the input file
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Cleaned event log not found: {INPUT_FILE}"
        )

    # 2. Load the cleaned event log
    df = pd.read_csv(INPUT_FILE)

    required_columns = {"case_id", "activity", "timestamp"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    # 3. Prepare the event data
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

    if df.empty:
        raise ValueError("No valid events remain after cleaning.")

    print(f"Valid events: {len(df):,}")
    print(f"Patient visits: {df['case_id'].nunique():,}")
    print(f"Unique activities: {df['activity'].nunique():,}")

    # 4. Convert the DataFrame into PM4Py format
    event_log = pm4py.format_dataframe(
        df,
        case_id="case_id",
        activity_key="activity",
        timestamp_key="timestamp"
    )

    # 5. Discover a Petri-net process model
    print("\nDiscovering the hospital process model...")

    net, initial_marking, final_marking = (
        pm4py.discover_petri_net_inductive(event_log)
    )

    print("Process model discovered successfully.")

    # 6. Export the process model
    output_file = OUTPUT_DIR / "careflow_process_model.png"

    pm4py.save_vis_petri_net(
        net,
        initial_marking,
        final_marking,
        str(output_file)
    )

    print(f"\nProcess model saved to:\n{output_file}")
    print("\nProcess discovery completed.")


if __name__ == "__main__":
    main()
