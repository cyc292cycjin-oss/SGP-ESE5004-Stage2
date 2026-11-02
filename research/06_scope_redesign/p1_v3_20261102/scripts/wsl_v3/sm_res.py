import json
E = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/smoke/V3_SMOKE_RESULT.json"
R = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/smoke_r2"
e = json.load(open(E))
print("criteria", e["criteria"], "passed", e["passed"])
print("B6", e["B6"]["b6_bn_eur"], e["B6"]["gate"].get("passed"), "v2", e.get("v2_smoke_same_56_snapshots", {}).get("b6_bn_eur"), e.get("v2_smoke_same_56_snapshots", {}).get("objective_eur"))
print("B5 solved", e.get("B5_NO_NEW_XB_solved", {}).get("passed"))
for s in ("integrated", "no_new_xb"):
    x = e[s]
    print("==", s, {k: x.get(k) for k in ("termination_condition", "status", "objective_eur", "solve_seconds", "peak_rss_gib", "truncated_to", "profile", "v6_label", "c1_grade", "ledger_identity_passed", "ledger_relative_error", "v5_all_passed", "v5_failed")})
    print("  c1", x.get("c1"))
    print("  duals", x.get("ship_capacity_duals"))
    print("  sg", x.get("sg_marine_fuel"))
    print("  slack", x.get("slack"))
    print("  ships", x.get("ship_flow_twh"))
    print("  xb", x.get("cross_border"))
    print("  id", x.get("id_industry_shares"))
    print("  dual", {k: {c: round(v, 2) for c, v in d.items()} for k, d in (x.get("liquid_dual_annual_mean_eur_per_mwh") or {}).items()})
    g = json.load(open(f"{R}/{s}/V5_GATES.json"))
    print("  B8 rel", {k: v["rel"] for k, v in g["B8"]["sector_totals"].items() if abs(v["rel"] or 0) > 1e-9}, "checks", g["B8"]["checks"], "B13", g["B13"]["passed"])
