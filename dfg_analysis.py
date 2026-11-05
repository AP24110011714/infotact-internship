"""Directly-follows graph: how often step A is directly followed by step B."""
import sys
import pandas as pd

PATH = "data/processed/clean_log.csv"
try:
    df = pd.read_csv(PATH, parse_dates=["timestamp"])
except FileNotFoundError:
    sys.exit(f"{PATH} not found. Build the event log first (case_id, activity, timestamp).")

df = df.sort_values(["case_id", "timestamp"])
df["next_activity"] = df.groupby("case_id")["activity"].shift(-1)
df["wait_min"] = (df.groupby("case_id")["timestamp"].shift(-1) - df["timestamp"]).dt.total_seconds() / 60

edges = (df.dropna(subset=["next_activity"])
           .groupby(["activity", "next_activity"])
           .agg(count=("case_id", "size"), mean_wait_min=("wait_min", "mean"))
           .reset_index()
           .sort_values("count", ascending=False))
edges["mean_wait_min"] = edges["mean_wait_min"].round(1)

print(edges.to_string(index=False))
edges.to_csv("outputs/dfg_edges.csv", index=False)
