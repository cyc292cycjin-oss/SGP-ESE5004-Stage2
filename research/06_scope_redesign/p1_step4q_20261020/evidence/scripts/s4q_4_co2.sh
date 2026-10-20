#!/bin/bash
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; E=/home/jin/wt_s4q_20261020/research/06_scope_redesign/p1_step4q_20261020/evidence/s4q_3
$PY - $E <<'P'
import json, sys
E = sys.argv[1]
for t in ("t8", "t16"):
    C = json.load(open(f"{E}/COMPARE_{t}_VS_S4M2.json"))
    for sc, inf in C["information"].items():
        d = inf["country_co2_shadow_price_raw_dual"]
        rel = {c: abs(v["diff"]) / abs(v["ref"]) for c, v in d.items() if v["diff"] is not None and v["ref"]}
        c = max(rel, key=rel.get); vals = [v["ref"] for v in d.values() if v["ref"] is not None]
        print(t, sc, "max rel", f"{rel[c]:.2e}", c, d[c], "ref range", f"{min(vals):.1f}..{max(vals):.1f}")
P
