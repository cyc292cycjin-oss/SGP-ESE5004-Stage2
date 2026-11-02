import json, sys
M = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project"
d = json.load(open(f"{M}/v3/path_check/integrated/V5_GATES.json"))
for k in d:
    if isinstance(d[k], dict) and d[k].get("passed") is False:
        print("FAILED", k, json.dumps(d[k], default=str)[:1500])
print("all_passed", d.get("all_passed"), "barconv", d.get("all_passed_barconvtol"), "solver_tol", d.get("all_passed_solver_tolerances"))
print("B16", json.dumps({k: v for k, v in d["B16_LEDGER"].items() if not isinstance(v, (dict, list))}))
o = json.load(open(f"{M}/dfx_v3/smoke_v2/integrated/V5_GATES.json"))
for k in ("B8", "B13"):
    print("v2 smoke", k, json.dumps(o.get(k), default=str)[:900])
