"""Supplement 02: why B6 moved little. LA net position before / after X1b in no_new_xb, hydro resource of the 56 snapshots against the year, LA dispatch. Read-only."""
import logging
from pathlib import Path
import pandas as pd, pypsa
logging.disable(logging.WARNING)
pd.set_option("display.width", 220, "display.max_columns", 40)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3")
N = {"before": pypsa.Network(M / "smoke_s1/no_new_xb/no_new_xb_SMOKE_TEST_ONLY_solved.nc"), "after": pypsa.Network(M / "smoke_s2/no_new_xb/no_new_xb_SMOKE_TEST_ONLY_solved.nc")}
for k, n in N.items():
    w = n.snapshot_weightings.generators; c = n.buses.country.astype(str); la = c == "LA"; rows = {}
    for name, z in n.lines[n.lines.border_class == "cross_border"].iterrows():
        a, b = c[z.bus0], c[z.bus1]
        if (a == "LA") != (b == "LA"):
            f = n.lines_t.p0[name] if a == "LA" else -n.lines_t.p0[name]; o = b if a == "LA" else a
            rows.setdefault(o, [0.0, 0.0]); rows[o][0] += float(f.clip(lower=0).mul(w).sum()) / 1e6; rows[o][1] += float((-f).clip(lower=0).mul(w).sum()) / 1e6
    K = n.links[(n.links.border_class == "cross_border") & (n.links.transport_carrier.astype(str) == "electricity")]
    for name, z in K.iterrows():
        a, b = c[z.bus0], c[z.bus1]
        if (a == "LA") != (b == "LA"):
            o = b if a == "LA" else a; rows.setdefault(o, [0.0, 0.0])
            if a == "LA":
                rows[o][0] += float(n.links_t.p0[name].clip(lower=0).mul(w).sum()) / 1e6
            else:
                rows[o][1] += float(n.links_t.p0[name].clip(lower=0).mul(w).sum()) / 1e6
    t = pd.DataFrame(rows, index=["export", "import"]).T; t["net"] = t.export - t.import_ if False else t["export"] - t["import"]; print(k, "LA exchange TWh"); print(t.round(2).to_string()); print("total net", round(float(t.net.sum()), 2))
    g = n.generators[n.generators.bus.map(c) == "LA"]; gp = n.generators_t.p[g.index.intersection(n.generators_t.p.columns)].mul(w, axis=0).sum().groupby(g.carrier.astype(str)).sum() / 1e6
    u = n.storage_units[n.storage_units.bus.map(c) == "LA"]; up = n.storage_units_t.p_dispatch[u.index.intersection(n.storage_units_t.p_dispatch.columns)].mul(w, axis=0).sum().groupby(u.carrier.astype(str)).sum() / 1e6
    l = n.links[(n.links.bus1.map(c) == "LA") & n.links.carrier.astype(str).isin(["lignite existing", "coal existing"])]; lp = (-n.links_t.p1[l.index]).mul(w, axis=0).sum().groupby(l.carrier.astype(str)).sum() / 1e6
    print("  LA gen TWh", gp[gp.abs() > 0.05].round(2).to_dict(), up.round(2).to_dict(), lp.round(2).to_dict(), "load TWh", round(float(n.get_switchable_as_dense("Load", "p_set")[n.loads.index[n.loads.bus.map(c) == "LA"]].mul(w, axis=0).sum().sum()) / 1e6, 2))
n = pypsa.Network(M / "builds_x1b/integrated/integrated_2920_3h_unsolved.nc"); c = n.buses.country.astype(str)
u = n.storage_units[(n.storage_units.bus.map(c) == "LA") & n.storage_units.carrier.astype(str).str.contains("hydro")]; i = n.storage_units_t.inflow[u.index.intersection(n.storage_units_t.inflow.columns)].sum(axis=1)
g = n.generators[(n.generators.bus.map(c) == "LA") & (n.generators.carrier.astype(str) == "ror existing")]; a = n.get_switchable_as_dense("Generator", "p_max_pu")[g.index].mul(g.p_nom, axis=1).sum(axis=1)
print("LA reservoir inflow MW: first 56", round(float(i.iloc[:56].mean())), "year", round(float(i.mean())), "ratio", round(float(i.iloc[:56].mean() / i.mean()), 3), "| ror available MW: first 56", round(float(a.iloc[:56].mean())), "year", round(float(a.mean())), "ratio", round(float(a.iloc[:56].mean() / a.mean()), 3))
print("first snapshots", n.snapshots[0], n.snapshots[55]); m = (i + a).groupby(n.snapshots.month).mean().round(0).to_dict(); print("LA hydro resource MW by month", m)
