"""W19a exploration: how v4 (26c2e47d) changed the rows that were in-use C at the W10 baseline (aad8e476). Read only."""
import pandas as pd

D = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w19a_20261109/cache/"
old = pd.read_csv(D + "DATA_REGISTRY_aad8e476.csv", dtype=str, keep_default_na=False).set_index("param_id")
new = pd.read_csv(D + "DATA_REGISTRY_26c2e47d.csv", dtype=str, keep_default_na=False).set_index("param_id")
USE = {"REGISTERED", "SENSITIVITY", "DATA_PENDING"}
print("rows", len(old), len(new), "removed", len(set(old.index) - set(new.index)), "added", len(set(new.index) - set(old.index)))
oc = old[(old.tier == "C") & old.status.isin(USE)]
print("old in-use C", len(oc))
cols = [c for c in old.columns]
chg = {}
for p in oc.index:
    if p not in new.index:
        chg[p] = ["REMOVED"]; continue
    chg[p] = [c for c in cols if old.at[p, c] != new.at[p, c]]
s = pd.Series({p: ",".join(v) for p, v in chg.items()})
print(s.value_counts().to_string())
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 220)
for p, v in chg.items():
    if v and v != ["source_sha256"]:
        o, n = old.loc[p], new.loc[p] if p in new.index else None
        print("\n##", p, v)
        for c in v:
            if c == "description":
                print("   desc+:", n.description[len(o.description):][:400] if n.description.startswith(o.description) else ("NEW: " + n.description[:400]))
            else:
                print(f"   {c}: {o[c][:120]!r} -> {n[c][:120]!r}")
