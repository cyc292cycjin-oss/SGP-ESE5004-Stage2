"""Independent review probe 1 (read-only): time weights, stock pinning, scenario diff incl. time series, EV store bounds, hooks."""
import json, sys, logging
import numpy as np, pandas as pd, pypsa
logging.disable(logging.WARNING)
OUT = "/home/jin/v3rev/out/probe1.json"
R = {}
def load(p):
    return pypsa.Network(p)
nets = {
 "I365": "/home/jin/v3rev/nets/dmax/integrated_365_24h_unsolved.nc",
 "R365": "/home/jin/v3rev/nets/dmax/no_new_xb_365_24h_unsolved.nc",
 "D365": "/home/jin/v3rev/nets/dmax/disconnected_365_24h_unsolved.nc",
 "I2920": "/home/jin/v3rev/nets/op2920/integrated_2920_3h_unsolved.nc",
 "R2920": "/home/jin/v3rev/nets/op2920/no_new_xb_2920_3h_unsolved.nc",
}
N = {k: load(v) for k, v in nets.items()}
for k, n in N.items():
    z = {}
    w = n.snapshot_weightings
    z["weights"] = {c: [float(w[c].min()), float(w[c].max()), float(w[c].sum())] for c in w.columns}
    z["n_snapshots"] = int(len(n.snapshots)); z["first"] = str(n.snapshots[0]); z["last"] = str(n.snapshots[-1])
    z["meta_keys"] = sorted(n.meta.keys())
    z["hooks"] = n.meta.get("required_constraint_hooks")
    z["scenario"] = n.meta.get("scenario"); z["xb"] = n.meta.get("research_cross_border", {}).get("switches") if isinstance(n.meta.get("research_cross_border"), dict) else None
    z["global_constraints"] = n.global_constraints[["type", "carrier_attribute", "sense", "constant"]].astype(str).to_dict("index") if len(n.global_constraints) else {}
    z["counts"] = {c.name: int(len(c.df)) for c in n.iterate_components()}
    z["objective_constant_like"] = {"xb_fom_eur": n.meta.get("existing_cross_border_fom_eur"), "ev": n.meta.get("research_ev"), "liquids_caps": (n.meta.get("research_liquids") or {}).get("capacity_mw")}
    # stock lines / links
    L = n.lines; K = n.links
    xl = L[L.border_class == "cross_border"] if "border_class" in L else L.iloc[:0]
    z["xb_lines"] = dict(n=int(len(xl)), ext=int(xl.s_nom_extendable.sum()), s_nom_sum=float(xl.s_nom.sum()), s_nom_min_sum=float(xl.s_nom_min.sum()), s_nom_max_sum=float(xl.s_nom_max.sum()),
                        stock_rows=int((xl.s_nom_min > 0).sum()), stock_s_nom_eq_min=int(((xl.s_nom_min > 0) & np.isclose(xl.s_nom, xl.s_nom_min)).sum()), capital_cost_range=[float(xl.capital_cost.min()), float(xl.capital_cost.max())] if len(xl) else None,
                        s_max_pu=sorted(set(xl.s_max_pu.round(4))) if len(xl) else None)
    xk = K[K.border_class == "cross_border"] if "border_class" in K else K.iloc[:0]
    z["xb_links_by_carrier"] = {c: dict(n=int(len(g)), ext=int(g.p_nom_extendable.sum()), p_nom_sum=float(g.p_nom.sum()), p_nom_min_sum=float(g.p_nom_min.sum()), stock_rows=int((g.p_nom_min > 0).sum()), stock_p_nom_eq_min=int(((g.p_nom_min > 0) & np.isclose(g.p_nom, g.p_nom_min)).sum()),
                                        capital_cost_nonzero=int((g.capital_cost > 0).sum()), p_min_pu=sorted(set(g.p_min_pu.round(3))), eff_range=[float(g.efficiency.min()), float(g.efficiency.max())]) for c, g in xk.groupby("carrier")}
    # components with extendable and nonzero nominal (brownfield objective-constant relevance)
    for typ, nom in (("Generator", "p_nom"), ("Link", "p_nom"), ("Line", "s_nom"), ("Store", "e_nom"), ("StorageUnit", "p_nom")):
        d = n.df(typ); e = d[d[nom + "_extendable"].astype(bool) & (d[nom] > 0)]
        z[f"ext_with_nominal_{typ}"] = dict(n=int(len(e)), nominal_sum=float(e[nom].sum()), capex_x_nominal=float((e[nom] * e.capital_cost).sum()), carriers=e.carrier.astype(str).value_counts().head(8).to_dict() if "carrier" in e else None)
    # EV
    st = n.stores[n.stores.carrier == "EV battery"]
    z["ev_stores"] = dict(n=int(len(st)), e_nom_sum_twh=float(st.e_nom.sum() / 1e6), cyclic=int(st.e_cyclic.sum()), e_min_pu_cols=int(st.index.isin(n.stores_t.e_min_pu.columns).sum()))
    if len(st) and len(n.stores_t.e_min_pu.columns):
        em = n.stores_t.e_min_pu[st.index.intersection(n.stores_t.e_min_pu.columns)]
        z["ev_e_min_pu"] = dict(values=sorted(set(np.round(em.to_numpy().ravel(), 4))), per_store_count_08=sorted(set((em >= 0.8 - 1e-9).sum().to_numpy().tolist())))
    ch = n.links[n.links.carrier == "BEV charger"]
    z["bev_charger"] = dict(n=int(len(ch)), ext=int(ch.p_nom_extendable.sum()), p_nom_sum_gw=float(ch.p_nom.sum() / 1e3), eff=sorted(set(ch.efficiency.round(4))), p_max_pu_ts=int(ch.index.isin(n.links_t.p_max_pu.columns).sum()),
                            p_max_pu_mean=float(n.links_t.p_max_pu[ch.index.intersection(n.links_t.p_max_pu.columns)].mean().mean()) if len(ch) else None)
    ev = n.loads[n.loads.carrier == "land transport EV"]
    pset = n.get_switchable_as_dense("Load", "p_set")[ev.index]
    z["ev_load"] = dict(n=int(len(ev)), twh=float(pset.mul(w.generators, axis=0).sum().sum() / 1e6), ts_cols=int(ev.index.isin(n.loads_t.p_set.columns).sum()), min_over_mean=float((pset.min() / pset.mean()).min()), max_over_mean=float((pset.max() / pset.mean()).max()))
    # hydro storage units pumping?
    su = n.storage_units
    z["storage_units"] = {c: dict(n=int(len(g)), p_min_pu=sorted(set(g.p_min_pu.round(3))), eff_store=sorted(set(g.efficiency_store.round(3))), ext=int(g.p_nom_extendable.sum()), max_hours=[float(g.max_hours.min()), float(g.max_hours.max())], cyclic=int(g.cyclic_state_of_charge.sum())) for c, g in su.groupby("carrier")}
    # stores: cyclic flags by carrier
    z["stores_cyclic_by_carrier"] = {c: dict(n=int(len(g)), cyclic=int(g.e_cyclic.sum()), e_min_pu_neg=int((g.e_min_pu < 0).sum())) for c, g in n.stores.groupby("carrier")}
    # loads by sector carrier totals TWh
    pall = n.get_switchable_as_dense("Load", "p_set").mul(w.generators, axis=0).sum() / 1e6
    z["load_twh_by_carrier"] = {str(c): float(v) for c, v in pall.groupby(n.loads.carrier.astype(str)).sum().sort_values(ascending=False).items()}
    z["load_twh_total"] = float(pall.sum())
    z["load_ts_cols_by_carrier"] = n.loads.loc[n.loads.index.isin(n.loads_t.p_set.columns), "carrier"].astype(str).value_counts().to_dict()
    # dedicated
    if "stock" in K:
        dd = K[K.stock.astype(str) == "dedicated_plant_line"]
        z["dedicated"] = dd[["bus0", "bus1", "p_nom", "efficiency", "p_min_pu", "p_nom_extendable", "border_class"]].to_dict("index")
    src = K[K.carrier == "dedicated plant source"]
    z["source_links"] = src[["bus0", "bus1", "p_nom", "efficiency", "p_min_pu", "marginal_cost", "capital_cost"]].to_dict("index")
    # slack
    z["slack_gens"] = n.generators[n.generators.carrier.astype(str).str.contains("slack|shed|lost|overflow", case=False)].carrier.value_counts().to_dict()
    R[k] = z

def diff(a, b, label):
    out = {}
    for c in a.iterate_components():
        typ = c.name; x = a.df(typ); y = b.df(typ)
        gone = x.index.difference(y.index); new = y.index.difference(x.index); both = x.index.intersection(y.index)
        rec = dict(removed=int(len(gone)), added=int(len(new)))
        if len(gone) and "carrier" in x:
            rec["removed_by_carrier"] = x.loc[gone].carrier.astype(str).value_counts().to_dict()
            if "border_class" in x:
                rec["removed_border_class"] = x.loc[gone].border_class.astype(str).value_counts().to_dict()
        if len(new) and "carrier" in y:
            rec["added_by_carrier"] = y.loc[new].carrier.astype(str).value_counts().to_dict()
        ch = {}
        for col in x.columns.intersection(y.columns):
            xc, yc = x.loc[both, col], y.loc[both, col]
            try:
                same = np.isclose(xc.astype(float), yc.astype(float), rtol=1e-12, atol=1e-9, equal_nan=True)
            except (ValueError, TypeError):
                same = (xc.astype(str) == yc.astype(str)).to_numpy()
            idx = both[~same]
            if len(idx):
                bc = y.loc[idx, "border_class"].astype(str).value_counts().to_dict() if "border_class" in y else None
                ch[col] = dict(n=int(len(idx)), examples=list(map(str, idx[:4])), border_class=bc, carriers=y.loc[idx].carrier.astype(str).value_counts().head(6).to_dict() if "carrier" in y else None)
        rec["changed_columns"] = ch
        ts = {}
        for attr, fa in a.pnl(typ).items():
            fb = b.pnl(typ).get(attr)
            if fb is None:
                continue
            ca = set(fa.columns); cb = set(fb.columns)
            cm = sorted(ca & cb)
            d = {}
            if cm:
                dd = (fa[cm].to_numpy() - fb[cm].to_numpy())
                bad = [cm[i] for i in np.where(np.abs(dd).max(axis=0) > 1e-9)[0]]
                if bad:
                    d["changed"] = dict(n=len(bad), examples=bad[:4])
            if ca - cb:
                d["only_in_a"] = dict(n=len(ca - cb), examples=sorted(ca - cb)[:4])
            if cb - ca:
                d["only_in_b"] = dict(n=len(cb - ca), examples=sorted(cb - ca)[:4])
            if d:
                ts[attr] = d
        rec["time_series"] = ts
        out[typ] = rec
    ma, mb = a.meta, b.meta
    out["meta_keys_only_a"] = sorted(set(ma) - set(mb)); out["meta_keys_only_b"] = sorted(set(mb) - set(ma))
    out["meta_differing"] = sorted(k for k in set(ma) & set(mb) if json.dumps(ma[k], sort_keys=True, default=str) != json.dumps(mb[k], sort_keys=True, default=str))
    gx, gy = a.global_constraints, b.global_constraints
    out["global_constraints"] = dict(only_a=sorted(set(gx.index) - set(gy.index)), only_b=sorted(set(gy.index) - set(gx.index)), changed=[i for i in gx.index.intersection(gy.index) if not gx.loc[i].astype(str).equals(gy.loc[i].astype(str))])
    R[label] = out
diff(N["I365"], N["R365"], "diff_I365_R365")
diff(N["I2920"], N["R2920"], "diff_I2920_R2920")
diff(N["I365"], N["D365"], "diff_I365_D365")
json.dump(R, open(OUT, "w"), indent=1, default=str)
print("done", OUT)
