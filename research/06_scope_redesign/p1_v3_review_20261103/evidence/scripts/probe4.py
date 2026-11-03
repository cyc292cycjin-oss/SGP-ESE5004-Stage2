"""Independent review probe 4: (i) demand table vs network by country x carrier (same method as v3_static.demand_check, on the dmax integrated 365 network and the 2920 network);
(ii) EV morning floor placement per time zone in the 2920 network; (iii) EV load shape peak local hour; (iv) split components add up (V3_RULES 2.5) using the op builds_bound network if available."""
import json, logging, glob
import numpy as np, pandas as pd, pypsa
logging.disable(logging.WARNING)
WT = "/home/jin/wt_v3_review"; OUT = "/home/jin/v3rev/out/probe4.json"; R = {}
def demand_check(n):
    w = n.snapshot_weightings.generators; p = n.get_switchable_as_dense("Load", "p_set").mul(w, axis=0).sum() / 1e6
    tag = n.loads.country.astype(str); country = tag.where(tag != "ASEAN", n.loads.bus.astype(str).str[:2])
    return n.loads.assign(twh=p.reindex(n.loads.index).fillna(0.0), country=country).groupby(["country", "carrier"]).twh.sum()
t = pd.read_csv(f"{WT}/research/06_scope_redesign/p1_v3_20261102/DEMAND_BY_COUNTRY_SECTOR_CARRIER_v3.csv"); ti = t.groupby(["country", "carrier"]).twh.sum()
for lab, p in (("I365_dmax", "/home/jin/v3rev/nets/dmax/integrated_365_24h_unsolved.nc"), ("R365_dmax", "/home/jin/v3rev/nets/dmax/no_new_xb_365_24h_unsolved.nc"), ("D365_dmax", "/home/jin/v3rev/nets/dmax/disconnected_365_24h_unsolved.nc"), ("I2920_op", "/home/jin/v3rev/nets/op2920/integrated_2920_3h_unsolved.nc")):
    n = pypsa.Network(p); d = demand_check(n)
    cmp = pd.DataFrame(dict(table=ti, network=d)).fillna(0.0); cmp["diff"] = cmp.network - cmp.table
    heat = cmp.index.get_level_values(1).str.startswith("industry heat"); bio = cmp.index.get_level_values(1) == "biomass final energy"
    rel = cmp[~heat & ~bio]
    R[lab] = dict(max_abs_diff_non_overflow_twh=float(rel["diff"].abs().max()), worst={"|".join(k): float(v) for k, v in rel["diff"].abs().sort_values(ascending=False).head(5).items()},
                  table_total=float(cmp.table.sum()), network_total=float(cmp.network.sum()), carriers_only_in_table=sorted(set(cmp.index[(cmp.network == 0) & (cmp.table > 0)].get_level_values(1))), carriers_only_in_network=sorted(set(cmp.index[(cmp.table == 0) & (cmp.network > 0)].get_level_values(1))),
                  biomass_overflow_by_country={k: float(v) for k, v in (cmp[bio].table - cmp[bio].network).groupby(level=0).sum().items() if abs(v) > 1e-6},
                  heat_gain_by_country={k: float(v) for k, v in (cmp[heat].network - cmp[heat].table).groupby(level=0).sum().items() if abs(v) > 1e-6})
    if lab == "I2920_op":
        tz = pd.read_csv(f"{WT}/research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv").set_index("node").utc_offset_h
        em = n.stores_t.e_min_pu; st = n.stores[n.stores.carrier == "EV battery"]
        byoff = {}
        for s in st.index:
            node = s[: -len(" EV battery store")]; off = float(tz[node]); col = em[s]
            hrs = sorted(set(n.snapshots[col.to_numpy() > 0.5].hour)); per_day = col.to_numpy().reshape(365, 8).sum(axis=1)
            local = sorted({(h + off) % 24 for h in hrs})
            byoff.setdefault(str(off), {}).setdefault("utc_hours", set()).update(hrs); byoff[str(off)].setdefault("local_hours_start", set()).update(local); byoff[str(off)]["nodes"] = byoff[str(off)].get("nodes", 0) + 1; byoff[str(off)]["per_day_min_max"] = [float(per_day.min()), float(per_day.max())]
        R["ev_floor_by_offset"] = {k: dict(nodes=v["nodes"], utc_snapshot_hours=sorted(v["utc_hours"]), local_window_start=sorted(v["local_hours_start"]), floors_per_day=v["per_day_min_max"]) for k, v in byoff.items()}
        # EV load peak local hour
        ev = n.loads[n.loads.carrier == "land transport EV"]; ps = n.loads_t.p_set[ev.index]
        peaks = {}
        for ld in ev.index:
            node = str(ev.at[ld, "bus"])[: -len(" EV battery")]; off = float(tz[node]); shape = ps[ld].groupby(n.snapshots.hour).mean(); utc = int(shape.idxmax())
            peaks.setdefault(str(off), set()).add((utc + off) % 24)
        R["ev_load_peak_local_hour_start_by_offset"] = {k: sorted(v) for k, v in peaks.items()}
        ch = n.links[n.links.carrier == "BEV charger"]; pm = n.links_t.p_max_pu[ch.index]
        R["charger_avail"] = dict(mean=float(pm.mean().mean()), min=float(pm.min().min()), max=float(pm.max().max()))
        # weekday pattern of EV load
        wk = ps.sum(axis=1).groupby(n.snapshots.dayofweek).mean(); R["ev_load_weekday_rel"] = {int(k): round(float(v / wk.mean()), 4) for k, v in wk.items()}
# split components vs builds_bound (pre-180) if present
bb = glob.glob("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_bound/integrated/integrated_365_24h_unsolved.nc")
if bb:
    a = pypsa.Network(bb[0]); b = pypsa.Network("/home/jin/v3rev/nets/dmax/integrated_365_24h_unsolved.nc"); rows = {}
    for typ in ("Generator", "StorageUnit"):
        da, db = a.df(typ), b.df(typ)
        parts = [k for k in db.index if k.endswith(" operating")]
        for k in parts:
            base = k[: -len(" operating")]
            rec = dict(p_nom_before=float(da.at[base, "p_nom"]), p_nom_after_sum=float(db.at[base, "p_nom"] + db.at[k, "p_nom"]))
            if "existing_annual_fixed_om_eur" in da:
                rec["fom_before"] = float(da.at[base, "existing_annual_fixed_om_eur"]); rec["fom_after_sum"] = float(db.at[base, "existing_annual_fixed_om_eur"] + db.at[k, "existing_annual_fixed_om_eur"])
            if typ == "StorageUnit" and base in a.storage_units_t.inflow:
                rec["inflow_before_twh"] = float(a.storage_units_t.inflow[base].mul(a.snapshot_weightings.generators).sum() / 1e6); rec["inflow_after_sum_twh"] = float((b.storage_units_t.inflow[base] + b.storage_units_t.inflow[k]).mul(b.snapshot_weightings.generators).sum() / 1e6)
                rec["max_hours_before_after"] = [float(da.at[base, "max_hours"]), float(db.at[base, "max_hours"]), float(db.at[k, "max_hours"])]
            rows[k] = rec
    R["split_components_vs_builds_bound"] = rows
json.dump(R, open(OUT, "w"), indent=1, default=str); print("done")
