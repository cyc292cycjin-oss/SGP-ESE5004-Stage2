"""Stores whose level chain could force one-way port flows to zero (the bunker pattern): non-cyclic store, e_initial <= tol,
e_min_pu >= 0 (level cannot go negative) with only OUTFLOW ports (discharge_only: every port takes from the bus the store feeds) -> every
outflow forced 0 through the chain; or e_initial <= tol with e_max_pu bound 0 ... Reported per network, static read only."""
import json, sys, math, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, pypsa
PK = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1/networks/"
NETS = {"F1": "integrated_2920_3h_unsolved.nc", "F2": "no_new_xb_2920_3h_unsolved.nc", "F3": "integrated_ev05_2920_3h_unsolved.nc", "F4": "no_new_xb_ev05_2920_3h_unsolved.nc"}
TOL = 1e-9
out = {}
for lab, fn in NETS.items():
    n = pypsa.Network(PK + fn)
    rules = n.meta.get("research_store_power_rules") or {}
    # find the rules dict anywhere in meta
    def find_rules(d, path=""):
        hits = {}
        if isinstance(d, dict):
            for k, v in d.items():
                if k == "store_power_rules" and isinstance(v, dict):
                    hits[path + k] = v
                hits.update(find_rules(v, path + k + "."))
        return hits
    fr = find_rules(n.meta)
    S = n.stores.copy()
    S["n_ports"] = 0; S["n_in"] = 0; S["n_out"] = 0; S["n_two"] = 0
    buscols = [c for c in n.links.columns if c.startswith("bus")]
    def effcol(col): return "efficiency" if col == "bus1" else "efficiency" + col[3:]
    for s in S.index:
        b = S.at[s, "bus"]
        nin = nout = ntwo = 0
        for col in buscols:
            for nm in n.links.index[n.links[col] == b]:
                pmin = float(n.links.at[nm, "p_min_pu"])
                tv = n.links_t.get("p_min_pu")
                if tv is not None and nm in tv.columns: pmin = min(pmin, float(tv[nm].min()))
                if col == "bus0":
                    if pmin < 0: ntwo += 1
                    else: nout += 1
                else:
                    e = float(n.links.at[nm, effcol(col)]) if effcol(col) in n.links.columns else 1.0
                    if pmin < 0: ntwo += 1
                    elif e > 0: nin += 1
                    elif e < 0: nout += 1
        for nm in n.generators.index[n.generators.bus == b]:
            if float(n.generators.at[nm, "p_min_pu"]) < 0 or float(n.generators.at[nm, "sign"]) < 0: ntwo += 1
            else: nin += 1
        for nm in n.loads.index[n.loads.bus == b]: nout += 1
        others = [x for x in n.stores.index[n.stores.bus == b] if x != s]
        ntwo += len(others) + int((n.storage_units.bus == b).sum())
        S.loc[s, ["n_ports", "n_in", "n_out", "n_two"]] = [nin + nout + ntwo, nin, nout, ntwo]
    S["only_out"] = (S.n_out > 0) & (S.n_in == 0) & (S.n_two == 0)
    S["only_in"] = (S.n_in > 0) & (S.n_out == 0) & (S.n_two == 0)
    cand = S[(~S.e_cyclic) & (S.e_initial.abs() <= TOL) & (S.e_min_pu >= 0) & S.only_out]
    cand2 = S[(~S.e_cyclic) & (S.e_initial.abs() <= TOL) & S.only_out & (S.e_min_pu < 0)]
    fixed_zero = S[(~S.e_nom_extendable) & (S.e_nom.abs() <= TOL)]
    out[lab] = dict(stores=int(len(S)), rules_paths=list(fr.keys()),
                    forced_zero_outflow_chain=[dict(store=s, carrier=str(S.at[s, "carrier"]), ext=bool(S.at[s, "e_nom_extendable"]), e_nom=float(S.at[s, "e_nom"]), n_out=int(S.at[s, "n_out"]), e_initial=float(S.at[s, "e_initial"])) for s in cand.index],
                    zero_initial_outflow_but_negative_level_allowed=[dict(store=s, carrier=str(S.at[s, "carrier"]), e_min_pu=float(S.at[s, "e_min_pu"])) for s in cand2.index][:10],
                    fixed_e_nom_zero=[dict(store=s, carrier=str(S.at[s, "carrier"]), e_initial=float(S.at[s, "e_initial"]), n_ports=int(S.at[s, "n_ports"])) for s in fixed_zero.index][:20],
                    n_fixed_e_nom_zero=int(len(fixed_zero)),
                    carriers_only_out=sorted(set(S[S.only_out].carrier)), carriers_only_in=sorted(set(S[S.only_in].carrier)),
                    e_initial_zero_noncyclic_count=int(((~S.e_cyclic) & (S.e_initial.abs() <= TOL)).sum()))
    print("done", lab, file=sys.stderr)
json.dump(out, open("/home/jin/v31rev/store_checks.json", "w"), indent=1, default=str)
for lab, R in out.items():
    print("=====", lab, json.dumps(R, default=str)[:3000])
