"""Supplement 01, read-only: EV effect (flat - E2) and remainder (flat - v2) by carrier at the same 56 snapshots, EV energy closure, capacities, marine liquids, duals used in the Owen reading."""
import json, logging
from pathlib import Path
import pandas as pd, pypsa
logging.disable(logging.WARNING)
pd.set_option("display.width", 220, "display.max_columns", 40, "display.max_rows", 200)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
V3 = M / "v3/smoke_s1"; V2 = M / "dfx_v3/smoke_v2"; O = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/smoke_s1")
N = {"e2": pypsa.Network(V3 / "integrated/integrated_SMOKE_TEST_ONLY_solved.nc"), "flat": pypsa.Network(V3 / "integrated_flat/integrated_SMOKE_TEST_ONLY_solved.nc"), "v2": pypsa.Network(V2 / "integrated/integrated_SMOKE_TEST_ONLY_solved.nc"),
     "e2_nnx": pypsa.Network(V3 / "no_new_xb/no_new_xb_SMOKE_TEST_ONLY_solved.nc"), "flat_nnx": pypsa.Network(V3 / "no_new_xb_flat/no_new_xb_SMOKE_TEST_ONLY_solved.nc")}


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


C = {k: cost(n) for k, n in N.items()}
T = pd.DataFrame({k: C[k].sum(axis=1) for k in C}).fillna(0.0)
T["ev_int"] = T.flat - T.e2; T["ev_nnx"] = T.flat_nnx - T.e2_nnx; T["rest"] = T.flat - T.v2
print("sum", T.sum().round(4).to_dict())
for key in ("ev_int", "rest"):
    print("---", key); print(T.reindex(T[key].abs().sort_values(ascending=False).index).head(16)[["v2", "flat", "e2", "ev_int", "ev_nnx", "rest"]].round(3).to_string())
T.round(5).to_csv(O / "COST_BY_CARRIER_V2_FLAT_E2.csv")


def gen_cap(n):
    return n.generators.groupby(n.generators.carrier.astype(str)).p_nom_opt.sum() / 1e3


def gen_twh(n):
    w = n.snapshot_weightings.generators
    return n.generators_t.p.mul(w, axis=0).sum().groupby(n.generators.carrier.astype(str)).sum() / 1e6


a = pd.DataFrame({k: gen_cap(N[k]) for k in ("v2", "flat", "e2")}).fillna(0.0); print((a[(a.e2 - a.flat).abs().gt(2) | (a.flat - a.v2).abs().gt(2)]).round(1).to_string())
b = pd.DataFrame({k: gen_twh(N[k]) for k in ("v2", "flat", "e2")}).fillna(0.0); print(b[(b.e2 - b.flat).abs().gt(5) | (b.flat - b.v2).abs().gt(5)].round(1).to_string())
L = {k: N[k].links.groupby(N[k].links.carrier.astype(str)).p_nom_opt.sum() / 1e3 for k in ("v2", "flat", "e2")}
c = pd.DataFrame(L).fillna(0.0)
print(c.loc[[x for x in ("H2 Electrolysis", "battery charger", "battery discharger", "H2 pipeline", "DC", "methanolisation", "OCGT", "CCGT", "CCGT existing", "BEV charger", "Fischer-Tropsch", "SMR", "SMR CC", "DAC") if x in c.index]].round(1).to_string())
s = pd.DataFrame({k: N[k].stores.groupby(N[k].stores.carrier.astype(str)).e_nom_opt.sum() / 1e3 for k in ("v2", "flat", "e2")}).fillna(0.0)
print(s[(s.e2 - s.flat).abs().gt(5) | (s.flat - s.v2).abs().gt(5)].round(1).to_string())
for k in ("v2", "flat", "e2"):
    n = N[k]; L0 = n.links; ch = L0[L0.carrier == "BEV charger"]; st = n.stores[n.stores.carrier == "EV battery"]; ld = n.loads[n.loads.carrier == "land transport EV"]; w = n.snapshot_weightings.generators
    p0 = n.links_t.p0[ch.index.intersection(n.links_t.p0.columns)]
    print(k, "EV load TWh", round(float(n.get_switchable_as_dense("Load", "p_set")[ld.index].mul(w, axis=0).sum().sum()) / 1e6, 3), "charger drawn", round(float(p0.mul(w, axis=0).sum().sum()) / 1e6, 3), "chargers GW", round(float(ch.p_nom_opt.sum()) / 1e3, 1), "peak draw GW", round(float(p0.sum(axis=1).max()) / 1e3, 1), "store e_nom GWh", round(float(st.e_nom_opt.sum()) / 1e3, 1))
for k in ("flat", "e2"):
    n = N[k]; ac = n.generators[n.generators.carrier.astype(str).str.contains("solar|onwind|offwind|hydro|ror")]
    cf = n.generators_t.p[ac.index.intersection(n.generators_t.p.columns)]; av = n.get_switchable_as_dense("Generator", "p_max_pu")[cf.columns] * ac.p_nom_opt.reindex(cf.columns); w = n.snapshot_weightings.generators
    print(k, "VRE available TWh", round(float(av.mul(w, axis=0).sum().sum()) / 1e6, 1), "used", round(float(cf.mul(w, axis=0).sum().sum()) / 1e6, 1), "curtailed share", round(1 - float(cf.mul(w, axis=0).sum().sum()) / float(av.mul(w, axis=0).sum().sum()), 4))
e = json.loads((O / "V3_SMOKE_RESULT.json").read_text())
for rid in ("integrated", "no_new_xb", "integrated_flat", "no_new_xb_flat"):
    d = e[rid]["liquid_dual_annual_mean_eur_per_mwh"]; print(rid, {c: {k: round(d[c][k], 2) for k in ("ID", "MY", "SG")} for c in ("methanol", "ammonia", "oil non-fossil")})
b = pd.read_csv(O / "V3_LIQUID_BALANCE.csv"); print(b.columns.tolist())
print(b[b.term == "ship out"].groupby(["scenario", "carrier"]).twh.sum().round(1).to_dict())
print(b[(b.country == "SG")].groupby(["scenario", "carrier", "term"]).twh.sum().round(1).loc[lambda s: s.abs() > 0.05].to_dict())
