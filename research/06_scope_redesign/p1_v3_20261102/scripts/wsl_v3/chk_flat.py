"""Supplement 01: the flat control differs from the E2 network only in the EV layer (no solve). Writes evidence/FLAT_VS_E2_DIFF.csv; prints a verdict line."""
import json, logging, sys
sys.path.insert(0, "/home/jin/wt_v3_20261102/scripts_project")
import numpy as np, pandas as pd, pypsa
from v3_static import ATTR, same
from v5.v5_gates import gate_b5_no_new_xb
logging.disable(logging.WARNING)
M = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3"
EV_BUS = ("EV battery", )
rows, bad = [], []
nets = {}
for sc in ("integrated", "no_new_xb"):
    e = pypsa.Network(f"{M}/builds/{sc}/{sc}_2920_3h_unsolved.nc"); f = pypsa.Network(f"{M}/builds_flat/{sc}/{sc}_2920_3h_unsolved.nc"); nets[sc] = f
    for typ in ATTR:
        x, y = e.df(typ), f.df(typ)
        only_e, only_f = x.index.difference(y.index), y.index.difference(x.index)
        for lab, idx, fr in (("only_E2", only_e, x), ("only_flat", only_f, y)):
            for k, v in fr.loc[idx].carrier.astype(str).value_counts().items():
                rows.append(dict(scenario=sc, type=typ, change=lab, carrier=k, count=int(v)))
                if k not in ("EV battery", "land transport EV", "BEV charger"):
                    bad.append(f"{sc} {typ} {lab} {k}")
        both = x.index.intersection(y.index)
        for col in ATTR[typ]:
            if col in x and col in y:
                ch = both[~same(x.loc[both, col], y.loc[both, col]).to_numpy()]
                for k, v in x.loc[ch].carrier.astype(str).value_counts().items():
                    rows.append(dict(scenario=sc, type=typ, change="attr:" + col, carrier=k, count=int(v)))
                    if k not in ("EV battery", "land transport EV", "BEV charger"):
                        bad.append(f"{sc} {typ} {col} {k}")
    p = e.get_switchable_as_dense("Load", "p_set"); q = f.get_switchable_as_dense("Load", "p_set")
    cm = p.columns.intersection(q.columns); d = (p[cm] - q[cm]).abs().max()
    ch = d.index[d > 1e-9]; oth = sorted(set(e.loads.loc[ch].carrier.astype(str)) - {"land transport EV"})
    if oth:
        bad.append(f"{sc} load series {oth}")
    w = e.snapshot_weightings.generators
    ee = float(p[e.loads.index[e.loads.carrier == "land transport EV"]].mul(w, axis=0).sum().sum()) / 1e6; fe = float(q[f.loads.index[f.loads.carrier == "land transport EV"]].mul(w, axis=0).sum().sum()) / 1e6
    print(sc, "EV TWh E2", round(ee, 6), "flat", round(fe, 6), "stores EV", int((f.stores.carrier == "EV battery").sum()), "meta", f.meta.get("research_ev"), "overrides", f.meta.get("research_config", {}).get("config_overrides"))
g = gate_b5_no_new_xb(nets["integrated"], nets["no_new_xb"])
pd.DataFrame(rows).to_csv("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/FLAT_VS_E2_DIFF.csv", index=False)
print("FLAT_DIFF", "rows", len(rows), "outside_EV_layer", sorted(set(bad))[:12], "B5_flat", g["passed"])
