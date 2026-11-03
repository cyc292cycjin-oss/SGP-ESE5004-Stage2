"""Independent review probe 5: (i) EV weekday alignment in local time; (ii) storage / firm capacity in the solved V1 (daily-resolution artefact check); (iii) electricity balance."""
import json, logging
import numpy as np, pandas as pd, pypsa
logging.disable(logging.WARNING)
WT = "/home/jin/wt_v3_review"; OUT = "/home/jin/v3rev/out/probe5.json"; R = {}
sh = pd.read_csv(f"{WT}/research_inputs/transport_v3/EV_WEEKLY_LOCAL_SHAPE_V3.csv")
R["shape_weekday_mean"] = {int(k): round(float(v), 4) for k, v in sh.groupby("weekday").consumption_norm.mean().items()}
R["shape_hour_mean_peak_hour"] = int(sh.groupby("hour").consumption_norm.mean().idxmax())
R["evidence_json"] = json.load(open(f"{WT}/research_inputs/transport_v3/EV_V3_EVIDENCE.json"))
n = pypsa.Network("/home/jin/v3rev/nets/op2920/integrated_2920_3h_unsolved.nc")
tz = pd.read_csv(f"{WT}/research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv").set_index("node").utc_offset_h
ev = n.loads[n.loads.carrier == "land transport EV"]
out = {}
for off in (6.5, 7.0, 8.0, 9.0):
    nodes = [str(b)[: -len(" EV battery")] for b in ev.bus if abs(float(tz[str(b)[: -len(" EV battery")]]) - off) < 1e-9]
    if not nodes:
        continue
    lds = ev.index[ev.bus.isin([f"{x} EV battery" for x in nodes])]
    s = n.loads_t.p_set[lds].sum(axis=1)
    loc = n.snapshots + pd.Timedelta(hours=off)   # local clock at the START of the 3 h snapshot
    wd = s.groupby(loc.dayofweek).mean(); wd = wd / wd.mean()
    out[str(off)] = {int(k): round(float(v), 4) for k, v in wd.items()}
R["network_ev_weekday_rel_local_start"] = out
# with the snapshot centre (start + 1.5 h)
s = n.loads_t.p_set[ev.index].sum(axis=1); off7 = n.snapshots + pd.Timedelta(hours=8.5)
wd = s.groupby(off7.dayofweek).mean(); R["network_ev_weekday_rel_all_nodes_center_plus7"] = {int(k): round(float(v / wd.mean()), 4) for k, v in wd.items()}
# toy: reproduce ev_series for a Monday-only week to see which UTC day gets the mass
import sys; sys.path.insert(0, f"{WT}/scripts_project")
from v3_ev import ev_series
week = np.zeros(168); week[0:24] = 7.0   # Monday local only
sn = n.snapshots
for off in (7.0,):
    x = ev_series(sn, off, week); g = pd.Series(x, index=sn).groupby(sn.dayofweek).sum()
    R[f"toy_monday_mass_by_utc_dayofweek_off{off}"] = {int(k): round(float(v), 2) for k, v in g.items()}
    gl = pd.Series(x, index=sn).groupby((sn + pd.Timedelta(hours=off)).dayofweek).sum()
    R[f"toy_monday_mass_by_local_dayofweek_off{off}"] = {int(k): round(float(v), 2) for k, v in gl.items()}
R["first_snapshot"] = str(sn[0]); R["first_snapshot_dayofweek"] = int(sn[0].dayofweek)
# solved V1 storage / firm capacity
for run, p in (("V1", "/home/jin/v3rev/cloud/solved/integrated_DFX_365X24H_solved.nc"), ("V2", "/home/jin/v3rev/cloud/solved/no_new_xb_DFX_365X24H_solved.nc")):
    m = pypsa.Network(p); z = {}
    S = m.stores; z["store_e_nom_opt_gwh"] = {c: round(float(v / 1e3), 3) for c, v in S.e_nom_opt.groupby(S.carrier.astype(str)).sum().items() if c in ("battery", "home battery", "H2 Store Tank", "EV battery", "methanol store", "ammonia store", "oil non-fossil store")}
    L = m.links; lc = L.carrier.astype(str)
    z["link_gw_opt"] = {c: round(float(L.p_nom_opt[lc == c].sum() / 1e3), 3) for c in ("battery charger", "battery discharger", "home battery charger", "H2 turbine", "H2 Fuel Cell", "OCGT", "CCGT", "CCGT CC", "OCGT existing", "CCGT existing", "H2 Electrolysis", "DAC")}
    G = m.generators; gc = G.carrier.astype(str)
    z["gen_gw_opt"] = {c: round(float(G.p_nom_opt[gc == c].sum() / 1e3), 2) for c in ("solar", "solar rooftop", "onwind", "offwind-ac", "offwind-dc", "offwind-float", "nuclear", "nuclear SMR", "geothermal")}
    SU = m.storage_units; z["storage_unit_gw_opt"] = {c: round(float(SU.p_nom_opt[SU.carrier == c].sum() / 1e3), 2) for c in sorted(set(SU.carrier))}
    w = m.snapshot_weightings.generators
    # electricity balance at AC buses: generation into AC buses
    ac = set(m.buses.index[m.buses.carrier == "AC"])
    gen_ac = m.generators_t.p[G.index[G.bus.isin(ac)]].mul(w, axis=0).sum() / 1e6
    z["elec_generation_twh_by_carrier"] = {c: round(float(v), 1) for c, v in gen_ac.groupby(gc.reindex(gen_ac.index)).sum().items() if abs(v) > 0.5}
    su_ac = m.storage_units_t.p[SU.index[SU.bus.isin(ac)]].mul(w, axis=0).sum() / 1e6
    z["elec_storage_units_net_twh"] = {c: round(float(v), 1) for c, v in su_ac.groupby(SU.carrier.reindex(su_ac.index)).sum().items()}
    # links delivering to AC (bus1 in ac): -p1
    l1 = L.index[L.bus1.isin(ac)]; d1 = (-m.links_t.p1[l1]).mul(w, axis=0).sum() / 1e6
    z["elec_links_into_ac_twh_by_carrier"] = {c: round(float(v), 1) for c, v in d1.groupby(lc.reindex(l1)).sum().items() if abs(v) > 0.5}
    l0 = L.index[L.bus0.isin(ac)]; d0 = m.links_t.p0[l0].mul(w, axis=0).sum() / 1e6
    z["elec_links_out_of_ac_twh_by_carrier"] = {c: round(float(v), 1) for c, v in d0.groupby(lc.reindex(l0)).sum().items() if abs(v) > 0.5}
    ld = m.loads[m.loads.bus.isin(ac)]; pl = m.get_switchable_as_dense("Load", "p_set")[ld.index].mul(w, axis=0).sum() / 1e6
    z["elec_loads_on_ac_twh_by_carrier"] = {c: round(float(v), 1) for c, v in pl.groupby(ld.carrier.astype(str)).sum().items()}
    z["elec_total_generation_twh"] = float(gen_ac.sum() + su_ac.sum() + d1.sum())
    R[run] = z
json.dump(R, open(OUT, "w"), indent=1, default=str); print("done")
