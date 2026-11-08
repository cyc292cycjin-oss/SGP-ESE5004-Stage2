"""V4 D2c section 6 (registration BEFORE the solves; SMOKE56_D2C.md section 1): alarm lines of the objective change of the D2c networks against the D2b smoke
solves (results_project/v4d2b/smoke56). The alarm line is a necessary condition ("violated -> something is wrong"), not a pass gate.

Change set (C8 of scripts/d2c_static.py, by class; decision 212 (b)):
  right-hand side (lower bound from the D2b duals, V(b) convex, y_D2b a subgradient: dV >= y_D2b'(b_D2c - b_D2b)):
    (a) oil palm trunk pool sizes (T05): Store e_initial / e_nom; dual = |Store-energy_balance| at the first snapshot (marginal value of the initial energy,
        EUR/MWh) of the D2b solve; the 56-snapshot solve truncates the pools, so the annual change is scaled by the solved / full e_initial ratio;
    (c) overflow useful-heat loads (source_band_basis post_product): dLoad x the band-bus price, sum over the 56 snapshots with the objective weights
        (the bus price lambda_t = nodal-balance dual per weighted MWh of the D2b solve).
  cost class (upper bound of that class from the D2b solution, V(c) concave: V(c + dc) <= V(c) + x_D2b'dc; the class contribution is >= 0 because the
    LNG import marginal cost only rises and the dispatch is >= 0):
    (b) LNG import marginal cost +0.7907 EUR/MWh: x = LNG import dispatch of the D2b solve.
  coefficient class: none.
  tolerance: 1e-6 x |V_D2b| (barrier 1e-6). Alarm line (lower): dV < rhs lower bound - tolerance -> violated. Expected size (INFERENCE): dV ~ rhs lower
  bound + (0 ... cost first-order upper bound) + the convexity excess of the trunk cut (the replacement routes cost more than the D2b marginal value).
Writes evidence/D2C_BOUNDS_PRE.json and tables/D2C_BOUNDS_PRE.csv. Nothing is solved.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa
import xarray as xr

W = Path(__file__).resolve().parents[1]
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
RUNS = {"R1_v4d2c_F1": ("v4d2b_F1", "integrated"), "R2_v4d2c_F2": ("v4d2b_F2", "no_new_xb")}


def first_row_abs(D, var, idx):
    x = D[var]; tdim = [d for d in x.dims if d.endswith("snapshot")][0]; cdim = [d for d in x.dims if not d.endswith("snapshot")][0]
    s = pd.Series(np.abs(x.isel({tdim: 0})).transpose(cdim).values, index=[str(c) for c in x[cdim].values])
    return s.reindex(idx).fillna(0.0)


def main():
    out, rows = {}, []
    for rid, (d2brun, sc) in RUNS.items():
        S = MAIN / "v4d2b/smoke56" / d2brun
        rec = json.loads((S / "SOLVE_RECEIPT.json").read_text())
        ns = pypsa.Network(str(S / f"{sc}_SMOKE_TEST_ONLY_solved.nc"))          # D2b solved (56 snapshots)
        n1 = pypsa.Network(str(MAIN / "v4d2b/builds/main" / sc / f"{sc}_2920_3h_unsolved.nc"))   # D2b full
        n2 = pypsa.Network(str(MAIN / "v4d2c/builds/main" / sc / f"{sc}_2920_3h_unsolved.nc"))  # D2c full
        D = xr.open_dataset(S / "DUALS_BY_CONSTRAINT.nc")
        w = ns.snapshot_weightings.objective.to_numpy(float); snaps = ns.snapshots
        lam = ns.buses_t.marginal_price
        terms = {}
        # (a) pools
        e0 = first_row_abs(D, "Store-energy_balance", ns.stores.index)
        pool_rows = []; lb_pool = 0.0
        for s in sorted(set(n1.stores.index) & set(n2.stores.index)):
            a, b = float(n1.stores.at[s, "e_initial"]), float(n2.stores.at[s, "e_initial"])
            if a == b:
                continue
            ratio = float(ns.stores.at[s, "e_initial"]) / a if (s in ns.stores.index and a) else 0.0
            d_tr = (b - a) * ratio; val = float(e0.get(s, 0.0))
            lb_pool += -d_tr * val
            pool_rows.append(dict(run=rid, store=s, e_initial_D2b_mwh=a, e_initial_D2c_mwh=b, delta_annual_mwh=b - a, truncation_ratio=ratio, delta_truncated_mwh=d_tr,
                                  marginal_value_eur_per_mwh=val, lb_term_eur=-d_tr * val, e_end_D2b_mwh=float(ns.stores_t.e[s].iloc[-1]) if s in ns.stores_t.e else None))
        terms["pools_rhs_lower_bound_eur"] = lb_pool
        # (c) loads (static p_set changes; series changes would be listed by C8 as UNEXPECTED)
        load_rows = []; lb_load = 0.0
        for l in sorted(set(n1.loads.index) | set(n2.loads.index)):
            a = float(n1.loads.at[l, "p_set"]) if l in n1.loads.index else 0.0
            b = float(n2.loads.at[l, "p_set"]) if l in n2.loads.index else 0.0
            if a == b or l in n1.loads_t.p_set.columns or l in n2.loads_t.p_set.columns:
                continue
            bus = str((n2.loads if l in n2.loads.index else n1.loads).at[l, "bus"])
            price = lam[bus].reindex(snaps).to_numpy(float) if bus in lam.columns else np.zeros(len(snaps))
            term = float(((b - a) * price * w).sum())
            lb_load += term
            load_rows.append(dict(run=rid, load=l, bus=bus, account=str((n2.loads if l in n2.loads.index else n1.loads).at[l, "account"]), p_set_D2b_mw=a, p_set_D2c_mw=b,
                                  delta_annual_mwh=(b - a) * 8760.0, mean_bus_price=float((price * w).sum() / w.sum()), lb_term_eur=term))
        terms["loads_rhs_lower_bound_eur"] = lb_load
        # (b) cost class: LNG import marginal cost
        g1, g2 = n1.generators, n2.generators
        cost_rows = []; ub_cost = 0.0
        for gname in sorted(set(g1.index) & set(g2.index)):
            a, b = float(g1.at[gname, "marginal_cost"]), float(g2.at[gname, "marginal_cost"])
            if a == b:
                continue
            p = ns.generators_t.p[gname].reindex(snaps).to_numpy(float) if gname in ns.generators_t.p.columns else np.zeros(len(snaps))
            term = float(((b - a) * p * w).sum())
            ub_cost += term
            cost_rows.append(dict(run=rid, generator=gname, carrier=str(g2.at[gname, "carrier"]), mc_D2b=a, mc_D2c=b, dispatch_mwh=float((p * w).sum()), ub_term_eur=term))
        terms["cost_first_order_upper_bound_eur"] = ub_cost
        LB = lb_pool + lb_load
        tol = 1e-6 * abs(float(rec["objective"]))
        out[rid] = dict(d2b_run=d2brun, d2b_objective_eur=float(rec["objective"]), d2b_network_sha256=(rec.get("input_network") or {}).get("sha256"), snapshots=len(snaps),
                        weight_sum_h=float(w.sum()), terms=terms, rhs_lower_bound_eur=LB, tolerance_eur=tol, alarm_line_eur=LB - tol,
                        cost_class_range_eur=[0.0, ub_cost],
                        rule="violated if dV = V_D2c - V_D2b < rhs lower bound - tolerance (necessary condition, not a gate); the LNG cost class adds 0 ... its first-order upper bound",
                        expected_note=("INFERENCE: the trunk pools were fully used in D2b (positive marginal values), so dV is probably well above the lower bound (replacement routes "
                                       "cost more than the D2b marginal value: convexity excess, as in D2b +2.9 bn over its bound); the band reallocation is small; the LNG term is <= the upper bound"),
                        pools=pool_rows, loads=load_rows, costs=cost_rows)
        rows.append(dict(run=rid, d2b_objective_eur=float(rec["objective"]), pools_lb_eur=lb_pool, loads_lb_eur=lb_load, rhs_lower_bound_eur=LB, cost_ub_eur=ub_cost,
                         tolerance_eur=tol, alarm_line_eur=LB - tol, pools_changed=len(pool_rows), loads_changed=len(load_rows), lng_generators_changed=len(cost_rows)))
        print(rid, "LB", round(LB / 1e6, 3), "M EUR | pools", round(lb_pool / 1e6, 3), "loads", round(lb_load / 1e6, 4), "| cost UB", round(ub_cost / 1e6, 3),
              "| tol", round(tol / 1e6, 3), "| alarm", round((LB - tol) / 1e6, 3), "| n pools/loads/gens", len(pool_rows), len(load_rows), len(cost_rows), flush=True)
        D.close()
    (W / "evidence").mkdir(exist_ok=True); (W / "tables").mkdir(exist_ok=True)
    (W / "evidence/D2C_BOUNDS_PRE.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    pd.DataFrame(rows).to_csv(W / "tables/D2C_BOUNDS_PRE.csv", index=False, float_format="%.6f", lineterminator="\n")


if __name__ == "__main__":
    main()
