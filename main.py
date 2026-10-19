pip install pm4py
import os
import pandas as pd
import pm4py

FILE = "data/processed/clean_log.csv"   # EDIT to your cleaned file
CASE, ACTIVITY, TIME = "case_id", "activity", "timestamp"   # EDIT if different

df = pd.read_csv(FILE, parse_dates=[TIME])
df = pm4py.format_dataframe(df, case_id=CASE, activity_key=ACTIVITY, timestamp_key=TIME)

dfg, start, end = pm4py.discover_dfg(df)

edges = pd.DataFrame([(a, b, c) for (a, b), c in dfg.items()],
                     columns=["from", "to", "count"]).sort_values("count", ascending=False)
print(edges.head(15).to_string(index=False))
edges.to_csv("data/processed/dfg_edges.csv", index=False)

os.makedirs("outputs", exist_ok=True)
pm4py.save_vis_dfg(dfg, start, end, "outputs/dfg.png")
