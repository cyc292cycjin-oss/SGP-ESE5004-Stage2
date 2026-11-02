"""Numbers of supplement 01 for the report, re-read from the evidence and the run folders. Read-only."""
import json
from pathlib import Path
import pandas as pd
pd.set_option("display.width", 220, "display.max_columns", 40)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
W = Path("/home/jin/wt_v3_20261102"); E = W / "research/06_scope_redesign/p1_v3_20261102/evidence/smoke_s1"; R = M / "v3/smoke_s1"; V2 = M / "dfx_v3/smoke_v2"
print(sorted(p.name for p in E.iterdir()))
e = json.loads((E / "V3_SMOKE_RESULT.json").read_text())
print("top", list(e)); print("criteria", e.get("criteria"))
RUNS = ["integrated", "no_new_xb", "integrated_flat", "no_new_xb_flat"]
print("run keys", list(e["integrated"]))
for s in RUNS:
    x = e[s]; print("=====", s)
    print({k: x.get(k) for k in ("termination_condition", "status", "objective_eur", "solve_seconds", "peak_rss_gib", "ledger_relative_error", "v6_label", "criterion_optimal_or_119ab", "criterion_c1_abc_and_gates_v6", "solved_network")})
    print(" v5_failed", x.get("v5_failed"), "b8_out", x.get("b8_sectors_out"), "slack", {k: v for k, v in x.items() if "slack" in k})
    sg = x.get("sg_marine_fuel") or {}; ins = sg.get("ship_in_twh_by_origin") or {}; tot = sum(ins.values()) or 1.0
    print(" SG load", round(sg.get("marine_load_twh", 0), 2), "supplied", round(sg.get("supplied_twh", 0), 2), {k: round(v / tot * 100, 2) for k, v in ins.items() if v > 0.01}, {k: v for k, v in sg.items() if k not in ("ship_in_twh_by_origin",)})
    d = x.get("liquid_dual_annual_mean_eur_per_mwh") or {}
    print(" dual range", {k: (round(min(v.values()), 2), round(max(v.values()), 2), max(v, key=v.get), round(v.get("SG", 0), 2)) for k, v in d.items()})
    print(" ship duals", x.get("ship_capacity_duals"))
    p = json.loads((R / s / "PRECISION.json").read_text())
    print(" precision keys", list(p)); print(" a", json.dumps(p.get("a_total_cost"), default=str)[:420]); print(" b", json.dumps(p.get("b_primal_violations"), default=str)[:420]); print(" c", json.dumps(p.get("c_prices"), default=str)[:420]); print(" grade", p.get("grade"), "acceptance", json.dumps(p.get("acceptance"), default=str)[:300])
    v6 = json.loads((R / s / "V6_ACCEPTANCE.json").read_text()); print(" V6", v6.get("label"), json.dumps(v6.get("G1"), default=str)[:300])
    g = json.loads((R / s / "V5_GATES.json").read_text()); print(" gates", {k: g.get(k) for k in ("all_passed", "all_passed_barconvtol", "all_passed_solver_tolerances", "acceptance_basis")}, {k: v.get("passed") for k, v in g.items() if isinstance(v, dict) and v.get("passed") is False})
    a = g.get("B8") or {}; print(" B8", a.get("passed"), {k: v.get("rel") for k, v in (a.get("sector_totals") or {}).items()})
    r = json.loads((R / s / "SOLVE_RECEIPT.json").read_text()); print(" receipt", {k: r.get(k) for k in ("termination_condition", "status", "objective", "solver_profile", "barrier_iterations", "bar_iter_count", "crossover", "seconds")})
for tag, ben in (("E2", "M12_BENEFIT"), ("flat", "M12_BENEFIT_FLAT")):
    B = R / ben; f = next(p for p in sorted(B.iterdir()) if p.suffix == ".json"); b = json.loads(f.read_text()); o = b.get("owen") or {}
    pI, pD = o.get("allocation_integrated_eur") or {}, o.get("allocation_disconnected_eur") or {}
    print(tag, "b6", b.get("b6_eur"), "usable", o.get("usable"), sorted(((k, round((pD[k] - pI[k]) / 1e9, 3)) for k in pI), key=lambda t: -t[1]))
    print(tag, "sum", round(sum(pD[k] - pI[k] for k in pI) / 1e9, 4), "keys", list(b)[:16])
