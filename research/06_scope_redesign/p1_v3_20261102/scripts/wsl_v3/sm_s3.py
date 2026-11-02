"""Numbers of supplement 03: smoke_s3 (one way) against smoke_s2 (two way) and smoke_s1 (no plant lines); LA exchange table in the format of report 02 section 3.3. Read-only."""
import json, logging
from pathlib import Path
import pandas as pd, pypsa
logging.disable(logging.WARNING)
pd.set_option("display.width", 200, "display.max_columns", 30)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3"); R, O, Z = M / "smoke_s3", M / "smoke_s2", M / "smoke_s1"
E = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence"); e = json.loads((E / "smoke_s3/V3_SMOKE_RESULT.json").read_text()); o = json.loads((E / "smoke_s2/V3_SMOKE_RESULT.json").read_text()); z = json.loads((E / "smoke_s1/V3_SMOKE_RESULT.json").read_text())
print("\n".join(l[:120] for l in (R / "STATUS.txt").read_text().splitlines() if l.startswith(("START", "END_", "GAP", "V6_", "M12_BENEFIT", "EVAL", "DONE"))))
print("criteria", e["criteria"], e.get("passed"))
for s in ("integrated", "no_new_xb"):
    x = e[s]; print("=====", s, x["termination_condition"], "obj", round(x["objective_eur"] / 1e9, 4), "two-way", round(o[s]["objective_eur"] / 1e9, 4), "none", round(z[s]["objective_eur"] / 1e9, 4), "s", round(x["solve_seconds"]), "peak", round(x["peak_rss_gib"], 2), x["v6_label"], x["v5_failed"], x["b8_sectors_out"])
    sg = x["sg_marine_fuel"]["ship_in_twh_by_origin"]; t = sum(sg.values()); print("  SG", {k: round(v / t * 100, 1) for k, v in sg.items() if v > 0.01}, "util", round(x["ship_capacity_duals"]["max_utilisation"], 4), "duals", x["ship_capacity_duals"]["above_tolerance"], "slack", x["slack"]["Generator"]["components"], x["slack"]["Link"]["components"])
    p = json.loads((R / s / "PRECISION.json").read_text()); v = json.loads((R / s / "V6_ACCEPTANCE.json").read_text()); a = p["a_total_cost"]["returned_iteration_by_log"]
    print("  C1", v["G1"]["a_relative"], p["grade"]["a"], p["grade"]["b"], p["grade"]["c"], "ratio", round(p["b_primal_violations"]["row_max_ratio"], 3), "foc", round(p["b_primal_violations"]["first_order_cost_eur_all_rows"]), "b16", p["c_prices"]["b16"]["relative_error"], "accepted", p["acceptance"]["accepted"], "ret", a["iteration"], "resid", a["primal_residual"])
b = {k: e[k]["objective_eur"] for k in ("integrated", "no_new_xb")}; print("B6", (b["no_new_xb"] - b["integrated"]) / 1e9, "two-way", (o["no_new_xb"]["objective_eur"] - o["integrated"]["objective_eur"]) / 1e9)
own = lambda d: pd.read_csv(d).set_index("player")["owen_benefit_eur"] / 1e9
t = pd.DataFrame(dict(none=own(Z / "M12_BENEFIT/BENEFIT.csv"), two_way=own(O / "M12_BENEFIT/BENEFIT.csv"), one_way=own(R / "M12_BENEFIT/BENEFIT.csv"))); print(t.round(3).to_string()); print(t.sum().round(3).to_dict())


def la(n):
    w = n.snapshot_weightings.generators; c = n.buses.country.astype(str); r = {}
    for k, z_ in n.lines[n.lines.border_class == "cross_border"].iterrows():
        a, b_ = c[z_.bus0], c[z_.bus1]
        if (a == "LA") != (b_ == "LA"):
            f = n.lines_t.p0[k] if a == "LA" else -n.lines_t.p0[k]; q = b_ if a == "LA" else a; r.setdefault(q, [0.0, 0.0]); r[q][0] += float(f.clip(lower=0).mul(w).sum()) / 1e6; r[q][1] += float((-f).clip(lower=0).mul(w).sum()) / 1e6
    for k, z_ in n.links[(n.links.border_class == "cross_border") & (n.links.transport_carrier.astype(str) == "electricity")].iterrows():
        a, b_ = c[z_.bus0], c[z_.bus1]
        if (a == "LA") != (b_ == "LA"):
            q = b_ if a == "LA" else a; r.setdefault(q, [0.0, 0.0]); r[q][0 if a == "LA" else 1] += float(n.links_t.p0[k].clip(lower=0).mul(w).sum()) / 1e6
    t = pd.DataFrame(r, index=["export", "import"]).T; t["net"] = t["export"] - t["import"]; return t.round(2)


for k, d in (("none", Z), ("two_way", O), ("one_way", R)):
    t = la(pypsa.Network(d / "no_new_xb/no_new_xb_SMOKE_TEST_ONLY_solved.nc")); print(k); print(t.to_string()); print("net", round(float(t.net.sum()), 2))
print((R / "LA_EXPORT_UTILISATION.csv").read_text()[:1300])
