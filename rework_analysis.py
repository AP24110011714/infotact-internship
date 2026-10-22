import os
import pandas as pd

FILE = "data/processed/clean_log.csv"   # EDIT to your cleaned file
CASE, ACTIVITY, TIME = "case_id", "activity", "timestamp"   # EDIT if different

df = pd.read_csv(FILE, parse_dates=[TIME])
df = df.sort_values([CASE, TIME])

# How many times each activity occurs in each case
counts = df.groupby([CASE, ACTIVITY]).size().reset_index(name="occurrences")
repeats = counts[counts["occurrences"] > 1]

total_cases = df[CASE].nunique()
cases_with_rework = repeats[CASE].nunique()
print("Total cases:", total_cases)
print("Cases with at least one repeated activity:", cases_with_rework,
      f"({cases_with_rework / total_cases * 100:.1f}%)")

# Which activities are repeated most often
by_activity = repeats.groupby(ACTIVITY).agg(
    cases_repeating=(CASE, "nunique"),
    extra_occurrences=("occurrences", lambda s: (s - 1).sum()),
).sort_values("cases_repeating", ascending=False).reset_index()
by_activity["percent_of_cases"] = (by_activity["cases_repeating"] / total_cases * 100).round(2)

print("Most repeated activities:")
print(by_activity.head(10).to_string(index=False))

# Direct loop-backs: an activity followed immediately by itself
df["next_activity"] = df.groupby(CASE)[ACTIVITY].shift(-1)
immediate = df[df[ACTIVITY] == df["next_activity"]]
print("Immediate repeats (A -> A):", len(immediate))

os.makedirs("data/processed", exist_ok=True)
repeats.to_csv("data/processed/repeated_activities_by_case.csv", index=False)
by_activity.to_csv("data/processed/rework_summary.csv", index=False)
