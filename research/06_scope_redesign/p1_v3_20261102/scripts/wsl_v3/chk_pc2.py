import json
R = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/path_check2"
for sc in ("integrated", "no_new_xb"):
    d = json.load(open(f"{R}/{sc}/V5_GATES.json"))
    print(sc, "failed", sorted(k for k, v in d.items() if isinstance(v, dict) and v.get("passed") is False), "B13", d["B13"]["passed"], "B8", d["B8"]["passed"], "Transport rel", d["B8"]["sector_totals"]["Transport"]["rel"], "B16 rel", d["B16_LEDGER"]["relative_error"])
    v6 = json.load(open(f"{R}/{sc}/V6_ACCEPTANCE.json"))
    print("  G2_1", {k: v for k, v in v6["G2"]["G2_1"].items() if k in ("passed", "sha256_equal", "readback")}, "D13", v6["diagnostics"].get("D13_imports_one_way"), "D11", v6["diagnostics"].get("D11_demand_conservation"))
e = json.load(open(f"{R}/eval/V3_SMOKE_RESULT.json"))
for sc in ("integrated", "no_new_xb"):
    print(sc, "duals", e[sc]["ship_capacity_duals"], "slack", e[sc]["slack"], "sgkeys", list(e[sc]["sg_marine_fuel"]))
print("B5", e.get("B5_NO_NEW_XB_solved", {}).get("passed"))
