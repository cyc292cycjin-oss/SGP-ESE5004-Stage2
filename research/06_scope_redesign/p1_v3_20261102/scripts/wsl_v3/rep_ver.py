"""Check the numbers of V3_REPORT_SUPPLEMENT01.md against the evidence (no number taken from memory). Read-only."""
import json, re
from pathlib import Path
import pandas as pd
D = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102"); E = D / "evidence/smoke_s1"; M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/smoke_s1")
t = (D / "V3_REPORT_SUPPLEMENT01.md").read_text(encoding="utf-8"); e = json.loads((E / "V3_SMOKE_RESULT.json").read_text()); bad = []
def has(x, why):
    if x not in t: bad.append((x, why))
R = ["integrated", "no_new_xb", "integrated_flat", "no_new_xb_flat"]
for r in R:
    x = e[r]; has(f"{x['objective_eur'] / 1e9:.4f}", r + " obj"); has(f"{x['peak_rss_gib']:.2f}", r + " peak"); has(f"{x['ledger_relative_error']:.1e}".replace("e-13", "e-13"), r + " b16"); has(f"{x['ship_capacity_duals']['max_utilisation'] * 100:.1f} %", r + " util")
    p = json.loads((M / r / "PRECISION.json").read_text()); v = json.loads((M / r / "V6_ACCEPTANCE.json").read_text())
    has(f"{v['G1']['a_relative']:.2e}", r + " a"); has(f"{p['b_primal_violations']['row_max_ratio']:.3f}".rstrip('0') if False else f"{p['b_primal_violations']['row_max_ratio']:.3f}", r + " ratio"); has(f"{p['b_primal_violations']['first_order_cost_eur_all_rows']:,.0f}", r + " foc")
    print(r, x["termination_condition"], "ret", p["a_total_cost"]["returned_iteration_by_log"]["iteration"], "resid", p["a_total_cost"]["returned_iteration_by_log"]["primal_residual"], "accepted", p["acceptance"]["accepted"], "solve s", round(x["solve_seconds"]), "ship in", {k: round(v_ / sum(x["sg_marine_fuel"]["ship_in_twh_by_origin"].values()) * 100, 1) for k, v_ in x["sg_marine_fuel"]["ship_in_twh_by_origin"].items() if v_ > .01})
f = e["flat_control"]
for k, v in (("EV int", f["ev_effect_cost_bn"]["integrated"]), ("EV nnx", f["ev_effect_cost_bn"]["no_new_xb"]), ("EV B6", f["ev_effect_b6_bn"]), ("B6 flat", f["b6_flat_bn"]), ("B6 E2", e["B6"]["b6_bn"] if isinstance(e["B6"], dict) and "b6_bn" in e["B6"] else e["no_new_xb"]["objective_eur"] / 1e9 - e["integrated"]["objective_eur"] / 1e9), ("rest", -f["v3_flat_minus_v2_integrated_bn"]), ("ref", f["v3_flat_no_new_xb_minus_v2_disconnected_bn"]), ("all", -f["v3_e2_minus_v2_integrated_bn"])):
    has(f"{v:.4f}", k)
b6v2 = e["v2_smoke_same_56_snapshots"]["b6_bn_eur"]; has(f"{b6v2:.4f}", "b6 v2"); has(f"{f['b6_flat_bn'] - b6v2:.4f}", "b6 diff")
print("identity", f["b6_flat_bn"] - b6v2, -f["v3_flat_minus_v2_integrated_bn"] + f["v3_flat_no_new_xb_minus_v2_disconnected_bn"])
for fn in ("BENEFIT.csv", "BENEFIT_FLAT.csv"):
    print(fn, pd.read_csv(E / fn).columns.tolist()[:8])
s = pd.read_csv(D / "evidence/X1_STOCK_TABLE_V3.csv"); print("usable total", s.no_new_xb_usable_mw.sum(), "stock total", s.apg_existing_mw.sum()); has(f"{s.no_new_xb_usable_mw.sum():,.0f}", "usable total")
print("missing:", bad)
