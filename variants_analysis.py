import pandas as pd

# EDIT THESE to match your cleaned file
FILE = "data/processed/clean_log.csv"
CASE, ACTIVITY, TIME = "case_id", "activity", "timestamp"

df = pd.read_csv(FILE, parse_dates=[TIME])
df = df.sort_values([CASE, TIME])

# One row per case: its full sequence of activities
paths = df.groupby(CASE)[ACTIVITY].apply(lambda s: " -> ".join(s))
variants = paths.value_counts().reset_index()
variants.columns = ["variant", "cases"]
variants["percent"] = (variants["cases"] / variants["cases"].sum() * 100).round(2)

print("Total cases:", paths.shape[0])
print("Unique variants:", variants.shape[0])
print(variants.head(10).to_string(index=False))

variants.to_csv("data/processed/variants.csv", index=False)
