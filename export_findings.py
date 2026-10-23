import os
import pandas as pd

P = "data/processed/"
dur = pd.read_csv(P + "case_durations.csv")
wait = pd.read_csv(P + "transition_waiting_times.csv")
var = pd.read_csv(P + "variants.csv")
rew = pd.read_csv(P + "rework_summary.csv")
rep = pd.read_csv(P + "repeated_activities_by_case.csv")

total = len(dur)
top3 = var.head(3)
rework_cases = rep.iloc[:, 0].nunique()   # first column is the case id

lines = []
lines.append("# CareFlow Key Findings\n")
lines.append(f"Based on {total} cases from the cleaned Sepsis event log.\n")

lines.append("## Case duration")
lines.append(f"- Average: {dur['duration_hours'].mean():.2f} hours")
lines.append(f"- Median: {dur['duration_hours'].median():.2f} hours")
lines.append(f"- 90th percentile: {dur['duration_hours'].quantile(0.9):.2f} hours")
lines.append(f"- Longest case: {dur['duration_hours'].max():.2f} hours\n")

lines.append("## Process variants")
lines.append(f"- Unique variants: {len(var)}")
lines.append(f"- Top 3 variants cover {top3['percent'].sum():.1f}% of cases\n")

lines.append("## Slowest transitions (by average wait)")
for _, r in wait.head(5).iterrows():
    lines.append(f"- {r['from']} -> {r['to']}: mean {r['mean_min']} min, "
                 f"median {r['median_min']} min, {int(r['count'])} cases")
lines.append("")

lines.append("## Rework / repeated activities")
lines.append(f"- Cases with at least one repeated activity: {rework_cases} "
             f"({rework_cases / total * 100:.1f}%)")
for _, r in rew.head(3).iterrows():
    lines.append(f"- {r.iloc[0]}: repeated in {int(r['cases_repeating'])} cases "
                 f"({r['percent_of_cases']}% of cases)")
lines.append("")

lines.append("## Notes")
lines.append("- Repetition and long waits are signals to examine, not proof of poor care.")
lines.append("- Results come from the scripts in this repository.")

os.makedirs("docs", exist_ok=True)
with open("docs/findings.md", "w") as f:
    f.write("\n".join(lines))
print("\n".join(lines))
