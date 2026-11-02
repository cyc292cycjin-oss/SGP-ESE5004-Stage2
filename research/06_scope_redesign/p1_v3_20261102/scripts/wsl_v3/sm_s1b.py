"""Supplement 01: gates that did not pass (details), B3 with full digits, returned iterations, biggest row violations. Read-only."""
import json
from pathlib import Path
import pandas as pd
pd.set_option("display.width", 220, "display.max_columns", 40)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
R = M / "v3/smoke_s1"; V2 = M / "dfx_v3/smoke_v2"
RUNS = ["integrated", "no_new_xb", "integrated_flat", "no_new_xb_flat"]


def short(x, n=650):
    return json.dumps(x, default=str)[:n]


for s in RUNS:
    print("=====", s)
    g = json.loads((R / s / "V5_GATES.json").read_text())
    for k in ("A1_A2", "A1_A2_S4B", "A3", "A3_S4B", "B1"):
        v = g.get(k) or {}
        print(k, v.get("passed"), short({a: b for a, b in v.items() if a not in ("gate", "rows", "countries")}))
        if k == "B1" and v.get("passed") is False:
            print("  B1 full", short(v, 1800))
    b = g["B3"]; r = pd.DataFrame(b["rows"]); r["excess_mwh"] = r.used_mwh - r.potential_mwh
    print("B3", b["passed"], "stores", len(r), "failed"); print(r[~r.within | r.refilled][["store", "potential_mwh", "used_mwh", "excess_mwh", "within", "refilled"]].to_string(index=False))
    x = r[r.country == "VN"]; print("  VN potential TWh", round(x.potential_mwh.sum() / 1e6, 6), "used", round(x.used_mwh.sum() / 1e6, 6), "max excess MWh", round(x.excess_mwh.max(), 5), "max excess share", x.excess_mwh.max() / x.potential_mwh.max())
    print("  all max excess MWh", round(r.excess_mwh.max(), 5), "countries at >=99.9 %", sorted(set(r[r.share_used >= 0.999].country)))
    p = json.loads((R / s / "PRECISION.json").read_text()); a = p["a_total_cost"]
    print(" a returned", short(a.get("returned_iteration_by_log"), 420)); print(" a keys", list(a))
    print(" b", short({k: v for k, v in p["b_primal_violations"].items() if k not in ("budget_note", "consistency_with_l23_script")}, 900))
    print(" c", short({k: v for k, v in p["c_prices"].items() if k not in ("formulas",)}, 900))
    print(" solver params", short(p.get("solver_parameters"), 400))
