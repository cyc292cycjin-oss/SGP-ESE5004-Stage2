"""DFX v3 probe 4 (read-only): sensitivity-mode tables must differ from the committed version only by the new ammonia columns (values unchanged);
feedstock territorial tables: only full_release_2050_t (F3 scope) and the anchor-mode multiplier rows may change."""
import subprocess
from io import StringIO
from pathlib import Path

import pandas as pd

WT = Path("/home/jin/wt_dfx_v3_20261026")


def old(rel):
    return subprocess.run(["git", "show", f"834a0f19:{rel}"], cwd=WT, check=True, capture_output=True, text=True).stdout


for mode in ("aeo8_ats_relative", "gdp", "population", "aeo8_ats_relative_level"):
    for sfx in ("", "_OTHER_USEFUL_HEAT_BANDS", "_TD_SENSITIVITY", "_OTHER_IDEES_TODAY", "_OTHER_ASEAN_OWN_2019"):
        rel = f"research_inputs/demand_v5/INDUSTRY_2050_SUMMARY_{mode}{sfx}.csv"
        if not (WT / rel).exists():
            continue
        n = pd.read_csv(WT / rel); o = pd.read_csv(StringIO(old(rel)))
        new_cols = [c for c in n.columns if c not in o.columns]
        same = all((n[c].equals(o[c]) if n[c].dtype.kind not in "fi" else ((n[c] - o[c]).abs() <= 1e-9 * o[c].abs().clip(lower=1.0)).all()) for c in o.columns)
        print(f"{rel.split('/')[-1]}: old columns unchanged={same}; new columns={new_cols}; ammonia_rule={set(n.get('ammonia_rule', ['-']))}")
for rel in ("research_inputs/registry_v5/FEEDSTOCK_CARBON_TERRITORIAL_2050_aeo8_ats_relative.csv", "research_inputs/registry_v5/FEEDSTOCK_CARBON_TERRITORIAL_2050_aeo8_ats_anchor.csv"):
    n = pd.read_csv(WT / rel).set_index("country"); o = pd.read_csv(StringIO(old(rel))).set_index("country")
    ch = [c for c in o.columns if c in n.columns and not (n[c].astype(str) == o[c].astype(str)).all()]
    print(f"{rel.split('/')[-1]}: changed columns {ch}")
    if "full_release_2050_t" in ch:
        print((pd.DataFrame({"old": o.full_release_2050_t, "new": n.full_release_2050_t}) / 1e6).round(3).T.to_string())
p = "research_inputs/registry_v5/PROCESS_EMISSIONS_2019_2050.csv"
n = pd.read_csv(WT / p); o = pd.read_csv(StringIO(old(p)))
ch = [c for c in o.columns if not (n[c].astype(str) == o[c].astype(str)).all()]
print("PROCESS_EMISSIONS changed columns:", ch)
print("tco2_2050_ats_anchor sum old -> new (Mt):", round(o.tco2_2050_ats_anchor.sum() / 1e6, 3), "->", round(n.tco2_2050_ats_anchor.sum() / 1e6, 3))
