#!/bin/bash
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; E=/home/jin/wt_s4q_20261020/research/06_scope_redesign/p1_step4q_20261020/evidence/s4q_2
S=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4m/s4m2/solves
$PY - $E $S <<'P'
import json, sys
E, S = sys.argv[1:3]
def brief(g, k):
    v = g.get(k)
    if not isinstance(v, dict): return None
    keep = {kk: vv for kk, vv in v.items() if not isinstance(vv, (dict, list)) or kk in ("checks", "failed_checks")}
    return {kk: (vv if not isinstance(vv, float) else float(f"{vv:.3g}")) for kk, vv in keep.items() if kk not in ("note", "description", "rule")}
for t in ("t8", "t16"):
    for sc in ("integrated", "disconnected", "integrated_nze"):
        g = json.load(open(f"{E}/{t}/{sc}/V5_GATES.json"))
        for k in ("A1_A2_S4B", "A3_S4B", "B2", "B14"):
            if isinstance(g.get(k), dict) and g[k].get("passed") is False:
                print(t, sc, k, json.dumps(brief(g, k), default=str)[:700])
g = json.load(open(f"{S}/s4m_A_integrated/V5_GATES.json"))
print("A integrated A1_A2_S4B", json.dumps(brief(g, "A1_A2_S4B"), default=str)[:700])
P
