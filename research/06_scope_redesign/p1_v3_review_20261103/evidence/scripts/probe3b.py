"""Independent review probe 3b: solved V1 / V2 networks (first screening batch): curtailment, capacity mix, H2 / synfuel volumes, LA exchange, EV store behaviour, liquid flows, ledger spot checks."""
import json, logging
import numpy as np, pandas as pd, pypsa
logging.disable(logging.WARNING)
OUT = "/home/jin/v3rev/out/probe3b.json"
R = {}
for run, p in (("V1", "/home/jin/v3rev/cloud/solved/integrated_DFX_365X24H_solved.nc"), ("V2", "/home/jin/v3rev/cloud/solved/no_new_xb_DFX_365X24H_solved.nc")):
    n = pypsa.Network(p); z = {}
    w = n.snapshot_weightings.generators; cty = n.buses.country.astype(str)
    z["objective"] = float(n.objective); z["objective_constant"] = float(getattr(n, "objective_constant", np.nan))
    G = n.generators; gp = n.generators_t.p
    gc = G.carrier.astype(str); gcty = G.bus.map(cty)
    # capacity by carrier x country (GW), extendable new vs existing
    cap = G.assign(gw=G.p_nom_opt / 1e3, c=gcty).groupby(["carrier", "c"]).gw.sum().unstack(fill_value=0.0)
    z["gen_capacity_gw"] = {k: {c: round(float(v), 2) for c, v in r.items() if v > 0.05} for k, r in cap.iterrows() if r.sum() > 0.5}
    # generation TWh by carrier x country
    gen = gp.mul(w, axis=0).sum() / 1e6
    z["gen_twh_by_carrier"] = {k: round(float(v), 2) for k, v in gen.groupby(gc).sum().sort_values(ascending=False).items() if abs(v) > 0.5}
    z["gen_twh_by_country"] = {k: round(float(v), 1) for k, v in gen.groupby(gcty).sum().items()}
    # curtailment of VRE: available - dispatched
    vre = G[gc.str.contains("solar|onwind|offwind", regex=True)]
    pmax = n.get_switchable_as_dense("Generator", "p_max_pu")[vre.index]
    avail = (pmax * vre.p_nom_opt).mul(w, axis=0).sum() / 1e6; disp = gp[vre.index].mul(w, axis=0).sum() / 1e6
    cur = (avail - disp)
    z["vre_curtailment_twh"] = dict(total=float(cur.sum()), available=float(avail.sum()), share=float(cur.sum() / avail.sum()), by_country={k: round(float(v), 2) for k, v in cur.groupby(vre.bus.map(cty)).sum().items()}, by_carrier={k: round(float(v), 2) for k, v in cur.groupby(vre.carrier).sum().items()})
    # link capacities / flows by carrier (GW, TWh at bus0)
    L = n.links; lp0 = n.links_t.p0; lc = L.carrier.astype(str)
    e0 = lp0.mul(w, axis=0).sum() / 1e6
    z["link_twh_in_by_carrier"] = {k: round(float(v), 2) for k, v in e0.groupby(lc).sum().sort_values(ascending=False).items() if abs(v) > 1.0}
    z["link_gw_opt_by_carrier"] = {k: round(float(v / 1e3), 2) for k, v in L.p_nom_opt.groupby(lc).sum().sort_values(ascending=False).items() if v > 500}
    for car in ("H2 Electrolysis", "Fischer-Tropsch", "methanolisation", "Haber-Bosch", "biomass-to-methanol", "DAC", "direct air capture", "SMR", "SMR CC", "OCGT", "CCGT", "H2 turbine", "H2 Fuel Cell", "battery charger", "BEV charger", "ammonia cracker"):
        s = L[lc == car]
        if len(s):
            z.setdefault("link_by_country", {})[car] = dict(gw={k: round(float(v / 1e3), 2) for k, v in s.p_nom_opt.groupby(s.bus0.map(cty).fillna(s.bus1.map(cty))).sum().items() if v > 50}, twh_in={k: round(float(v), 2) for k, v in e0[s.index].groupby(s.bus0.map(cty).fillna(s.bus1.map(cty))).sum().items() if abs(v) > 0.5})
    # stores
    S = n.stores; z["store_e_nom_opt_gwh_by_carrier"] = {k: round(float(v / 1e3), 1) for k, v in S.e_nom_opt.groupby(S.carrier.astype(str)).sum().sort_values(ascending=False).items() if v > 1e3}
    # EV store behaviour
    ev = S[S.carrier == "EV battery"]; e = n.stores_t.e[ev.index]; emin = n.stores_t.e_min_pu.reindex(columns=ev.index).fillna(0.0) * ev.e_nom
    z["ev"] = dict(e_nom_twh=float(ev.e_nom.sum() / 1e6), min_margin_mwh=float((e - emin).min().min()), day_end_above_floor_sum_twh_max=float((e - emin).sum(axis=1).max() / 1e6), positive_change_sum_twh=float(e.diff().clip(lower=0).sum().sum() / 1e6), cyclic_gap=float((e.iloc[-1] - e.iloc[0]).abs().max()))
    ch = L[lc == "BEV charger"]; z["ev_charger"] = dict(twh_in=float(e0[ch.index].sum()), max_util=float((lp0[ch.index] / ch.p_nom).max().max()), mean_util=float((lp0[ch.index].mean() / ch.p_nom).mean()))
    # cross-border electricity exchange LA
    xb = L[(L.border_class == "cross_border") & (L.transport_carrier.astype(str) == "electricity")]
    xl = n.lines[n.lines.border_class == "cross_border"]
    def pair_flows(df, flow, is_line):
        rows = {}
        for name, r in df.iterrows():
            a, b = cty[r.bus0], cty[r.bus1]; k = "-".join(sorted((a, b))); f = flow[name].mul(w).sum() / 1e6
            if is_line:
                out = f if a < b else -f
            else:
                out = f if a < b else -f
            rows.setdefault(k, 0.0); rows[k] += float(out)
        return rows
    lf = pair_flows(xl, n.lines_t.p0, True); kf = pair_flows(xb[~xb.index.str.endswith("-reversed")], lp0, False); kr = pair_flows(xb[xb.index.str.endswith("-reversed")], lp0, False)
    z["xb_elec_net_twh_first_to_second"] = dict(lines=lf, links_fwd=kf, links_rev=kr)
    xf = xb[~xb.index.str.endswith("-reversed")]
    z["xb_elec_capacity_gw"] = dict(lines={k: round(float(v / 1e3), 2) for k, v in xl.s_nom_opt.groupby(pd.Series([("-".join(sorted((cty[a], cty[b])))) for a, b in zip(xl.bus0, xl.bus1)], index=xl.index)).sum().items()},
                                    links={k: round(float(v / 1e3), 2) for k, v in xf.p_nom_opt.groupby(pd.Series([("-".join(sorted((cty[a], cty[b])))) for a, b in zip(xf.bus0, xf.bus1)], index=xf.index)).sum().items()})
    la_bal = {}
    for name, r in pd.concat([xl.assign(t="Line"), xb.assign(t="Link")]).iterrows():
        a, b = cty[r.bus0], cty[r.bus1]
        if "LA" not in (a, b):
            continue
        fl = (n.lines_t.p0 if r.t == "Line" else lp0)[name]
        exp = fl.clip(lower=0).mul(w).sum() if a == "LA" else (-fl).clip(lower=0).mul(w).sum()
        imp = (-fl).clip(lower=0).mul(w).sum() if a == "LA" else fl.clip(lower=0).mul(w).sum()
        if r.t == "Line":
            exp, imp = (exp, imp)
        k = f"LA-{b if a == 'LA' else a}:{r.carrier}"; la_bal.setdefault(k, [0.0, 0.0]); la_bal[k][0] += float(exp / 1e6); la_bal[k][1] += float(imp / 1e6)
    z["la_exchange_twh_export_import"] = la_bal
    # dedicated line utilisation and source bus
    dd = L[lc == "dedicated plant line"]; z["dedicated_twh"] = {k: round(float(v), 3) for k, v in e0[dd.index].items()}; z["dedicated_util"] = {k: round(float(e0[k] * 1e6 / (dd.at[k, "p_nom"] * 8760)), 3) for k in dd.index}
    src = L[lc == "dedicated plant source"]; z["source_link_twh"] = {k: round(float(v), 3) for k, v in e0[src.index].items()}
    # liquid flows: ships by carrier, imports, production
    ships = L[lc.isin(["methanol ship", "ammonia ship", "oil non-fossil ship", "liquid transit rail"])]
    z["ship_twh_by_carrier"] = {k: round(float(v), 2) for k, v in e0[ships.index].groupby(ships.carrier).sum().items()}
    z["ship_max_util"] = float((lp0[ships.index] / ships.p_nom).max().max())
    z["ship_twh_top_routes"] = {k: round(float(v), 2) for k, v in e0[ships.index].sort_values(ascending=False).head(12).items()}
    imp = G[gc.str.contains("import")]; z["import_twh_by_carrier_country"] = {k: {c: round(float(v), 2) for c, v in r.items() if v > 0.01} for k, r in gen[imp.index].groupby([imp.carrier, imp.bus.map(cty)]).sum().unstack(fill_value=0.0).iterrows()}
    # national liquid bus prices (annual mean, weighted)
    mp = n.buses_t.marginal_price
    for car in ("methanol", "ammonia", "oil non-fossil", "oil"):
        b = n.buses[(n.buses.carrier == car) & n.buses.index.str.match(r"^[A-Z]{2} ")]
        z[f"price_{car}"] = {k: round(float((mp[k] * w).sum() / w.sum()), 2) for k in b.index}
    ac = n.buses[n.buses.carrier == "AC"]
    pm = (mp[ac.index].mul(w, axis=0).sum() / w.sum())
    z["elec_price_country_mean_minmax"] = {c: [round(float(pm[g.index].mean()), 2), round(float(mp[g.index].min().min()), 1), round(float(mp[g.index].max().max()), 1)] for c, g in ac.groupby("country")}
    z["elec_price_std_over_time_country"] = {c: round(float(mp[g.index].std().mean()), 2) for c, g in ac.groupby("country")}
    # emissions: atmosphere final level, DAC, sequestration, bunker
    atm = S[S.carrier == "co2 atmosphere"]; z["atmosphere_final_level_t"] = {k: float(v) for k, v in n.stores_t.e[atm.index].iloc[-1].items()}
    seq = S[S.carrier == "co2 sequestered"]; z["sequestered_final_mt"] = {k: round(float(v / 1e6), 2) for k, v in n.stores_t.e[seq.index].iloc[-1].items()}
    seqx = S[S.carrier == "co2 sequestered extra-ASEAN"]; z["sequestered_extra_asean_final_mt"] = {k: round(float(v / 1e6), 3) for k, v in n.stores_t.e[seqx.index].iloc[-1].items() if v > 1}
    z["bunker_final_level_t"] = float(n.stores_t.e["co2 bunkers ASEAN"].iloc[-1]) if "co2 bunkers ASEAN" in S.index else None
    dac = L[lc.str.contains("DAC|direct air", regex=True)]; z["dac_mt_by_country"] = {k: round(float(v), 2) for k, v in (e0[dac.index]).groupby(dac.bus0.map(cty).fillna(dac.bus1.map(cty))).sum().items()} if len(dac) else {}
    z["dac_carriers"] = sorted(set(dac.carrier))
    # bunker loads supply: aviation non-fossil vs fossil meters
    met = L[lc == "oil final-energy accounting"]; av = met[met.index.str.contains("aviation international")]
    z["aviation_intl_meter_twh"] = dict(fossil=float(e0[av[~av.bus0.str.contains("non-fossil")].index].sum()), nonfossil=float(e0[av[av.bus0.str.contains("non-fossil")].index].sum()))
    # ledger spot: existing FOM constants and xb fom present in objective? compare objective with sum of components
    capex = 0.0
    for t, nom in (("Generator", "p_nom"), ("Link", "p_nom"), ("Line", "s_nom"), ("Store", "e_nom"), ("StorageUnit", "p_nom")):
        d = n.df(t); capex += float(((d[nom + "_opt"] - d[nom]) * d.capital_cost).where(d[nom + "_extendable"], 0.0).sum())
    varc = 0.0
    for t, fl in (("Generator", "p"), ("Link", "p0"), ("Store", "p"), ("StorageUnit", "p_dispatch")):
        mc = n.get_switchable_as_dense(t, "marginal_cost"); f = n.pnl(t)[fl].reindex(columns=mc.columns, fill_value=0.0); varc += float((f * mc).mul(w, axis=0).sum().sum())
    fom = float(n.meta.get("existing_annual_fixed_om_eur", 0.0)) + float(n.meta.get("existing_cross_border_fom_eur", 0.0))
    z["objective_decomposition_bn"] = dict(capex_new=capex / 1e9, variable=varc / 1e9, fom_constants=fom / 1e9, sum=(capex + varc + fom) / 1e9, objective=float(n.objective) / 1e9, gap=(capex + varc + fom - float(n.objective)) / 1e9)
    # top variable cost carriers
    vc = {}
    for t, fl in (("Generator", "p"), ("Link", "p0")):
        mc = n.get_switchable_as_dense(t, "marginal_cost"); f = n.pnl(t)[fl].reindex(columns=mc.columns, fill_value=0.0); v = (f * mc).mul(w, axis=0).sum()
        for k, val in v.groupby(n.df(t).carrier.astype(str).reindex(v.index)).sum().items():
            vc[k] = vc.get(k, 0.0) + float(val)
    z["variable_cost_bn_by_carrier_top"] = {k: round(v / 1e9, 3) for k, v in sorted(vc.items(), key=lambda kv: -abs(kv[1]))[:15]}
    cx = {}
    for t, nom in (("Generator", "p_nom"), ("Link", "p_nom"), ("Line", "s_nom"), ("Store", "e_nom"), ("StorageUnit", "p_nom")):
        d = n.df(t); v = ((d[nom + "_opt"] - d[nom]) * d.capital_cost).where(d[nom + "_extendable"], 0.0)
        for k, val in v.groupby(d.carrier.astype(str)).sum().items():
            cx[k] = cx.get(k, 0.0) + float(val)
    z["capex_bn_by_carrier_top"] = {k: round(v / 1e9, 3) for k, v in sorted(cx.items(), key=lambda kv: -abs(kv[1]))[:15]}
    R[run] = z
json.dump(R, open(OUT, "w"), indent=1, default=str)
print("done")
