"""Numbers of supplement 02 for the report: smoke_s2 against smoke_s1 (before X1b). Read-only."""
import json
from pathlib import Path
import pandas as pd
pd.set_option("display.width", 220, "display.max_columns", 40)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3"); R, O = M / "smoke_s2", M / "smoke_s1"
E = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/smoke_s2")
print((R / "STATUS.txt").read_text()[:2600])
e = json.loads((E / "V3_SMOKE_RESULT.json").read_text()); b = json.loads((O.parent.parent.parent.parent / "x").read_text()) if False else None
p0 = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/smoke_s1/V3_SMOKE_RESULT.json"); o = json.loads(p0.read_text())
print("criteria", e["criteria"], "passed", e.get("passed"), "B6", e["B6"].get("b6_bn") if isinstance(e["B6"], dict) else e["B6"], "before", o["B6"].get("b6_bn") if isinstance(o["B6"], dict) else o["B6"])
for s in ("integrated", "no_new_xb"):
    x = e[s]; y = o[s]; sg = x["sg_marine_fuel"]; ins = sg["ship_in_twh_by_origin"]; tot = sum(ins.values())
    print("=====", s, x["termination_condition"], "obj", round(x["objective_eur"] / 1e9, 4), "before", round(y["objective_eur"] / 1e9, 4), "d", round((x["objective_eur"] - y["objective_eur"]) / 1e9, 4), "s", round(x["solve_seconds"]), "peak", round(x["peak_rss_gib"], 2), "v6", x["v6_label"], "failed", x["v5_failed"], "b8", x["b8_sectors_out"])
    print("  SG", {k: round(v / tot * 100, 1) for k, v in ins.items() if v > 0.01}, "ship util", round(x["ship_capacity_duals"]["max_utilisation"], 4), "duals", x["ship_capacity_duals"]["above_tolerance"], "slack", x["slack"]["Generator"]["components"], x["slack"]["Link"]["components"])
    d = x["liquid_dual_annual_mean_eur_per_mwh"]; print("  methanol", {k: round(d["methanol"][k], 2) for k in ("ID", "MY", "SG", "TH")}, "range", round(min(d["methanol"].values()), 2), round(max(d["methanol"].values()), 2), max(d["methanol"], key=d["methanol"].get))
    p = json.loads((R / s / "PRECISION.json").read_text()); v = json.loads((R / s / "V6_ACCEPTANCE.json").read_text()); a = p["a_total_cost"]
    print("  C1 rel", v["G1"]["a_relative"], "abc", p["grade"]["a"], p["grade"]["b"], p["grade"]["c"], "ratio", round(p["b_primal_violations"]["row_max_ratio"], 3), "foc", round(p["b_primal_violations"]["first_order_cost_eur_all_rows"]), "b16", p["c_prices"]["b16"]["relative_error"], "accepted", p["acceptance"]["accepted"], "ret", a["returned_iteration_by_log"]["iteration"], "resid", a["returned_iteration_by_log"]["primal_residual"], "last", a["last_iteration"]["iteration"], a["last_iteration"]["dual_residual"])
def own(d):
    t = pd.read_csv(d); c = t.columns[0]; return t.set_index(c)["owen_benefit_eur"] / 1e9
a, b = own(R / "M12_BENEFIT/BENEFIT.csv"), own(O / "M12_BENEFIT/BENEFIT.csv"); t = pd.DataFrame(dict(after=a, before=b)); t["d"] = t.after - t.before; print(t.round(3).to_string()); print(t.sum().round(3).to_dict())
print((R / "ID_LEDGER_DECOMPOSITION.csv").read_text()); print((R / "LA_EXPORT_UTILISATION.csv").read_text()[:1500]); print(json.dumps(json.loads((R / "VN_BIOMASS_BALANCE.json").read_text()).get("pool"), default=str)[:500])
print("before LA"); print((O / "LA_EXPORT_UTILISATION.csv").read_text()[:800])
