import os
import pandas as pd

FILE = "data/processed/clean_log.csv"   # EDIT to your cleaned file
CASE, ACTIVITY, TIME = "case_id", "activity", "timestamp"   # EDIT if different

df = pd.read_csv(FILE, parse_dates=[TIME])
df = df.sort_values([CASE, TIME])

# Pair each event with the next event in the same case
df["next_activity"] = df.groupby(CASE)[ACTIVITY].shift(-1)
df["next_time"] = df.groupby(CASE)[TIME].shift(-1)
steps = df.dropna(subset=["next_activity"]).copy()
steps["wait_minutes"] = (steps["next_time"] - steps[TIME]).dt.total_seconds() / 60

# Summarize each transition (from -> to)
summary = steps.groupby([ACTIVITY, "next_activity"])["wait_minutes"].agg(
    count="count", mean="mean", median="median",
    p90=lambda s: s.quantile(0.9), max="max"
).round(2).reset_index()
summary.columns = ["from", "to", "count", "mean_min", "median_min", "p90_min", "max_min"]
summary = summary.sort_values("mean_min", ascending=False)

print("Slowest 10 transitions (by average wait):")
print(summary.head(10).to_string(index=False))

os.makedirs("data/processed", exist_ok=True)
summary.to_csv("data/processed/transition_waiting_times.csv", index=False)
