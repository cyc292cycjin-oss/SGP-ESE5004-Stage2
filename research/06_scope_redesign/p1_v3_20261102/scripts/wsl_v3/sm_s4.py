"""Numbers of supplement 04: smoke_s4 (one way + bound to stock) against smoke_s3 (one way), smoke_s2 (two way), smoke_s1 (no plant lines): four-column LA tables. Read-only."""
import json, logging
from pathlib import Path
import pandas as pd, pypsa
logging.disable(logging.WARNING)
pd.set_option("display.width", 220, "display.max_columns", 30, "display.max_rows", 100)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3"); B, R, O, Z = M / "smoke_s4", M / "smoke_s3", M / "smoke_s2", M / "smoke_s1"
E = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence")
res = {k: json.loads((E / f"smoke_{k}/V3_SMOKE_RESULT.json").read_text()) for k in ("s4", "s3", "s2", "s1")}; e = res["s4"]
print("\n".join(l[:130] for l in (B / "STATUS.txt").read_text().splitlines() if l.startswith(("START", "END_", "GAP", "V6_", "M12_BENEFIT", "EVAL", "DONE", "STOP", "NO_"))))
print("criteria", e["criteria"], e.get("passed"))
for s in ("integrated", "no_new_xb"):
    x = e[s]; print("=====", s, x["termination_condition"], "obj", round(x["objective_eur"] / 1e9, 4), {k: round(res[k][s]["objective_eur"] / 1e9, 4) for k in ("s3", "s2", "s1")}, "s", round(x["solve_seconds"]), "peak", round(x["peak_rss_gib"], 2), x["v6_label"], x["v5_failed"], x["b8_sectors_out"])
    sg = x["sg_marine_fuel"]["ship_in_twh_by_origin"]; t = sum(sg.values()); print("  SG", {k: round(v / t * 100, 1) for k, v in sg.items() if v > 0.01}, "util", round(x["ship_capacity_duals"]["max_utilisation"], 4), "duals", x["ship_capacity_duals"]["above_tolerance"], "slack", x["slack"]["Generator"]["components"], x["slack"]["Link"]["components"])
    p = json.loads((B / s / "PRECISION.json").read_text()); v = json.loads((B / s / "V6_ACCEPTANCE.json").read_text()); a = p["a_total_cost"]["returned_iteration_by_log"]
    print("  C1", v["G1"]["a_relative"], p["grade"]["a"], p["grade"]["b"], p["grade"]["c"], "ratio", round(p["b_primal_violations"]["row_max_ratio"], 3), "foc", round(p["b_primal_violations"]["first_order_cost_eur_all_rows"]), "b16", p["c_prices"]["b16"]["relative_error"], "accepted", p["acceptance"]["accepted"], "ret", a["iteration"], "resid", a["primal_residual"])
b6 = lambda r: (r["no_new_xb"]["objective_eur"] - r["integrated"]["objective_eur"]) / 1e9
print("B6", {k: round(b6(res[k]), 4) for k in ("s4", "s3", "s2", "s1")})
own = lambda d: pd.read_csv(d).set_index("player")["owen_benefit_eur"] / 1e9
t = pd.DataFrame(dict(none=own(Z / "M12_BENEFIT/BENEFIT.csv"), two_way=own(O / "M12_BENEFIT/BENEFIT.csv"), one_way=own(R / "M12_BENEFIT/BENEFIT.csv"), bound=own(B / "M12_BENEFIT/BENEFIT.csv"))); print(t.round(3).to_string()); print(t.sum().round(3).to_dict())


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


def tab(n):
    w = n.snapshot_weightings.generators; c = n.buses.country.astype(str); g = n.generators[n.generators.bus.map(c) == "LA"]
    e_ = n.generators_t.p[g.index.intersection(n.generators_t.p.columns)].mul(w, axis=0).sum().groupby(g.carrier.astype(str)).sum() / 1e6; p = g[g.p_nom_extendable].groupby(g.carrier.astype(str)).p_nom_opt.sum() / 1e3
    u = n.storage_units[n.storage_units.bus.map(c) == "LA"]; ue = n.storage_units_t.p_dispatch[u.index.intersection(n.storage_units_t.p_dispatch.columns)].mul(w, axis=0).sum().sum() / 1e6
    return dict(wind_gw=float(p.get("onwind", 0.0)), wind_twh=float(e_.get("onwind", 0.0) + e_.get("onwind existing", 0.0)), solar_gw=float(p.get("solar", 0.0)), solar_twh=float(e_.get("solar", 0.0)), ror_twh=float(e_.get("ror existing", 0.0) + e_.get("ror", 0.0)), reservoir_twh=float(ue), thermal=None)


N = {k: pypsa.Network(str(d / "no_new_xb/no_new_xb_SMOKE_TEST_ONLY_solved.nc")) for k, d in (("none", Z), ("two_way", O), ("one_way", R), ("bound", B))}
for k, n in N.items():
    t = la(n); print(k); print(t.to_string()); print("net", round(float(t.net.sum()), 2)); print(" ", {a: round(b, 2) if b is not None else b for a, b in tab(n).items()})
n = N["bound"]; w = n.snapshot_weightings.generators
K = n.links[n.links.carrier == "dedicated plant line"]; p = n.links_t.p0[K.index]; print(pd.DataFrame(dict(bus0=K.bus0, contract=K.p_nom, mean_mw=p.mean(), max_mw=p.max(), twh=p.mul(w, axis=0).sum() / 1e6, util=p.mean() / K.p_nom)).round(3).to_string()); print("lines TWh", round(float(p.mul(w, axis=0).sum().sum()) / 1e6, 2))
S = n.links[n.links.carrier == "dedicated plant source"]; q = n.links_t.p0[S.index]; print(pd.DataFrame(dict(p_nom=S.p_nom, mean_mw=q.mean(), max_mw=q.max(), twh=q.mul(w, axis=0).sum() / 1e6)).round(3).to_string()); print("source to grid TWh", round(float(q.mul(w, axis=0).sum().sum()) / 1e6, 2))
T = n.links[n.links.carrier.isin(["coal existing", "lignite existing"]) & n.links.index.str.contains("LA2")]; print("thermal out", {k: (round(float((n.links_t.p0[k] * T.at[k, "efficiency"]).mean()), 2), round(float((n.links_t.p0[k] * T.at[k, "efficiency"]).mul(w).sum()) / 1e6, 3)) for k in T.index})
for s in ("integrated", "no_new_xb"):
    L = pd.read_csv(B / s / "COUNTRY_COST_LEDGER_DETAIL.csv"); print(s, "ledger rows with the source carrier", int((L.astype(str) == "dedicated plant source").any(axis=1).sum()), "plant line rows", int((L.astype(str) == "dedicated plant line").any(axis=1).sum()))
print((B / "LA_EXPORT_UTILISATION.csv").read_text()[:1300])
