"""V3 phase 1 (read only): facts of the v2 DFX networks for V3_CODE_LOCATIONS / V3_DATA_INTAKE / V3_DESIGN. No solver."""
import json, sys, logging
from pathlib import Path
import numpy as np, pandas as pd, pypsa
logging.disable(logging.WARNING)
R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
OUT = R / "v3/phase1"; OUT.mkdir(parents=True, exist_ok=True)
P = R / "dfx_v3/builds_v2"
n = pypsa.Network(str(P / "integrated/integrated_2920_3h_unsolved.nc"))
d = pypsa.Network(str(P / "disconnected/disconnected_2920_3h_unsolved.nc"))
res = {}
sn = n.snapshots
res["snapshots"] = dict(n=len(sn), first=str(sn[0]), last=str(sn[-1]), tz=str(getattr(sn, "tz", None)), weights=sorted(set(n.snapshot_weightings.objective.tolist())))
res["components"] = {c.name: [int(len(c.df))] for c in n.iterate_components()}
for c in d.iterate_components():
    res["components"].setdefault(c.name, [0]).append(int(len(c.df)))
b = n.buses
res["bus_carriers"] = b.carrier.astype(str).value_counts().to_dict()
asean = b.index[b.country.astype(str) == "ASEAN"].tolist(); res["asean_buses"] = asean


def attached(net, bus):
    out = {}
    for t in ["Generator", "Load", "Store"]:
        df = net.df(t); x = df[df.bus == bus]
        if len(x):
            out[t] = x.carrier.astype(str).value_counts().to_dict()
    L = net.links; lab = {}
    for col in [c for c in L if c.startswith("bus") and c[3:].isdigit()]:
        x = L[L[col] == bus]
        for car, k in x.carrier.astype(str).value_counts().items():
            lab[f"{col}:{car}"] = int(k)
    if lab:
        out["Link"] = lab
    return out


res["asean_attached"] = {x: attached(n, x) for x in asean}
L = n.links
op = L[L.carrier == "oil pool"]
res["oil_pool_links"] = dict(n=len(op), sample=op.iloc[0][["bus0", "bus1", "p_nom", "p_nom_extendable", "p_nom_max", "p_min_pu", "marginal_cost", "capital_cost", "efficiency", "border_class"]].astype(str).to_dict())
for g in ["ASEAN oil import", "ASEAN methanol import", "ASEAN ammonia import", "ASEAN oil non-fossil import"]:
    if g in n.generators.index:
        z = n.generators.loc[g]; res.setdefault("imports", {})[g] = dict(marginal=float(z.marginal_cost), p_nom_ext=bool(z.p_nom_extendable), p_nom_max=float(z.p_nom_max))
# cross-border inventory
rows = []
for t, nom in (("Line", "s_nom"), ("Link", "p_nom")):
    df = n.df(t); x = df[df.border_class == "cross_border"]
    for name, z in x.iterrows():
        rows.append(dict(type=t, name=name, carrier=str(z.carrier), transport=str(z.transport_carrier), bus0=z.bus0, bus1=z.bus1, c0=str(n.buses.at[z.bus0, "country"]), c1=str(n.buses.at[z.bus1, "country"]),
                         nom=float(z[nom]), nom_min=float(z[nom + "_min"]), nom_max=float(z[nom + "_max"]), ext=bool(z[nom + "_extendable"]), length=float(z.length),
                         kind=str(z.get("gas_pipeline_kind", "")), reversed=bool(z.get("reversed", False)), capital_cost=float(z.capital_cost)))
X = pd.DataFrame(rows); X.to_csv(OUT / "V2_CROSS_BORDER_COMPONENTS.csv", index=False)
fwd = X[~X.reversed]
res["cross_border"] = dict(by_carrier=fwd.groupby(["type", "carrier"]).size().rename("n").reset_index().to_dict("records"),
                           stock=fwd[(fwd.nom_min > 0) | (fwd.kind == "existing_2025")].groupby(["type", "carrier"]).agg(n=("nom", "size"), mw=("nom", "sum")).reset_index().to_dict("records"),
                           fom_eur=float(n.meta.get("existing_cross_border_fom_eur", 0.0)), rows_reversed=int(X.reversed.sum()))
st = fwd[(fwd.nom_min > 0) | (fwd.kind == "existing_2025")].assign(pair=lambda t: [("-".join(sorted([a, b]))) for a, b in zip(t.c0, t.c1)])
st.to_csv(OUT / "V2_CROSS_BORDER_STOCK.csv", index=False)
res["cross_border"]["stock_by_pair_mw"] = st.groupby(["pair", "carrier"]).nom.sum().round(1).reset_index().to_dict("records")
res["maritime_trade"] = L[L.border_class == "maritime_trade"].carrier.astype(str).value_counts().to_dict()
# EV / BEV
ev = n.loads[n.loads.carrier == "land transport EV"]; chg = L[L.carrier == "BEV charger"]
res["bev"] = dict(ev_loads=len(ev), ev_static_p_set_nonzero=int((ev.p_set > 0).sum()), ev_in_loads_t=int(sum(1 for x in ev.index if x in n.loads_t.p_set.columns)), ev_twh=float(ev.p_set.sum() * 8760 / 1e6),
                  chargers=len(chg), charger_p_max_pu=sorted(set(chg.p_max_pu.round(6).tolist()))[:5], charger_eff=sorted(set(chg.efficiency.round(6).tolist()))[:5], charger_p_nom=float(chg.p_nom.sum()),
                  charger_ext=int(chg.p_nom_extendable.sum()), charger_capital=sorted(set(chg.capital_cost.round(3).tolist()))[:3],
                  ev_battery_stores=int((n.stores.carrier.astype(str).str.contains("EV|battery storage")).sum()), ev_store_carriers=sorted(set(n.stores.carrier.astype(str))),
                  v2g_links=int(L.carrier.astype(str).str.contains("V2G").sum()))
# time convention: mean diurnal profile of solar availability and base load per country
ac = b[(b.carrier == "AC")]
sol = n.generators[n.generators.carrier == "solar"]; pmax = n.generators_t.p_max_pu
diur = {}
for c in sorted(set(ac.country)):
    s_ = [g for g in sol.index if str(n.generators.at[g, "country"] if "country" in n.generators else "") == c and g in pmax.columns] or [g for g in sol.index if g in pmax.columns and str(n.buses.at[sol.at[g, "bus"], "country"]) == c]
    prof = pmax[s_].mean(axis=1).groupby(sn.hour).mean() if s_ else pd.Series(dtype=float)
    lds = [l for l in n.loads.index[(n.loads.account == "Astar") & (n.loads.country == c)] if l in n.loads_t.p_set.columns]
    lp = n.loads_t.p_set[lds].sum(axis=1).groupby(sn.hour).mean() if lds else pd.Series(dtype=float)
    diur[c] = dict(solar_peak_hour_snapshot=int(prof.idxmax()) if len(prof) else None, load_peak_hour_snapshot=int(lp.idxmax()) if len(lp) else None, load_min_hour_snapshot=int(lp.idxmin()) if len(lp) else None,
                   lon=float(ac[ac.country == c].x.mean()), nodes=int((ac.country == c).sum()))
res["diurnal"] = diur
# node table
gen = b[b.carrier.isin(["AC", "DC"])][["carrier", "country", "x", "y"]]
gen.to_csv(OUT / "V2_NODES.csv")
res["nodes_by_country"] = gen.groupby("country").size().to_dict()
res["nodes_ac_by_country"] = gen[gen.carrier == "AC"].groupby("country").size().to_dict()
# stores on liquid buses and per-carrier link counts relevant for the size estimate
res["link_carriers"] = L.carrier.astype(str).value_counts().to_dict()
res["store_carriers"] = n.stores.carrier.astype(str).value_counts().to_dict()
res["load_carriers_twh"] = {k: float(v) for k, v in (n.get_switchable_as_dense("Load", "p_set").mul(n.snapshot_weightings.generators, axis=0).sum().groupby(n.loads.carrier).sum() / 1e6).items()}
bk = n.meta.get("research_bunkers", {})
res["bunkers"] = dict(mode=bk.get("mode"), asean_loads=bk.get("asean_loads"), by_country=bk.get("by_country"))
res["hooks"] = n.meta.get("required_constraint_hooks")
Path(OUT / "V2_NETWORK_FACTS.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False))
print(json.dumps({k: res[k] for k in ("snapshots", "components", "asean_buses", "oil_pool_links", "imports", "maritime_trade", "bev", "diurnal", "nodes_by_country", "hooks")}, indent=0, default=str, ensure_ascii=False)[:9000])
print(json.dumps(res["cross_border"], indent=0, default=str)[:4500])
print(json.dumps(res["asean_attached"], indent=0, default=str)[:3500])
print(json.dumps(res["bunkers"], indent=0, default=str)[:2500])
