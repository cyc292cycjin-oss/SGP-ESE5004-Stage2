"""B13 before / after on the four v3 networks and on the v2 build: the old and the new predicate on every link touching a pool bus (no solve)."""
import json, logging, sys
sys.path.insert(0, "/home/jin/wt_v3_20261102/scripts_project")
import pandas as pd, pypsa
from v5.v5_gates import gate_b13_imports_one_way, pool_buses
logging.disable(logging.WARNING)
M = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project"
B = f"{M}/v3/builds"
OUT = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/B13_BEFORE_AFTER.json"
res = {}
for lab, f in (("integrated_2920", f"{B}/integrated/integrated_2920_3h_unsolved.nc"), ("no_new_xb_2920", f"{B}/no_new_xb/no_new_xb_2920_3h_unsolved.nc"), ("integrated_365", f"{B}/integrated/integrated_365_24h_unsolved.nc"),
               ("no_new_xb_365", f"{B}/no_new_xb/no_new_xb_365_24h_unsolved.nc"), ("v2_integrated_2920", f"{M}/dfx_v3/builds_v2/integrated/integrated_2920_3h_unsolved.nc")):
    n = pypsa.Network(f); pools = pool_buses(n); L = n.links; cols = [c for c in L if c.startswith("bus") and c[3:].isdigit()]
    touch = L[L[cols].isin(pools).any(axis=1)]
    old, new = [], []
    for name, z in touch.iterrows():
        others = [z[c] for c in cols if z[c] and z[c] not in pools]
        if not others or any(b not in n.buses.index for b in others):
            old.append(name)
        if (not others and z.get("border_class") != "maritime_trade") or any(b not in n.buses.index for b in others):
            new.append(name)
    trade = set(L.index[(L.get("border_class") == "maritime_trade") & L.carrier.isin(["oil non-fossil ship", "methanol ship", "ammonia ship", "liquid transit rail"])])
    g = gate_b13_imports_one_way(n)
    res[lab] = dict(links_touching_pools=int(len(touch)), old_rule_flagged=len(old), new_rule_flagged=len(new), liquid_trade_links=len(trade), old_flagged_equal_liquid_trade=set(old) == trade,
                    old_flagged_by_carrier={str(k): int(v) for k, v in L.loc[old].carrier.astype(str).value_counts().items()}, gate_passed_after=bool(g["passed"]))
    print(lab, res[lab])
json.dump(res, open(OUT, "w"), indent=1, sort_keys=True)
