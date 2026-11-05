"""Second pass (static read only).
(a) every Store: classify every port on its bus with direction AND usable capacity (a port of a link fixed at zero capacity is not a port);
    flag  (i) cyclic stores whose usable ports are all one-way  -> zero-slack chain over the whole horizon (bunker pattern, built-in rows);
         (ii) non-cyclic stores with e_initial <= tol, e_min_pu >= 0 and only usable OUTFLOW ports -> forced zero chain;
         (iii) non-cyclic stores with e_initial <= tol, e_max_pu <= 0 ... (not expected).
(b) the captured-CO2 buses named in pass 1 as 'no outlet' (MM): list every port with efficiency and capacity.
(c) the 28 tiny static loads.
"""
import json, sys, math, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, pypsa
PK = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1/networks/"
NETS = {"F1": "integrated_2920_3h_unsolved.nc", "F2": "no_new_xb_2920_3h_unsolved.nc", "F3": "integrated_ev05_2920_3h_unsolved.nc", "F4": "no_new_xb_ev05_2920_3h_unsolved.nc"}
TOL = 1e-9
out = {}


def effcol(col):
    return "efficiency" if col == "bus1" else "efficiency" + col[3:]


def link_usable(n, nm):
    r = n.links.loc[nm]
    if bool(r.p_nom_extendable):
        return math.isinf(float(r.p_nom_max)) or float(r.p_nom_max) > 0
    pmax = float(r.p_max_pu)
    tv = n.links_t.get("p_max_pu")
    if tv is not None and nm in tv.columns:
        pmax = max(pmax, float(tv[nm].max()))
    pmin = float(r.p_min_pu)
    tv2 = n.links_t.get("p_min_pu")
    if tv2 is not None and nm in tv2.columns:
        pmin = min(pmin, float(tv2[nm].min()))
    return float(r.p_nom) * max(abs(pmax), abs(pmin)) > 0


def gen_usable(n, nm):
    r = n.generators.loc[nm]
    if bool(r.p_nom_extendable):
        return math.isinf(float(r.p_nom_max)) or float(r.p_nom_max) > 0
    pmax = float(r.p_max_pu)
    tv = n.generators_t.get("p_max_pu")
    if tv is not None and nm in tv.columns:
        pmax = max(pmax, float(tv[nm].max()))
    return float(r.p_nom) * pmax > 0


def bus_ports(n, bus, exclude_store):
    """list of dict(comp, name, port, direction in {in, out, two}, usable)"""
    res = []
    buscols = [c for c in n.links.columns if c.startswith("bus")]
    tvmin = n.links_t.get("p_min_pu")
    for col in buscols:
        for nm in n.links.index[n.links[col] == bus]:
            pmin = float(n.links.at[nm, "p_min_pu"])
            if tvmin is not None and nm in tvmin.columns:
                pmin = min(pmin, float(tvmin[nm].min()))
            if col == "bus0":
                d = "two" if pmin < 0 else "out"
                e = -1.0
            else:
                e = float(n.links.at[nm, effcol(col)]) if effcol(col) in n.links.columns else 1.0
                tve = n.links_t.get(effcol(col))
                lo = hi = e
                if tve is not None and nm in tve.columns:
                    lo, hi = float(tve[nm].min()), float(tve[nm].max())
                if lo < 0 < hi or pmin < 0:
                    d = "two"
                elif hi > 0:
                    d = "in"
                elif lo < 0:
                    d = "out"
                else:
                    d = "zero"
            res.append(dict(comp="Link", name=nm, port=col, direction=d, eff=e, usable=link_usable(n, nm), carrier=str(n.links.at[nm, "carrier"])))
    for nm in n.generators.index[n.generators.bus == bus]:
        sign = float(n.generators.at[nm, "sign"]); pmin = float(n.generators.at[nm, "p_min_pu"])
        d = "two" if pmin < 0 else ("in" if sign > 0 else "out")
        res.append(dict(comp="Generator", name=nm, port="bus", direction=d, eff=sign, usable=gen_usable(n, nm), carrier=str(n.generators.at[nm, "carrier"])))
    for nm in n.loads.index[n.loads.bus == bus]:
        ps = float(n.loads.at[nm, "p_set"]); tv = n.loads_t.get("p_set")
        mx = ps
        if tv is not None and nm in tv.columns:
            mx = float(tv[nm].abs().max())
        res.append(dict(comp="Load", name=nm, port="bus", direction="out", eff=-1.0, usable=abs(mx) > 0, carrier=str(n.loads.at[nm, "carrier"])))
    for nm in n.stores.index[(n.stores.bus == bus) & (n.stores.index != exclude_store)]:
        res.append(dict(comp="Store", name=nm, port="bus", direction="two", eff=1.0, usable=True, carrier=str(n.stores.at[nm, "carrier"])))
    for nm in n.storage_units.index[n.storage_units.bus == bus]:
        res.append(dict(comp="StorageUnit", name=nm, port="bus", direction="two", eff=1.0, usable=True, carrier=str(n.storage_units.at[nm, "carrier"])))
    return res


for lab, fn in NETS.items():
    n = pypsa.Network(PK + fn)
    R = {}
    S = n.stores
    flags_cyclic, flags_zero_init, summary = [], [], {}
    port_cache = {}
    for s in S.index:
        b = S.at[s, "bus"]
        P = [p for p in bus_ports(n, b, s) if p["usable"] and p["direction"] != "zero"]
        port_cache[s] = P
        dirs = set(p["direction"] for p in P)
        one_way = len(P) > 0 and (dirs == {"in"} or dirs == {"out"})
        rec = dict(store=s, carrier=str(S.at[s, "carrier"]), bus=b, n_usable_ports=len(P), dirs=sorted(dirs), ext=bool(S.at[s, "e_nom_extendable"]), e_nom=float(S.at[s, "e_nom"]),
                   e_nom_max=float(S.at[s, "e_nom_max"]), e_initial=float(S.at[s, "e_initial"]), e_cyclic=bool(S.at[s, "e_cyclic"]), e_min_pu=float(S.at[s, "e_min_pu"]), e_max_pu=float(S.at[s, "e_max_pu"]),
                   capital_cost=float(S.at[s, "capital_cost"]), marginal_cost=float(S.at[s, "marginal_cost"]),
                   example_ports=[(p["comp"], p["name"], p["port"], p["direction"]) for p in P[:4]])
        if bool(S.at[s, "e_cyclic"]) and one_way:
            flags_cyclic.append(rec)
        if (not bool(S.at[s, "e_cyclic"])) and abs(float(S.at[s, "e_initial"])) <= TOL and float(S.at[s, "e_min_pu"]) >= 0 and dirs == {"out"}:
            flags_zero_init.append(rec)
        if len(P) == 0:
            summary.setdefault("stores_without_usable_port", []).append((s, str(S.at[s, "carrier"])))
    R["cyclic_one_way_stores"] = flags_cyclic
    R["noncyclic_zero_initial_outflow_only"] = flags_zero_init
    R["stores_without_usable_port"] = summary.get("stores_without_usable_port", [])[:20]
    R["n_stores"] = int(len(S)); R["n_cyclic"] = int(S.e_cyclic.sum())
    # captured co2 buses flagged in pass 1 (MM) + every 'co2 stored' bus: usable consuming ports
    cs = n.buses.index[n.buses.carrier == "co2 stored"]
    dead = []
    for b in cs:
        P = bus_ports(n, b, "")
        cons = [p for p in P if p["usable"] and p["direction"] in ("out", "two") and p["comp"] == "Link"]
        ins = [p for p in P if p["usable"] and p["direction"] == "in"]
        stores_here = [p for p in P if p["comp"] == "Store"]
        if not cons:
            dead.append(dict(bus=b, country=str(n.buses.at[b, "country"]), n_inflow_ports=len(ins), inflow_carriers=sorted(set(p["carrier"] for p in ins))[:6],
                             stores=[(p["name"], bool(n.stores.at[p["name"], "e_cyclic"]), float(n.stores.at[p["name"], "e_min_pu"]), bool(n.stores.at[p["name"], "e_nom_extendable"])) for p in stores_here],
                             all_ports=[(p["comp"], p["name"], p["port"], p["direction"], p["usable"], round(p["eff"], 4)) for p in P][:12]))
    R["co2_stored_buses"] = int(len(cs)); R["co2_stored_buses_without_consumer"] = dead
    # tiny static loads
    tl = n.loads[(n.loads.p_set.abs() > 0) & (n.loads.p_set.abs() < 1e-9)]
    tvcols = set(n.loads_t.p_set.columns) if "p_set" in n.loads_t else set()
    R["tiny_static_loads"] = dict(count=int(len(tl)), with_time_series=int(sum(1 for x in tl.index if x in tvcols)),
                                  carriers=sorted(set(tl.carrier)), buses_carriers=sorted(set(n.buses.loc[tl.bus, "carrier"])),
                                  examples=[(x, float(tl.at[x, "p_set"]), str(tl.at[x, "carrier"])) for x in tl.index[:8]],
                                  min=float(tl.p_set.abs().min()), max=float(tl.p_set.abs().max()))
    out[lab] = R
    print("done", lab, file=sys.stderr)

json.dump(out, open("/home/jin/v31rev/store_checks2.json", "w"), indent=1, default=str)
for lab, R in out.items():
    print("=====", lab, "stores", R["n_stores"], "cyclic", R["n_cyclic"])
    print(" cyclic one-way stores:", len(R["cyclic_one_way_stores"]))
    for r in R["cyclic_one_way_stores"][:40]:
        print("   ", json.dumps(r, default=str)[:400])
    print(" noncyclic zero-initial outflow-only:", len(R["noncyclic_zero_initial_outflow_only"]))
    for r in R["noncyclic_zero_initial_outflow_only"][:20]:
        print("   ", json.dumps(r, default=str)[:400])
    print(" stores without usable port:", R["stores_without_usable_port"])
    print(" co2 stored buses:", R["co2_stored_buses"], "without consumer:", len(R["co2_stored_buses_without_consumer"]))
    for r in R["co2_stored_buses_without_consumer"]:
        print("   ", json.dumps(r, default=str)[:900])
    print(" tiny static loads:", json.dumps(R["tiny_static_loads"], default=str)[:900])
