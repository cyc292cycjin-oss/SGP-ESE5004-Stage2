"""Read-only, for the X1 decision: how tight is each cross-border stock pair in the no_new_xb smoke (one January week), and how much Lao plant sits behind LA-TH. No solve, no network change."""
import json, logging, sys
sys.path.insert(0, "/home/jin/wt_v3_20261102/scripts_project")
from pathlib import Path
import numpy as np, pandas as pd, pypsa
logging.disable(logging.WARNING)
pd.set_option("display.width", 200, "display.max_columns", 20, "display.max_rows", 60)
R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/smoke_r2")
n = pypsa.Network(R / "no_new_xb/no_new_xb_SMOKE_TEST_ONLY_solved.nc")
w = n.snapshot_weightings.objective
c = n.buses.country.astype(str); rows = []
L = n.lines[n.lines.border_class == "cross_border"]
for name, z in L.iterrows():
    cap = float(z.s_nom) * float(z.s_max_pu); f = n.lines_t.p0[name]
    mu = (n.lines_t["mu_upper"][name].abs() + n.lines_t["mu_lower"][name].abs()).div(w) if "mu_upper" in n.lines_t and name in n.lines_t["mu_upper"] else pd.Series(0.0, index=n.snapshots)
    rows.append(dict(pair="-".join(sorted((c[z.bus0], c[z.bus1]))), kind="AC", cap=cap, f=f, mu=mu))
K = n.links[(n.links.border_class == "cross_border") & (n.links.transport_carrier.astype(str) == "electricity")] if "transport_carrier" in n.links else n.links.iloc[0:0]
for name, z in K.iterrows():
    cap = float(z.p_nom); f = n.links_t.p0[name]
    mu = (n.links_t["mu_upper"][name].abs() + n.links_t["mu_lower"][name].abs()).div(w)
    rows.append(dict(pair="-".join(sorted((c[z.bus0], c[z.bus1]))), kind="DC", cap=cap, f=f, mu=mu))
out = []
for p, g in pd.DataFrame(rows).groupby("pair"):
    cap = sum(g.cap); util = sum(x.abs() for x in g.f) / cap
    bind = np.mean([(x > 1e-3) for x in g.mu], axis=0)   # binding = non-zero bound dual; a static s_nom x s_max_pu is not the limit when s_max_pu varies in time
    out.append(dict(pair=p, lines=len(g), kinds="+".join(sorted(set(g.kind))), cap_mw=round(cap, 1), mean_util=round(float(util.mean()), 3), max_util=round(float(util.max()), 3), share_line_hours_binding=round(float(bind.mean()), 3), mean_shadow_eur_mwh=round(float(np.mean([x.mean() for x in g.mu])), 2), max_shadow_eur_mwh=round(float(np.max([x.max() for x in g.mu])), 2)))
print("s_max_pu static", n.lines.s_max_pu[L.index].round(3).unique()[:6], "time-varying lines", len(n.lines_t.s_max_pu.columns.intersection(L.index)), "range", (float(n.lines_t.s_max_pu[n.lines_t.s_max_pu.columns.intersection(L.index)].min().min()), float(n.lines_t.s_max_pu[n.lines_t.s_max_pu.columns.intersection(L.index)].max().max())) if len(n.lines_t.s_max_pu.columns.intersection(L.index)) else None)
t = pd.DataFrame(out).sort_values("mean_shadow_eur_mwh", ascending=False); print(t.to_string(index=False))
t.to_csv("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/X1_CORRIDOR_LOADING_NO_NEW_XB_56.csv", index=False)
G = n.generators; cg = G.bus.map(c); su = n.storage_units; cs = su.bus.map(c)
for k in ("LA", "MM"):
    print(k, "gen GW by carrier", (G[cg == k].groupby(G.carrier.astype(str)).p_nom_opt.sum() / 1e3).round(2).loc[lambda s: s > 0.05].to_dict(), "hydro units GW", round(float(su[cs == k].p_nom_opt.sum()) / 1e3, 2))
    p = n.get_switchable_as_dense("Load", "p_set"); l = n.loads[n.loads.bus.map(c) == k]; print("  mean load GW", round(float(p[l.index].sum(axis=1).mean()) / 1e3, 2))
la = n.buses_t.marginal_price[[b for b in n.buses.index if n.buses.at[b, "carrier"] == "AC" and c[b] == "LA"]].mean(axis=1); th = n.buses_t.marginal_price[[b for b in n.buses.index if n.buses.at[b, "carrier"] == "AC" and c[b] == "TH"]].mean(axis=1)
print("AC price mean EUR/MWh LA", round(float(la.mean()), 1), "TH", round(float(th.mean()), 1))
