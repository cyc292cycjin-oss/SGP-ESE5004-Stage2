"""Supplement 04, basis of the predictions after decision 179 (read-only, existing one-way smoke): line flows by plant node against the dry-week availability of the moved stock; APG exchange; what LA would have to rebuild."""
import logging
from pathlib import Path
import pandas as pd, pypsa
logging.disable(logging.WARNING)
pd.set_option("display.width", 220, "display.max_columns", 30)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3")
cap = pd.read_csv("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/SOURCE_CAPACITY_V3.csv").set_index("node")
for sc in ("no_new_xb", "integrated"):
    n = pypsa.Network(str(M / f"smoke_s3/{sc}/{sc}_SMOKE_TEST_ONLY_solved.nc")); w = n.snapshot_weightings.generators
    K = n.links[n.links.carrier == "dedicated plant line"]; p = n.links_t.p0[K.index]
    t = pd.DataFrame(dict(node=K.bus0, contract=K.p_nom, mean_mw=p.mean(), max_mw=p.max(), twh=p.mul(w, axis=0).sum() / 1e6))
    g = t.groupby("node")[["contract", "mean_mw", "twh"]].sum().join(cap[["avail_dry_week_mw"]]); g["excess_over_stock_mw"] = (g.mean_mw - g.avail_dry_week_mw).clip(lower=0.0)
    print(sc); print(t.round(2).to_string()); print(g.round(2).to_string()); print("lines TWh", round(float(t.twh.sum()), 2), "stock dry-week TWh/a", round(float(cap.avail_dry_week_mw.sum()) * 8760 / 1e6, 2))
    su = n.storage_units[n.storage_units.bus.astype(str).str.startswith("LA")]; ge = n.generators[n.generators.bus.astype(str).str.startswith("LA2")]
    print("  LA hydro out TWh", round(float(n.storage_units_t.p_dispatch[su.index].mul(w, axis=0).sum().sum()) / 1e6, 2), "gen by carrier TWh", (n.generators_t.p[ge.index.intersection(n.generators_t.p.columns)].mul(w, axis=0).sum().groupby(ge.carrier.astype(str)).sum() / 1e6).round(2).loc[lambda s: s > 0.01].to_dict())
    print("  LA wind+solar capacity GW", (ge[ge.p_nom_extendable].groupby(ge.carrier.astype(str)).p_nom_opt.sum() / 1e3).round(2).loc[lambda s: s > 0.01].to_dict())
    x = n.lines[n.lines.border_class == "cross_border"]; c = n.buses.country.astype(str)
    r = {}
    for k, z in x.iterrows():
        a, b = c[z.bus0], c[z.bus1]
        if (a == "LA") != (b == "LA"):
            f = n.lines_t.p0[k] if a == "LA" else -n.lines_t.p0[k]; q = b if a == "LA" else a; d = r.setdefault(q, dict(export=0.0, imp=0.0, cap=0.0)); d["export"] += float(f.clip(lower=0).mul(w).sum()) / 1e6; d["imp"] += float((-f).clip(lower=0).mul(w).sum()) / 1e6; d["cap"] += float(z.s_nom_opt * z.s_max_pu)
    print("  lines by country", {k: {a: round(b, 2) for a, b in v.items()} for k, v in r.items()})
    pr = n.buses_t.marginal_price; la = [b for b in cap.index]; th = ["TH2 1", "TH2 4"]
    print("  mean node price", pr[la + th + ["VN2 2"]].mean().round(1).to_dict())
