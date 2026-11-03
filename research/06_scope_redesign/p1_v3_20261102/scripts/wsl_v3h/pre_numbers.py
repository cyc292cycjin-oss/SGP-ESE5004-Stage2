import json, sys
from pathlib import Path
import pandas as pd, pypsa
run = Path(sys.argv[1]); reg = pd.read_csv(sys.argv[2], dtype=str, keep_default_na=False).set_index("param_id"); rv = lambda p: float(reg.loc[p, "value"])
KEY = {"oil non-fossil ship": "oil", "methanol ship": "methanol", "ammonia ship": "ammonia"}
for rid in ("integrated", "no_new_xb"):
    n = pypsa.Network(str(sorted((run / rid).glob("*_solved.nc"))[0])); w = n.snapshot_weightings.objective
    L = n.links[n.links.carrier.isin(list(KEY))]; F = n.links_t.p0[L.index].mul(w, axis=0).sum(); km = L.route_km.astype(float); k = L.carrier.map(KEY)
    cA = pd.Series([rv(f"liquid_ship_fixed_ieaghg_{a}") + rv(f"liquid_ship_ckm_ieaghg_{a}") * d for a, d in zip(k, km)], index=L.index)
    cB = pd.Series([rv(f"liquid_ship_ckm_td_{a}") * d for a, d in zip(k, km)], index=L.index)
    print(rid, "upper bound increase bn (eta_B F cA - F cB):", float((L.efficiency * F * cA - F * cB).sum() / 1e9), "objective", n.objective / 1e9 if n.objective else None)
# LP sizes: linear in the snapshot count (56 and 365 of the registered decision-180 networks, RUN_PLAN_V3 21.1); the same method on v2 vs the D2 measurement
def ext(a56, a365, n=2920):
    b = (a365 - a56) / (365 - 56); return a56 + b * (n - 56)
v3 = dict(col=(729156, 4694244), row=(1603380, 10380525), nnz=(3715722, 24246787)); v3x = dict(col=(707802, 4557015), row=(1555798, 10073383), nnz=(3565488, 23271214))
print("v3 integrated 2920:", {k: round(ext(*v)) for k, v in v3.items()}); print("v3 no_new_xb 2920:", {k: round(ext(*v)) for k, v in v3x.items()})
v2 = dict(col=(695950, 4477801), row=(1541222, 9975377), nnz=(3612124, 23460944))
print("v2 integrated 2920 extrapolated:", {k: round(ext(*v)) for k, v in v2.items()}, "D2 measured: col 35748446 row 79714102 nnz 186531986")
