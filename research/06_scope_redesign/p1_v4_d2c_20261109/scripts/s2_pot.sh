#!/bin/bash
# D2c section 2.2: write BIOMASS_BASIS_T06.csv (scripts/d2c_trunk_mass.py), regenerate the potential tables (W08 / T04 / T05 must stay byte-identical, T06 new). No solver.
set -u
R=/home/jin/wt_v4_d2c; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2c_20261109
export PYTHONHASHSEED=0
cd $R || exit 1
$PY -m py_compile scripts_project/v4_biomass_potential.py scripts_project/v4_common.py scripts_project/v4_industry.py || exit 1
$PY $W/scripts/d2c_trunk_mass.py $R || exit 1
$PY scripts_project/v4_biomass_potential.py > /home/jin/v4d2c/biopot.log 2>&1 || { tail -20 /home/jin/v4d2c/biopot.log; exit 1; }
cat /home/jin/v4d2c/biopot.log
for f in BIOMASS_POTENTIAL_2050_V4.csv BIOMASS_POTENTIAL_ADJ_V4.csv BIOMASS_POTENTIAL_2050_V4_T04.csv BIOMASS_POTENTIAL_ADJ_V4_T04.csv BIOMASS_POTENTIAL_2050_V4_T05.csv BIOMASS_POTENTIAL_ADJ_V4_T05.csv BIOMASS_BASIS_T05.csv; do
  [ "$(git show HEAD:research_inputs/biomass_v5/$f | sha256sum | cut -c1-64)" = "$(sha256sum research_inputs/biomass_v5/$f | cut -c1-64)" ] && echo "SAME $f" || echo "CHANGED $f"
done
sha256sum research_inputs/biomass_v5/BIOMASS_BASIS_T06.csv research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4_T06.csv research_inputs/biomass_v5/BIOMASS_POTENTIAL_ADJ_V4_T06.csv
$PY - <<'P'
import pandas as pd
B = "/home/jin/wt_v4_d2c/research_inputs/biomass_v5/"
a5 = pd.read_csv(B + "BIOMASS_POTENTIAL_2050_V4_T05.csv").set_index(["country", "category"]); a6 = pd.read_csv(B + "BIOMASS_POTENTIAL_2050_V4_T06.csv").set_index(["country", "category"])
num = lambda s: pd.to_numeric(s, errors="coerce").fillna(0.0)
d = (num(a6.potential_main_mwh) - num(a5.potential_main_mwh)) / 1e6
print("rows", len(a5), len(a6), "| changed main rows:", {k: round(v, 6) for k, v in d[d != 0].items()})
for col in a5.columns:
    x, y = a5[col].astype(str), a6[col].astype(str)
    n = int((x != y).sum())
    if n:
        print("column", col, "differs in", n, "rows:", sorted(set(c for (_, c) in x[x != y].index)))
for f5, f6 in (("BIOMASS_POTENTIAL_2050_V4_T05.csv", "BIOMASS_POTENTIAL_2050_V4_T06.csv"), ("BIOMASS_POTENTIAL_ADJ_V4_T05.csv", "BIOMASS_POTENTIAL_ADJ_V4_T06.csv")):
    x = open(B + f5, encoding="utf-8").read().split("\n"); y = open(B + f6, encoding="utf-8").read().split("\n")
    dl = [i for i, (p, q) in enumerate(zip(x, y)) if p != q]
    print("LINES", f6, "vs", f5, "| lines", len(x), len(y), "| differing", len(dl), "| keys", [(y[i].split(",")[0], y[i].split(",")[1]) for i in dl])
t5 = pd.read_csv(B + "BIOMASS_POTENTIAL_ADJ_V4_T05.csv"); t6 = pd.read_csv(B + "BIOMASS_POTENTIAL_ADJ_V4_T06.csv")
for tt, t in (("T05", t5), ("T06", t6)):
    z = t[t.category == "TOTAL solid"].set_index("country").potential_adjusted_TWh
    tr = t[t.category == "oil_palm_trunk"].set_index("country").potential_adjusted_TWh
    print(tt, "ASEAN solid", round(float(z["ASEAN11"]), 4), "| trunk", {k: round(float(v), 6) for k, v in tr.items()}, "sum", round(float(tr.sum()), 4))
P
echo S2POT_DONE
