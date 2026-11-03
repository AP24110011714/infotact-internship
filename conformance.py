import pandas as pd

FILE = "data/processed/clean_log.csv"   # EDIT to your cleaned file
CASE, ACTIVITY, TIME = "case_id", "activity", "timestamp"   # EDIT if different

# EDIT: the expected order of key steps. Names must match your data exactly.
IDEAL = ["ER Registration", "ER Triage", "ER Sepsis Triage"]

df = pd.read_csv(FILE, parse_dates=[TIME]).sort_values([CASE, TIME])

print("Activities in your data (most common first):")
print(df[ACTIVITY].value_counts().head(15).to_string())

unknown = [a for a in IDEAL if a not in set(df[ACTIVITY])]
if unknown:
    raise SystemExit(f"These IDEAL steps are not in your data: {unknown}. Edit IDEAL.")


def check(seq):
    """Return the ideal steps that are missing or out of order in this case."""
    pos, bad = 0, []
    for step in IDEAL:
        if step in seq[pos:]:
            pos = seq.index(step, pos) + 1
        else:
            bad.append(step)
    return bad


rows = []
for case, seq in df.groupby(CASE)[ACTIVITY].apply(list).items():
    bad = check(seq)
    rows.append({"case_id": case, "conforms": not bad,
                 "missing_or_out_of_order": "; ".join(bad)})
res = pd.DataFrame(rows)

total = len(res)
ok = int(res["conforms"].sum())
print(f"\nIdeal order: {' -> '.join(IDEAL)}")
print(f"Conforming cases: {ok} of {total} ({ok / total * 100:.1f}%)")
print("Most common deviations:")
print(res.loc[~res["conforms"], "missing_or_out_of_order"].value_counts().head(5).to_string())

res.to_csv("data/processed/conformance_results.csv", index=False)
