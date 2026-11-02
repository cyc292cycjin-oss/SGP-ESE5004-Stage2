"""v3 against v2 at the same 56 snapshots (read-only): EV energy closure, ship duals with the right dimension, cost by carrier, sector demand."""
import json, logging, sys
sys.path.insert(0, "/home/jin/wt_v3_20261102/scripts_project")
from pathlib import Path
import numpy as np, pandas as pd, pypsa, xarray as xr
logging.disable(logging.WARNING)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
V3 = M / "v3/smoke_r2"; V2 = M / "dfx_v3/smoke_v2"
N = {"v3_int": pypsa.Network(V3 / "integrated/integrated_SMOKE_TEST_ONLY_solved.nc"), "v2_int": pypsa.Network(V2 / "integrated/integrated_SMOKE_TEST_ONLY_solved.nc"),
     "v3_nnx": pypsa.Network(V3 / "no_new_xb/no_new_xb_SMOKE_TEST_ONLY_solved.nc"), "v2_dis": pypsa.Network(V2 / "disconnected/disconnected_SMOKE_TEST_ONLY_solved.nc")}
w = N["v3_int"].snapshot_weightings.generators
print("weight", float(w.iloc[0]))
# --- ship duals, right dimension
for sc in ("integrated", "no_new_xb"):
    ds = xr.open_dataset(V3 / sc / "DUALS_BY_CONSTRAINT.nc"); a = ds["Link-fix-p-upper"]; dim = "Link-fix-p-upper|Link-fix"
    names = pd.Index(a[dim].values.astype(str)); L = N["v3_int" if sc == "integrated" else "v3_nnx"].links
    ship = L.index[L.carrier.isin(["oil non-fossil ship", "methanol ship", "ammonia ship", "liquid transit rail"])]; sel = names.intersection(ship)
    x = a.sel({dim: sel}).values; other = a.sel({dim: names.difference(ship)}).values
    print(sc, "Link-fix-p-upper ship rows", len(sel), "cells", x.size, "nonzero", int((x != 0).sum()), "abs max", float(np.abs(x).max()), "| other links nonzero", int((other != 0).sum()), "abs max", float(np.abs(other).max()))
# --- EV energy closure
for k, n in N.items():
    L = n.links; ch = L[L.carrier == "BEV charger"]; st = n.stores[n.stores.carrier == "EV battery"]; ld = n.loads[n.loads.carrier == "land transport EV"]
    wk = n.snapshot_weightings.generators
    p0 = n.links_t.p0[ch.index.intersection(n.links_t.p0.columns)] if len(ch) else pd.DataFrame()
    drawn = float(p0.mul(wk, axis=0).sum().sum()) / 1e6 if len(ch) else 0.0
    delivered = float((p0 * ch.efficiency.reindex(p0.columns)).mul(wk, axis=0).sum().sum()) / 1e6 if len(ch) else 0.0
    load = float(n.get_switchable_as_dense("Load", "p_set")[ld.index].mul(wk, axis=0).sum().sum()) / 1e6
    print(k, "EV load", round(load, 3), "charger drawn", round(drawn, 3), "delivered", round(delivered, 3), "chargers", len(ch), "eff", sorted(set(ch.efficiency.round(4)))[:3], "ext", int(ch.p_nom_extendable.sum()), "p_nom GW", round(float(ch.p_nom_opt.sum()) / 1e3, 1), "stores", len(st))
    if len(st):
        e = n.stores_t.e[st.index]
        print("   store cyclic all", bool(st.e_cyclic.all()), "e_initial sum", float(st.e_initial.sum()), "e_nom GWh", round(float(st.e_nom_opt.sum()) / 1e3, 1), "e_nom ext", int(st.e_nom_extendable.sum()), "capital", float(st.capital_cost.max()), "e first GWh", round(float(e.iloc[0].sum()) / 1e3, 1), "e last GWh", round(float(e.iloc[-1].sum()) / 1e3, 1), "net p TWh", round(float(n.stores_t.p[st.index].mul(wk, axis=0).sum().sum()) / 1e6, 4))
        h = p0.sum(axis=1).groupby(p0.index.hour).mean() / 1e3
        print("   charge GW by UTC hour", h.round(1).to_dict())
    else:
        print("   charge GW by UTC hour", (p0.sum(axis=1).groupby(p0.index.hour).mean() / 1e3).round(1).to_dict())
# --- sector demand
for k in ("v3_int", "v2_int"):
    pass
g3 = json.loads((V3 / "integrated/V5_GATES.json").read_text())["B8"]["sector_totals"]; g2 = json.loads((V2 / "integrated/V5_GATES.json").read_text())["B8"]["sector_totals"]
print("sector TWh v2 -> v3", {k: (round(g2[k]["expected_mwh"] / 1e6, 2), round(g3[k]["expected_mwh"] / 1e6, 2)) for k in g3 if k in g2 and abs(g3[k]["expected_mwh"] - g2[k]["expected_mwh"]) > 1e5})
def lc(n):
    wk = n.snapshot_weightings.generators
    p = n.get_switchable_as_dense("Load", "p_set").mul(wk, axis=0).sum() / 1e6
    return p.groupby(n.loads.carrier.astype(str)).sum()
d = pd.DataFrame(dict(v2=lc(N["v2_int"]), v3=lc(N["v3_int"]))).fillna(0.0); d["d"] = d.v3 - d.v2
print(d[d.d.abs() > 0.05].round(2).to_string())
# --- cost by carrier
def cost(n):
    wo = n.snapshot_weightings.objective; rows = {}
    def add(c, cap, op):
        rows.setdefault(c, [0.0, 0.0]); rows[c][0] += cap; rows[c][1] += op
    for name, z in n.generators.iterrows():
        cap = z.capital_cost * z.p_nom_opt if z.p_nom_extendable else 0.0
        mc = (n.generators_t.marginal_cost[name] if name in n.generators_t.marginal_cost else z.marginal_cost)
        add("G " + str(z.carrier), cap, float((n.generators_t.p[name] * mc * wo).sum()) if name in n.generators_t.p else 0.0)
    for name, z in n.links.iterrows():
        cap = z.capital_cost * z.p_nom_opt if z.p_nom_extendable else 0.0
        add("L " + str(z.carrier), cap, float((n.links_t.p0[name] * z.marginal_cost * wo).sum()) if (name in n.links_t.p0 and z.marginal_cost) else 0.0)
    for name, z in n.stores.iterrows():
        add("S " + str(z.carrier), z.capital_cost * z.e_nom_opt if z.e_nom_extendable else 0.0, 0.0)
    for name, z in n.storage_units.iterrows():
        add("U " + str(z.carrier), z.capital_cost * z.p_nom_opt if z.p_nom_extendable else 0.0, float((n.storage_units_t.p_dispatch[name] * z.marginal_cost * wo).sum()) if name in n.storage_units_t.p_dispatch else 0.0)
    for name, z in n.lines.iterrows():
        add("Line", z.capital_cost * z.s_nom_opt if z.s_nom_extendable else 0.0, 0.0)
    return pd.DataFrame(rows, index=["cap", "op"]).T / 1e9
c3, c2 = cost(N["v3_int"]), cost(N["v2_int"])
t = pd.DataFrame(dict(v2=c2.sum(axis=1), v3=c3.sum(axis=1), d_cap=c3.cap.sub(c2.cap, fill_value=0.0), d_op=c3.op.sub(c2.op, fill_value=0.0))).fillna(0.0); t["d"] = t.d_cap + t.d_op
print("sum", t[["v2", "v3", "d_cap", "d_op", "d"]].sum().round(3).to_dict())
print(t.reindex(t.d.abs().sort_values(ascending=False).index).head(22).round(3).to_string())
# --- capacity
def cap(n):
    g = n.generators.groupby(n.generators.carrier.astype(str)).p_nom_opt.sum() / 1e3
    return g
a = pd.DataFrame(dict(v2=cap(N["v2_int"]), v3=cap(N["v3_int"]))).fillna(0.0); a["d"] = a.v3 - a.v2
print(a[a.d.abs() > 3].round(1).to_string())
l3 = N["v3_int"].links.groupby(N["v3_int"].links.carrier.astype(str)).p_nom_opt.sum() / 1e3; l2 = N["v2_int"].links.groupby(N["v2_int"].links.carrier.astype(str)).p_nom_opt.sum() / 1e3
b = pd.DataFrame(dict(v2=l2, v3=l3)); print(b.loc[[x for x in ("H2 Electrolysis", "battery charger", "H2 pipeline", "DC", "gas pipeline", "CO2 pipeline") if x in b.index]].round(1).to_string())
for k in ("v2_int", "v3_int", "v3_nnx", "v2_dis"):
    n = N[k]; lines = n.lines[n.lines.border_class == "cross_border"]; links = n.links[n.links.border_class == "cross_border"]
    print(k, "xb AC", round(float(lines.s_nom_opt.sum()) / 1e3, 1), {c: round(float(v) / 1e3, 1) for c, v in links.groupby(links.carrier.astype(str)).p_nom_opt.sum().items()})
