"""W08 section 5 / validation plan section 2: first-order estimate of the system-cost difference v4 - v3.1 of the 56-snapshot smoke, written and
committed BEFORE any W08 solve (INFERENCE; the criterion of the instruction: the solved difference within the estimate +- 50 %).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w08_first_order.py

Fixed point: the v3.1 local regression smoke (V3.1 FIX, d3b9a3bc code; /home/jin/v3fix/drill_pkg_13ebce95/runs/smoke56_v31/F1, F2: solved networks and
DUALS_BY_CONSTRAINT.nc). First 56 snapshots, representative weights 8760 / 56 (s2_solve.set_representative_weights; annual quantities unscaled).
  loads   sum over every load of the union (v3.1 network, v4 network): sum_t (p_v4(t) - p_v31(t)) x marginal price of its bus (v3.1 smoke) x weight;
  pools   every Store whose e_initial changes (solid-biomass potentials): - delta e_initial x |dual of its first-snapshot energy balance| (value of one
          more MWh in the pool);
  caps    every domestic gas production generator: - delta annual cap x |dual of ResearchImportAnnual-<generator>| (binding caps only carry a dual).
Not included (second order or structural, listed): EV battery / charger sizes, fugitive factor per MWh, new / removed components without a v3.1 dual.
Pairs: v4_F1 = v4 main integrated vs v3.1 F1; v4_F2 = v4 main no_new_xb vs v3.1 F2; v4iid_F1 = v4 IId integrated vs v3.1 F1.
Writes SMOKE56_FIRST_ORDER.csv (pair x term x country) and evidence/W08_first_order.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa
import xarray as xr

W = Path(__file__).resolve().parents[1]
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/builds")
PKG = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1/networks")
SM = Path("/home/jin/v3fix/drill_pkg_13ebce95/runs/smoke56_v31")
N = 56
PAIRS = {"v4_F1": (PKG / "integrated_2920_3h_unsolved.nc", MAIN / "main/integrated/integrated_2920_3h_unsolved.nc", SM / "F1", "integrated"),
         "v4_F2": (PKG / "no_new_xb_2920_3h_unsolved.nc", MAIN / "main/no_new_xb/no_new_xb_2920_3h_unsolved.nc", SM / "F2", "no_new_xb"),
         "v4iid_F1": (PKG / "integrated_2920_3h_unsolved.nc", MAIN / "iid/integrated/integrated_2920_3h_unsolved.nc", SM / "F1", "integrated")}


def pset(n: pypsa.Network, sn) -> pd.DataFrame:
    P = pd.DataFrame({l: np.full(len(sn), float(n.loads.at[l, "p_set"])) for l in n.loads.index}, index=sn)
    t = n.loads_t.p_set
    if len(t.columns):
        P.loc[:, t.columns] = t.loc[sn, t.columns].to_numpy()
    return P


def zero_slack_substitute(S: pypsa.Network, sn) -> dict:
    """Countries whose solid-biomass pool was exactly used by fixed demand in the v3.1 smoke (fixed / pool >= 0.999, W12 F7: degenerate duals,
    114 vs 19,544 EUR/MWh between runs): their biomass is valued at the substitute instead of the degenerate dual - 0.90 (useful-heat efficiency of
    the overflow rule) x the band-heat price of the country (mean over its nodes, weighted by the overflow source-band shares), per snapshot."""
    led = S.meta["s2_demand_ledger"]["industry"]["biomass_overflow"]
    pools = S.stores[S.stores.bus.str.startswith("solid biomass")].groupby("country").e_initial.sum()
    lam = S.buses_t.marginal_price.loc[sn]
    out = {}
    for c, d in led.items():
        pot = float(pools.get(c, 0.0))
        if pot <= 0 or float(d["fixed_biomass_after_mwh"]) / pot < 0.999:
            continue
        sh = d.get("source_band_shares") or {"medium_a": 0.2, "medium_b": 0.8, "high": 0.0}
        band_car = {"medium_a": "industry heat medium A", "medium_b": "industry heat medium B", "high": "industry heat high"}
        y = np.zeros(len(sn)); tot = 0.0
        for b, s in sh.items():
            buses = S.buses[(S.buses.country == c) & (S.buses.carrier == band_car[b])].index
            buses = [x for x in buses if x in lam.columns]
            if s > 0 and buses:
                y += s * lam[buses].mean(axis=1).to_numpy(); tot += s
        if tot > 0:
            out[c] = 0.90 * y / tot
    return out


def main():
    rows, ev = [], {}
    for pid, (pa, pb, sdir, sc) in PAIRS.items():
        A = pypsa.Network(str(pa)); Bn = pypsa.Network(str(pb)); S = pypsa.Network(str(sdir / f"{sc}_SMOKE_TEST_ONLY_solved.nc"))
        sn = S.snapshots[:N]; w = S.snapshot_weightings.objective.loc[sn].to_numpy()
        lam = S.buses_t.marginal_price.loc[sn]
        sub = zero_slack_substitute(S, sn)
        ev.setdefault("substitute_valuation", {})[pid] = {c: dict(mean_eur_per_mwh=float(v.mean()), degenerate_dual_mean_eur_per_mwh=float(lam[f"solid biomass {c}"].mean()))
                                                          for c, v in sub.items()}
        PA, PB = pset(A, A.snapshots[:N]), pset(Bn, Bn.snapshots[:N])
        PA.index = sn; PB.index = sn
        loads = sorted(set(PA.columns) | set(PB.columns))
        miss, miss_mwh, proxied, proxied_mwh = [], [], [], []
        for l in loads:
            pa_ = PA[l].to_numpy() if l in PA.columns else np.zeros(N); pb_ = PB[l].to_numpy() if l in PB.columns else np.zeros(N)
            d = pb_ - pa_
            if not np.any(d):
                continue
            bus = (Bn.loads.at[l, "bus"] if l in Bn.loads.index else A.loads.at[l, "bus"])
            car = Bn.loads.at[l, "carrier"] if l in Bn.loads.index else A.loads.at[l, "carrier"]
            c = Bn.buses.at[bus, "country"] if bus in Bn.buses.index else A.buses.at[bus, "country"]
            if bus in lam.columns:
                price = lam[bus].to_numpy()
            else:   # bus new in v4 (e.g. KH industry oil final, MM agriculture biomass final): mean v3.1 price of the buses of the same country and carrier
                bc = Bn.buses.at[bus, "carrier"] if bus in Bn.buses.index else A.buses.at[bus, "carrier"]
                peers = [x for x in S.buses.index[(S.buses.country == c) & (S.buses.carrier == bc)] if x in lam.columns]
                if not peers:
                    miss.append(l); miss_mwh.append(float((d * w).sum())); continue
                price = lam[peers].mean(axis=1).to_numpy(); proxied.append(l); proxied_mwh.append(float((d * w).sum()))
            raw = float((d * price * w).sum())
            cor = float((d * sub[c] * w).sum()) if (str(car) == "biomass final energy" and c in sub) else raw
            rows.append(dict(pair=pid, term="load", item=str(car), country=str(c), delta_annual_mwh=float((d * w).sum()), cost_eur_raw=raw, cost_eur=cor))
        D = xr.open_dataset(sdir / "DUALS_BY_CONSTRAINT.nc")
        eb = D["Store-energy_balance"]
        tdim = [x for x in eb.dims if x.endswith("snapshot")][0]; sdim = [x for x in eb.dims if not x.endswith("snapshot")][0]
        e0 = {str(s): float(abs(v)) for s, v in zip(eb[sdim].values, eb.isel({tdim: 0}).transpose(sdim).values)}
        st = sorted(set(A.stores.index) | set(Bn.stores.index))
        for s in st:
            ea = float(A.stores.at[s, "e_initial"]) if s in A.stores.index else 0.0; eb_ = float(Bn.stores.at[s, "e_initial"]) if s in Bn.stores.index else 0.0
            if ea == eb_:
                continue
            if s not in e0:
                miss.append(s); continue
            c = (Bn.stores.at[s, "country"] if s in Bn.stores.index else A.stores.at[s, "country"])
            car = str(Bn.stores.at[s, "carrier"] if s in Bn.stores.index else A.stores.at[s, "carrier"])
            raw = -(eb_ - ea) * e0[s]
            cor = -(eb_ - ea) * float((sub[c] * w).sum() / w.sum()) if (car == "solid biomass" and c in sub) else raw
            rows.append(dict(pair=pid, term="pool", item=car, country=str(c), delta_annual_mwh=eb_ - ea, cost_eur_raw=raw, cost_eur=cor))
        ca, cb = A.meta.get("external_annual_caps", {}), Bn.meta.get("external_annual_caps", {})
        for g in sorted(set(ca) | set(cb)):
            if not g.endswith("gas production"):
                continue
            da = float(ca.get(g, 0.0)); db = float(cb.get(g, 0.0))
            if da == db:
                continue
            k = f"ResearchImportAnnual-{g}"
            y = float(abs(D[k].values)) if k in D.data_vars else 0.0
            c = Bn.generators.at[g, "country"] if g in Bn.generators.index else A.generators.at[g, "country"]
            rows.append(dict(pair=pid, term="gas_cap", item="gas production", country=str(c), delta_annual_mwh=db - da, cost_eur_raw=-(db - da) * y, cost_eur=-(db - da) * y))
        obj = json.loads((sdir / "SOLVE_RECEIPT.json").read_text())["objective"]
        R = pd.DataFrame([r for r in rows if r["pair"] == pid])
        est = float(R.cost_eur.sum())
        ev[pid] = dict(v31_network=str(pa), v4_network=str(pb), v31_smoke=str(sdir), v31_objective_eur=obj, first_order_delta_eur=est,
                       first_order_delta_raw_dual_eur=float(R.cost_eur_raw.sum()),
                       criterion="primary: first_order_delta_eur (zero-slack biomass at the substitute value) +- 50 %; the raw-dual value is reported only",
                       by_term={t: float(R[R.term == t].cost_eur.sum()) for t in ("load", "pool", "gas_cap")},
                       band_eur=[est - 0.5 * abs(est), est + 0.5 * abs(est)], expected_v4_objective_eur=obj + est, unmatched=miss[:50], n_unmatched=len(miss),
                       unmatched_load_annual_mwh=float(sum(miss_mwh)), gross_terms_eur=float(R.cost_eur.abs().sum()),
                       proxied_loads=len(proxied), proxied_load_annual_mwh=float(sum(proxied_mwh)),
                       not_included="EV battery / charger sizes (fleet proxy), fugitive factor per MWh of production, components without a v3.1 dual")
        print(pid, round(est / 1e9, 4), "bn EUR", {t: round(v / 1e9, 4) for t, v in ev[pid]["by_term"].items()}, "unmatched", len(miss))
    out = pd.DataFrame(rows)
    agg = out.groupby(["pair", "term", "item", "country"], as_index=False)[["delta_annual_mwh", "cost_eur"]].sum()
    agg.to_csv(W / "SMOKE56_FIRST_ORDER.csv", index=False, float_format="%.6g", lineterminator="\n")
    (W / "evidence").mkdir(exist_ok=True)
    (W / "evidence/W08_first_order.json").write_text(json.dumps(dict(status="INFERENCE (pre-solve, registered before any W08 solve)", method=__doc__, pairs=ev), indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
