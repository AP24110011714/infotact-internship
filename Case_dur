import os
import pandas as pd

FILE = "data/processed/clean_log.csv"   # EDIT to your cleaned file
CASE, ACTIVITY, TIME = "case_id", "activity", "timestamp"   # EDIT if different

df = pd.read_csv(FILE, parse_dates=[TIME])
df = df.sort_values([CASE, TIME])

# One row per case: start, end, number of events, total duration
cases = df.groupby(CASE).agg(
    start=(TIME, "min"),
    end=(TIME, "max"),
    events=(ACTIVITY, "count"),
)
cases["duration_hours"] = ((cases["end"] - cases["start"]).dt.total_seconds() / 3600).round(2)

print("Total cases:", len(cases))
print("Average duration (hours):", round(cases["duration_hours"].mean(), 2))
print("Median duration (hours):", round(cases["duration_hours"].median(), 2))
print("90th percentile (hours):", round(cases["duration_hours"].quantile(0.9), 2))
print("Longest 10 cases:")
print(cases.sort_values("duration_hours", ascending=False).head(10).to_string())

os.makedirs("data/processed", exist_ok=True)
cases.reset_index().to_csv("data/processed/case_durations.csv", index=False)
