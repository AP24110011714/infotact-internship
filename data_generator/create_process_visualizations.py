import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Project directories
PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_DIR / "outputs" / "process_mining"
OUTPUT_DIR = INPUT_DIR / "visualizations"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load analysis results
activities = pd.read_csv(INPUT_DIR / "activity_frequency.csv")
transitions = pd.read_csv(INPUT_DIR / "transition_performance.csv")
visits = pd.read_csv(INPUT_DIR / "patient_visit_duration.csv")

# 1. Activity Frequency Chart
activities = activities.sort_values("event_count", ascending=True)

plt.figure(figsize=(10, 6))
plt.barh(activities["activity"], activities["event_count"])
plt.xlabel("Number of Events")
plt.ylabel("Hospital Activity")
plt.title("CareFlow: Activity Frequency")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "activity_frequency.png", dpi=300)
plt.close()

# 2. Slowest Activity Transitions
slowest = transitions.sort_values(
    "average_wait_minutes", ascending=False
).head(10).copy()

slowest["transition"] = (
    slowest["from_activity"].astype(str)
    + " -> "
    + slowest["to_activity"].astype(str)
)

slowest = slowest.sort_values("average_wait_minutes", ascending=True)

plt.figure(figsize=(12, 7))
plt.barh(slowest["transition"], slowest["average_wait_minutes"])
plt.xlabel("Average Waiting Time (Minutes)")
plt.ylabel("Activity Transition")
plt.title("CareFlow: Top 10 Slowest Activity Transitions")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "slowest_transitions.png", dpi=300)
plt.close()

# 3. Patient Visit Duration Distribution
durations = visits["duration_minutes"].dropna()

plt.figure(figsize=(10, 6))
plt.hist(durations, bins=20, edgecolor="black")
plt.xlabel("Visit Duration (Minutes)")
plt.ylabel("Number of Patient Visits")
plt.title("CareFlow: Patient Visit Duration Distribution")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "visit_duration_distribution.png", dpi=300)
plt.close()

print("All CareFlow visualizations created successfully!")
print(f"Charts saved in: {OUTPUT_DIR}")
print("1. activity_frequency.png")
print("2. slowest_transitions.png")
print("3. visit_duration_distribution.png")