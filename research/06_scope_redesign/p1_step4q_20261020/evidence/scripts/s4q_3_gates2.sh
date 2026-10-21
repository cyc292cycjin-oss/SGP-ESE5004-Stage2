#!/bin/bash
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; E=/home/jin/wt_s4q_20261020/research/06_scope_redesign/p1_step4q_20261020/evidence/s4q_2
$PY - $E <<'P'
import json, sys
E = sys.argv[1]
g = json.load(open(f"{E}/t16/disconnected/V5_GATES.json"))
for k in ("B2", "B14"):
    s = json.dumps(g[k], default=str); print(k, len(s), s[:900]); print()
a3 = g["A3_S4B"]; print("A3_S4B keys", list(a3)[:12]); print(json.dumps({k: v for k, v in a3.items() if k != "checks"}, default=str)[:600])
ch = a3.get("checks"); 
if isinstance(ch, dict):
    bad = {k: v for k, v in ch.items() if isinstance(v, dict) and v.get("passed") is False}; print("A3 failing checks", len(bad), json.dumps(dict(list(bad.items())[:3]), default=str)[:900])
elif isinstance(ch, list):
    bad = [c for c in ch if isinstance(c, dict) and c.get("passed") is False]; print("A3 failing checks", len(bad), json.dumps(bad[:3], default=str)[:900])
for t in ("t8", "t16"):
    for sc in ("integrated", "disconnected", "integrated_nze"):
        p = json.load(open(f"/home/jin/s4q_local/judge_shadow/{t}/{sc}/PRECISION.json"))
        c = p["c_prices"]; print(t, sc, "c passed", c["passed"], "all_terms", c["passed_kkt_all_terms"], "totals", {k: round(v, 1) if isinstance(v, float) else v for k, v in c["totals_eur"].items()})
P
