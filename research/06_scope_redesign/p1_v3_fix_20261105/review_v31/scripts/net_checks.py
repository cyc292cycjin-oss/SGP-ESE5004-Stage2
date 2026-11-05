import json, sys, math, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, pypsa
PK = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1/networks/"
NETS = {"F1": "integrated_2920_3h_unsolved.nc", "F2": "no_new_xb_2920_3h_unsolved.nc", "F3": "integrated_ev05_2920_3h_unsolved.nc", "F4": "no_new_xb_ev05_2920_3h_unsolved.nc"}
BUNKER = "co2 bunkers ASEAN"
out = {}


def ports_on(n, bus):
    res = []
    for col in [c for c in n.links.columns if c.startswith("bus")]:
        for name in n.links.index[n.links[col] == bus]:
            res.append(("Link", name, col))
    for name in n.generators.index[n.generators.bus == bus]:
        res.append(("Generator", name, "bus"))
    for name in n.loads.index[n.loads.bus == bus]:
        res.append(("Load", name, "bus"))
    for name in n.stores.index[n.stores.bus == bus]:
        res.append(("Store", name, "bus"))
    for name in n.storage_units.index[n.storage_units.bus == bus]:
        res.append(("StorageUnit", name, "bus"))
    return res


def effcol(col):
    return "efficiency" if col == "bus1" else "efficiency" + col[3:]


def link_eff(n, name, col):
    if col == "bus0":
        return -1.0, None
    e = float(n.links.at[name, effcol(col)]) if effcol(col) in n.links.columns else 1.0
    tv = n.links_t.get(effcol(col))
    tvmin = float(tv[name].min()) if tv is not None and name in tv.columns else None
    return e, tvmin


def cap_info(n, name):
    r = n.links.loc[name]
    return dict(ext=bool(r.p_nom_extendable), p_nom=float(r.p_nom), p_nom_min=float(r.p_nom_min),
                p_nom_max=(None if math.isinf(float(r.p_nom_max)) else float(r.p_nom_max)),
                p_max_pu=float(r.p_max_pu), capital_cost=float(r.capital_cost), marginal_cost=float(r.marginal_cost))


def usable(ci):
    if ci["ext"]:
        return ci["p_nom_max"] is None or ci["p_nom_max"] > 0
    return ci["p_nom"] * ci["p_max_pu"] > 0


for lab, fn in NETS.items():
    n = pypsa.Network(PK + fn)
    R = {}
    w = n.snapshot_weightings
    R["snapshots"] = int(len(n.snapshots))
    R["weights_min"] = {c: float(w[c].min()) for c in w.columns}
    R["weights_sum"] = {c: float(w[c].sum()) for c in w.columns}
    # ---- A. bunker premises
    P = ports_on(n, BUNKER)
    meters = [(nm, col) for t, nm, col in P if t == "Link"]
    others = [(t, nm, col) for t, nm, col in P if t != "Link"]
    effs = [link_eff(n, nm, col) for nm, col in meters]
    L = n.links.loc[[nm for nm, _ in meters]]
    tvp = n.links_t.get("p_min_pu")
    tvcols = [x for x in L.index if tvp is not None and x in tvp.columns]
    tvx = n.links_t.get("p_max_pu")
    tvxcols = [x for x in L.index if tvx is not None and x in tvx.columns]
    st = n.stores.loc[BUNKER]
    R["bunker"] = dict(
        ports=len(meters), distinct_links=int(L.index.nunique()), non_link_attached=[(t, nm) for t, nm, c in others],
        port_cols=sorted(set(c for _, c in meters)), eff_static_min=min(e for e, _ in effs), eff_static_max=max(e for e, _ in effs),
        eff_tv_present=sum(1 for _, t in effs if t is not None), eff_tv_min=min([t for _, t in effs if t is not None], default=None),
        p_min_pu_static_min=float(L.p_min_pu.min()), p_min_pu_static_max=float(L.p_min_pu.max()), p_min_pu_tv_links=len(tvcols),
        p_min_pu_tv_min=(float(tvp[tvcols].min().min()) if tvcols else None),
        p_max_pu_static_min=float(L.p_max_pu.min()), p_max_pu_tv_links=len(tvxcols),
        extendable=int(L.p_nom_extendable.sum()), not_extendable=int((~L.p_nom_extendable).sum()),
        p_nom_min_max=float(L.p_nom_min.max()), p_nom_max_min=float(L.p_nom_max.min()),
        capital_cost_min=float(L.capital_cost.min()), capital_cost_max=float(L.capital_cost.max()),
        marginal_cost_min=float(L.marginal_cost.min()), marginal_cost_max=float(L.marginal_cost.max()),
        carriers=sorted(set(L.carrier)), bus0=sorted(set(L.bus0))[:5],
        store=dict(e_initial=float(st.e_initial), e_cyclic=bool(st.e_cyclic), standing_loss=float(st.standing_loss),
                   e_nom_extendable=bool(st.e_nom_extendable), e_min_pu=float(st.e_min_pu), e_max_pu=float(st.e_max_pu),
                   capital_cost=float(st.capital_cost), marginal_cost=float(st.marginal_cost), e_nom_max=float(st.e_nom_max), e_nom_min=float(st.e_nom_min)),
        store_tv=[k for k in ("e_min_pu", "e_max_pu", "marginal_cost") if k in n.stores_t and BUNKER in n.stores_t[k].columns])
    finals = sorted(set(L.bus1))
    twin_ok = 0
    twin_bad = []
    for fb in finals:
        feeders = [nm for nm in n.links.index[n.links.bus1 == fb] if nm not in L.index]
        ok = [nm for nm in feeders if usable(cap_info(n, nm))]
        if ok:
            twin_ok += 1
        else:
            twin_bad.append((fb, feeders))
    R["bunker"]["final_buses"] = len(finals)
    R["bunker"]["final_buses_with_usable_nonfossil_feeder"] = twin_ok
    R["bunker"]["final_buses_without"] = twin_bad[:5]
    # ---- B. country atmosphere accounts: removal ports and their downstream
    atm = n.buses.index[n.buses.carrier == "co2 atmosphere"]
    C = {}
    for ab in atm:
        c = str(n.buses.at[ab, "country"])
        rem = []
        for t, nm, col in ports_on(n, ab):
            if t != "Link":
                continue
            e, tvmin = link_eff(n, nm, col)
            if e < 0 or (tvmin is not None and tvmin < 0):
                rem.append((nm, col, e, tvmin))
        info = []
        sinks = {}
        for nm, col, e, tvmin in rem:
            ci = cap_info(n, nm)
            r = n.links.loc[nm]
            outs = []
            for oc in [x for x in n.links.columns if x.startswith("bus") and x != "bus0" and x != col]:
                b = r[oc]
                if isinstance(b, str) and b and b in n.buses.index:
                    ee, _ = link_eff(n, nm, oc)
                    if ee > 0:
                        outs.append((b, str(n.buses.at[b, "carrier"]), ee))
            for b, car, ee in outs:
                if "co2" not in car:
                    continue
                if b in sinks:
                    continue
                d = dict(carrier=car, stores=[], links_out=[], transport=[])
                for t2, nm2, col2 in ports_on(n, b):
                    if t2 == "Store":
                        s = n.stores.loc[nm2]
                        d["stores"].append(dict(name=nm2, carrier=str(s.carrier), ext=bool(s.e_nom_extendable), e_nom=float(s.e_nom),
                                                e_nom_max=(None if math.isinf(float(s.e_nom_max)) else float(s.e_nom_max)), e_cyclic=bool(s.e_cyclic), e_min_pu=float(s.e_min_pu)))
                    elif t2 == "Link" and col2 == "bus0":
                        ci2 = cap_info(n, nm2)
                        r2 = n.links.loc[nm2]
                        dest = [(r2[x], str(n.buses.at[r2[x], "country"]) if r2[x] in n.buses.index else "") for x in n.links.columns
                                if x.startswith("bus") and x != "bus0" and isinstance(r2[x], str) and r2[x]]
                        rec_ = dict(name=nm2, carrier=str(r2.carrier), usable=usable(ci2), dest=dest[:3], **ci2)
                        if any(dc != c and dc not in ("", "ASEAN", "nan") for _, dc in dest):
                            d["transport"].append(rec_)
                        else:
                            d["links_out"].append(rec_)
                sinks[b] = d
            info.append(dict(link=nm, port=col, eff=e, carrier=str(r.carrier), usable=usable(ci), outputs=outs[:3], **ci))
        usable_rem = [x for x in info if x["usable"]]
        kinds = {}
        for x in info:
            kinds.setdefault(x["carrier"], [0, 0])
            kinds[x["carrier"]][0] += 1
            kinds[x["carrier"]][1] += int(x["usable"])
        sink_summary = {}
        for b, d in sinks.items():
            seq = [s for s in d["stores"] if "sequester" in s["carrier"] or "sequester" in s["name"]]
            buf = [s for s in d["stores"] if s not in seq]
            uo = [l for l in d["links_out"] if l["usable"]]
            ut = [l for l in d["transport"] if l["usable"]]
            sink_summary[b] = dict(sequestration_stores=[(s["name"], s["ext"], s["e_nom_max"]) for s in seq],
                                   buffer_stores=[(s["name"], s["ext"], s["e_nom_max"], s["e_cyclic"]) for s in buf],
                                   usable_use_links=sorted(set(l["carrier"] for l in uo)),
                                   usable_transport=[(l["name"], l["carrier"], l["dest"]) for l in ut][:6],
                                   n_use=len(uo), n_transport=len(ut), n_transport_total=len(d["transport"]))
        C[c] = dict(atmosphere_bus=ab, removal_ports=len(info), usable_removal_ports=len(usable_rem), removal_kinds=kinds, captured_buses=sink_summary)
    R["countries"] = C
    # ---- C. tiny positive magnitudes that become RHS
    tiny = {}

    def rec(k, s):
        s = pd.Series(np.abs(np.asarray(s, dtype=float)).ravel())
        s = s[s > 0]
        if len(s):
            tiny[k] = dict(min_pos=float(s.min()), n_below_1e_9=int((s < 1e-9).sum()))

    rec("loads.p_set", n.loads.p_set)
    if "p_set" in n.loads_t and len(n.loads_t.p_set.columns):
        rec("loads_t.p_set", n.loads_t.p_set.values)
    g = n.generators[~n.generators.p_nom_extendable]
    rec("fixed gens p_nom*p_max_pu", g.p_nom * g.p_max_pu)
    if "p_max_pu" in n.generators_t and len(n.generators_t.p_max_pu.columns):
        cols = [c for c in n.generators_t.p_max_pu.columns if c in g.index]
        if cols:
            rec("fixed gens p_nom*p_max_pu(t)", n.generators_t.p_max_pu[cols].values * g.loc[cols, "p_nom"].values)
    l = n.links[~n.links.p_nom_extendable]
    rec("fixed links p_nom*p_max_pu", l.p_nom * l.p_max_pu)
    rec("fixed links p_nom*abs(p_min_pu)", l.p_nom * l.p_min_pu.abs())
    if "p_max_pu" in n.links_t and len(n.links_t.p_max_pu.columns):
        cols = [c for c in n.links_t.p_max_pu.columns if c in l.index]
        if cols:
            rec("fixed links p_nom*p_max_pu(t)", n.links_t.p_max_pu[cols].values * l.loc[cols, "p_nom"].values)
    s = n.stores[~n.stores.e_nom_extendable]
    rec("fixed stores e_nom", s.e_nom)
    rec("stores e_initial", n.stores.e_initial)
    if len(n.lines):
        rec("lines s_nom (fixed)", n.lines[~n.lines.s_nom_extendable].s_nom)
    if "inflow" in n.storage_units_t and len(n.storage_units_t.inflow.columns):
        rec("storage_units_t.inflow", n.storage_units_t.inflow.values)
    if "p_set" in n.links_t and len(n.links_t.p_set.columns):
        rec("links_t.p_set", n.links_t.p_set.values)
    if "p_set" in n.generators_t and len(n.generators_t.p_set.columns):
        rec("generators_t.p_set", n.generators_t.p_set.values)
    R["tiny_magnitudes"] = tiny
    if "p_set" in n.loads_t and len(n.loads_t.p_set.columns):
        W = n.loads_t.p_set.iloc[248:472]
        v = np.abs(W.values)
        vpos = v[v > 0]
        small_cols = sorted(set(W.columns[((v > 0) & (v < 1e-12)).any(0)]))
        R["tiny_loads_window_M02"] = dict(min_pos=float(vpos.min()), n_below_1e_12=int((vpos < 1e-12).sum()), cols_below_1e_12=small_cols[:8], n_cols=len(small_cols))
        # whole year
        v2 = np.abs(n.loads_t.p_set.values)
        small_all = sorted(set(n.loads_t.p_set.columns[((v2 > 0) & (v2 < 1e-12)).any(0)]))
        R["tiny_loads_full_year"] = dict(n_cols=len(small_all), cols=small_all[:8], carriers=sorted(set(n.loads.loc[small_all, "carrier"]))[:8] if small_all else [])
    # ---- D. load shedding / slack generators
    gen = n.generators
    shed = gen[gen.carrier.str.contains("load|shed|slack|backup|unmet", case=False, regex=True) | (gen.marginal_cost > 5000)]
    R["load_shedding_like_generators"] = dict(count=int(len(shed)), carriers=sorted(set(shed.carrier))[:10],
                                              marginal_cost_min=(float(shed.marginal_cost.min()) if len(shed) else None))
    out[lab] = R
    print("done", lab, file=sys.stderr)

json.dump(out, open("/home/jin/v31rev/net_checks.json", "w"), indent=1, default=str)
for lab, R in out.items():
    print("=====", lab, "snapshots", R["snapshots"], "weights_min", R["weights_min"], "weights_sum", R["weights_sum"])
    b = R["bunker"]
    print(" bunker:", json.dumps({k: v for k, v in b.items() if k not in ("final_buses_without",)}, default=str)[:2000])
    print("  final_buses_without:", b["final_buses_without"])
    for c, d in sorted(R["countries"].items()):
        print(f" {c}: removal ports {d['removal_ports']} usable {d['usable_removal_ports']} kinds {d['removal_kinds']}")
        for bus, s in d["captured_buses"].items():
            print(f"    -> {bus}: seq={s['sequestration_stores']} buf={s['buffer_stores']} use={s['usable_use_links']} n_transport_usable={s['n_transport']}/{s['n_transport_total']} transport_ex={s['usable_transport'][:3]}")
    print(" tiny:", json.dumps(R["tiny_magnitudes"]))
    print(" tiny loads M02:", R.get("tiny_loads_window_M02"))
    print(" tiny loads year:", R.get("tiny_loads_full_year"))
    print(" shedding:", R["load_shedding_like_generators"])
