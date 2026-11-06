"""W08 section 5, data-chain check after the cost criterion missed (post-solve, no solver): convexity bracket of the solved cost difference.

For an LP min c'x s.t. A x = b (loads, pool sizes, annual caps on the right-hand side) the optimal value V(b) is convex in b, so with duals y as
subgradients:   y_v31' (b_v4 - b_v31)  <=  V(b_v4) - V(b_v31)  <=  y_v4' (b_v4 - b_v31).
Lower bound: the v3.1 smoke duals (raw duals, the registered 'raw-dual' column of the first-order table); upper bound: the duals of the v4 smoke
solve of the same scenario. Same terms as w08_first_order.py (loads, pool initial energy, annual gas caps), raw duals only (no substitute valuation).
Post-solve completion: loads on buses absent from a solve are priced at the mean price of the buses of the same country and carrier
(else same carrier); a pool present on one side only (oil_palm_fibre removed in v4) at the mean bus price minus the store marginal cost;
fixed capacities (non-extendable store e_nom and link p_nom, e.g. EV batteries / chargers) at the summed |dual| of their upper bounds.
Components still without a price are listed (missing).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w08_bounds.py
Writes tables/W08_SMOKE56_BRACKET.csv and evidence/W08_bracket.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from w08_first_order import MAIN, N, PKG, SM, pset   # noqa: E402

W = Path(__file__).resolve().parents[1]
RUN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/smoke56")
PAIRS = {"v4_F1": (PKG / "integrated_2920_3h_unsolved.nc", MAIN / "main/integrated/integrated_2920_3h_unsolved.nc", SM / "F1", RUN / "v4_F1", "integrated"),
         "v4_F2": (PKG / "no_new_xb_2920_3h_unsolved.nc", MAIN / "main/no_new_xb/no_new_xb_2920_3h_unsolved.nc", SM / "F2", RUN / "v4_F2", "no_new_xb"),
         "v4iid_F1": (PKG / "integrated_2920_3h_unsolved.nc", MAIN / "iid/integrated/integrated_2920_3h_unsolved.nc", SM / "F1", RUN / "v4iid_F1", "integrated")}


def sum_abs(D, var: str) -> dict:
    """{component: sum over snapshots of |dual|} of a per-snapshot bound constraint (value of one more unit of the fixed capacity)."""
    if var not in D.data_vars:
        return {}
    x = D[var]; tdim = [d for d in x.dims if d.endswith("snapshot")][0]; cdim = [d for d in x.dims if not d.endswith("snapshot")][0]
    return {str(c): float(v) for c, v in zip(x[cdim].values, np.abs(x).sum(tdim).transpose(cdim).values)}


def priced(A, Bn, sdir, sc) -> dict:
    S = pypsa.Network(str(sdir / f"{sc}_SMOKE_TEST_ONLY_solved.nc"))
    sn = S.snapshots[:N]; w = S.snapshot_weightings.objective.loc[sn].to_numpy(); lam = S.buses_t.marginal_price.loc[sn]
    PA, PB = pset(A, A.snapshots[:N]), pset(Bn, Bn.snapshots[:N]); PA.index = sn; PB.index = sn
    out = dict(load=0.0, pool=0.0, gas_cap=0.0, removed_pool=0.0, capacity=0.0); miss = []; by = {}; bycar = {}; proxied = 0.0

    def bus_price(bus, c, bc):
        if bus in lam.columns:
            return lam[bus].to_numpy(), False
        peers = [x for x in S.buses.index[(S.buses.country == c) & (S.buses.carrier == bc)] if x in lam.columns] or \
                [x for x in S.buses.index[S.buses.carrier == bc] if x in lam.columns]
        return (lam[peers].mean(axis=1).to_numpy(), True) if peers else (None, False)

    for l in sorted(set(PA.columns) | set(PB.columns)):
        d = (PB[l].to_numpy() if l in PB.columns else np.zeros(N)) - (PA[l].to_numpy() if l in PA.columns else np.zeros(N))
        if not np.any(d):
            continue
        net = Bn if l in Bn.loads.index else A
        bus = net.loads.at[l, "bus"]; c = net.buses.at[bus, "country"]; bc = net.buses.at[bus, "carrier"]
        p, prox = bus_price(bus, c, bc)
        if p is None:
            miss.append(dict(component=l, annual_mwh=float((d * w).sum()))); continue
        v = float((d * p * w).sum()); out["load"] += v; by[c] = by.get(c, 0.0) + v
        e = bycar.setdefault(bc, [0.0, 0.0]); e[0] += float((d * w).sum()); e[1] += v
        proxied += float(abs((d * w).sum())) if prox else 0.0
    D = xr.open_dataset(sdir / "DUALS_BY_CONSTRAINT.nc"); eb = D["Store-energy_balance"]
    tdim = [x for x in eb.dims if x.endswith("snapshot")][0]; sdim = [x for x in eb.dims if not x.endswith("snapshot")][0]
    e0 = {str(s): float(abs(v)) for s, v in zip(eb[sdim].values, eb.isel({tdim: 0}).transpose(sdim).values)}
    eup = sum_abs(D, "Store-fix-e-upper"); pup = sum_abs(D, "Link-fix-p-upper")
    for s in sorted(set(A.stores.index) | set(Bn.stores.index)):
        ea = float(A.stores.at[s, "e_initial"]) if s in A.stores.index else 0.0; e4 = float(Bn.stores.at[s, "e_initial"]) if s in Bn.stores.index else 0.0
        if ea != e4:
            if s in e0:
                out["pool"] += -(e4 - ea) * e0[s]
            else:   # resource pool present on one side only (oil_palm_fibre removed in v4): value = bus price - store marginal cost (>= 0)
                net = A if s in A.stores.index else Bn
                p, _ = bus_price(net.stores.at[s, "bus"], net.stores.at[s, "country"], net.buses.at[net.stores.at[s, "bus"], "carrier"])
                if p is None:
                    miss.append(dict(component=s, annual_mwh=e4 - ea))
                else:
                    out["removed_pool"] += -(e4 - ea) * max(0.0, float((p * w).sum() / w.sum()) - float(net.stores.at[s, "marginal_cost"]))
        if s in A.stores.index and s in Bn.stores.index and not bool(Bn.stores.at[s, "e_nom_extendable"]):
            dn = float(Bn.stores.at[s, "e_nom"]) - float(A.stores.at[s, "e_nom"])
            if dn and abs(float(Bn.stores.at[s, "e_initial"]) - float(Bn.stores.at[s, "e_nom"])) > 0:   # pools: e_nom = e_initial (counted above)
                out["capacity"] += -dn * eup.get(s, 0.0)
    for k in sorted(set(A.links.index) & set(Bn.links.index)):
        if bool(Bn.links.at[k, "p_nom_extendable"]):
            continue
        dn = float(Bn.links.at[k, "p_nom"]) - float(A.links.at[k, "p_nom"])
        if dn:
            out["capacity"] += -dn * pup.get(k, 0.0)
    ca, cb = A.meta.get("external_annual_caps", {}), Bn.meta.get("external_annual_caps", {})
    for g in sorted(set(ca) | set(cb)):
        if g.endswith("gas production") and float(ca.get(g, 0.0)) != float(cb.get(g, 0.0)):
            k = f"ResearchImportAnnual-{g}"
            out["gas_cap"] += -(float(cb.get(g, 0.0)) - float(ca.get(g, 0.0))) * (float(abs(D[k].values)) if k in D.data_vars else 0.0)
    return dict(total=sum(out.values()), terms=out, by_country_load=by, by_carrier_load={k: dict(delta_annual_mwh=v[0], cost_eur=v[1]) for k, v in bycar.items()}, missing=len(miss), missing_annual_mwh=float(sum(m["annual_mwh"] for m in miss)),
                missing_list=miss[:40], proxied_load_annual_mwh=proxied)


def main():
    sm = json.loads((W / "evidence/W08_smoke56.json").read_text())["criteria"]
    rows, ev = [], {}
    for pid, (pa, pb, s31, s4, sc) in PAIRS.items():
        A = pypsa.Network(str(pa)); Bn = pypsa.Network(str(pb))
        lo = priced(A, Bn, s31, sc); hi = priced(A, Bn, s4, sc)
        act = sm[pid]["delta_vs_v31_eur"]
        r = dict(pair=pid, lower_bound_v31_duals_eur=lo["total"], solved_delta_eur=act, upper_bound_v4_duals_eur=hi["total"],
                 inside=bool(lo["total"] <= act <= hi["total"]), lower_terms=lo["terms"], upper_terms=hi["terms"], upper_load_by_carrier=hi["by_carrier_load"],
                 upper_load_by_country=hi["by_country_load"], upper_proxied_load_annual_mwh=hi["proxied_load_annual_mwh"],
                 unpriced_lower_mwh=lo["missing_annual_mwh"], unpriced_upper_mwh=hi["missing_annual_mwh"])
        rows.append({k: v for k, v in r.items() if not isinstance(v, dict)}); ev[pid] = r
        print(pid, round(lo["total"] / 1e9, 3), "<=", round(act / 1e9, 3), "<=", round(hi["total"] / 1e9, 3), r["inside"], {k: round(v / 1e9, 2) for k, v in hi["terms"].items()}, flush=True)
    pd.DataFrame(rows).to_csv(W / "tables/W08_SMOKE56_BRACKET.csv", index=False, float_format="%.6g", lineterminator="\n")
    (W / "evidence/W08_bracket.json").write_text(json.dumps(dict(status="EXACT bracket rule (LP convexity) with VERIFIED duals; INFERENCE where components are unpriced", method=__doc__, pairs=ev),
                                                       indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
