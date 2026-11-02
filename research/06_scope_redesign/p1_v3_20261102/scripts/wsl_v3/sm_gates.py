import json, re
from pathlib import Path
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
R = M / "v3/smoke_r2"; V2 = M / "dfx_v3/smoke_v2"
def short(x, n=900):
    return json.dumps(x, default=str)[:n]
for sc in ("integrated", "no_new_xb"):
    g = json.loads((R / sc / "V5_GATES.json").read_text())
    print("=====", sc, "basis", g.get("acceptance_basis"), "all", g.get("all_passed"), "barconv", g.get("all_passed_barconvtol"), "tol", g.get("all_passed_solver_tolerances"))
    for k in ("A1_A2", "A1_A2_S4B", "A3", "A3_S4B", "B3", "B3_S4B"):
        v = g.get(k) or {}
        print(k, "passed", v.get("passed"), short({a: b for a, b in v.items() if a not in ("gate",)}, 700))
    p = json.loads((R / sc / "PRECISION.json").read_text())
    print(" a", short(p.get("a_total_cost"), 800)); print(" b", short(p.get("b_primal_violations"), 700)); print(" c", short(p.get("c_prices"), 500)); print(" grade", short(p.get("grade"), 300)); print(" accept", short(p.get("acceptance"), 300))
    v6 = json.loads((R / sc / "V6_ACCEPTANCE.json").read_text())
    print(" V6", v6.get("label"), short(v6.get("G1"), 500))
g = json.loads((V2 / "integrated/V5_GATES.json").read_text())
print("===== v2 smoke integrated all", g.get("all_passed"), "tol", g.get("all_passed_solver_tolerances"), {k: (v.get("passed")) for k, v in g.items() if isinstance(v, dict) and k in ("A1_A2", "A1_A2_S4B", "A3", "B3", "B8", "B13")})
print(short({k: v for k, v in (g.get("A1_A2") or {}).items() if k != "gate"}, 500))
