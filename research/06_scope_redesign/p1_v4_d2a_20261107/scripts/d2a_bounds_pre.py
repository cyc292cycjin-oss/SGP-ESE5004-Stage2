"""V4 D2a section 6.1 (decisions 214 item 5 / 220; Fable F-21): alarm lines of the objective change of the D2a networks against the D1 networks, registered
BEFORE the D2a solves (SMOKE56_D2A.md section 1). The alarm line is a necessary condition ("violated -> something is wrong"), not a pass gate.

Change set (C8 of scripts/d2a_static.py, by class; decision 212 (b)):
  right-hand side (lower bound from the D1 duals, V(b) convex, y_D1 a subgradient: dV >= y_D1'(b_D2a - b_D1)):
    (a) solid-biomass pool sizes (T04): Store e_initial / e_nom of the EFB (and 5150-offset) pools; dual = |Store-energy_balance| at the first snapshot
        (marginal value of initial energy, EUR/MWh) of the D1 solve; the 56-snapshot solve truncates the pools, so the annual change is scaled by the
        solved / full e_initial ratio of the store;
    (b) the TH2 4 PHS group 950 -> 171 MW: dual = sum over snapshots of |StorageUnit-fix-p_dispatch-upper| + |StorageUnit-fix-p_store-upper| +
        max_hours x |StorageUnit-fix-state_of_charge-upper| (value per MW of the fixed capacity);
    (c) the TH reservoir inflows re-shared to the reclassified 608.2 MW: existing TH reservoirs lose inflow (dual = |StorageUnit-energy_balance| per MWh,
        the water value); the new reservoir is a NEW component (no D1 dual): its contribution is bounded by -min(608.2 MW x sum_t lambda_TH2 4,t w_t,
        max_t lambda_TH2 4,t x its inflow energy) - a loose but valid completion (the new unit cannot earn more than its capacity or its water allows).
  cost class: none (no marginal / capital cost changes vs D1).
  coefficient class (first-order estimate only, NO bound): methanolisation efficiency3 (CO2 input per MWh H2, 4.0321 -> 4.02482 MWh_MeOH per t) and the
        fuel-carbon port efficiency4; dZ = sum_t price(bus) x d(coefficient) x p0_t x w_t at the D1 solution.
  tolerance: +-1e-6 x |V_D1| (barrier 1e-6); alarm line: dV < LB_rhs - tol - 2 x |FO_coefficient| -> violated (the coefficient term has no bound; a 100 %
        margin is placed on its first-order size).
Writes evidence/D2A_BOUNDS_PRE.json and tables/D2A_BOUNDS_PRE.csv.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa
import xarray as xr

W = Path(__file__).resolve().parents[1]
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
RUNS = {"R1_v4d2a_F1": ("v4d1_F1", "integrated"), "R2_v4d2a_F2": ("v4d1_F2", "no_new_xb")}
PHS_OLD = "existing_survivor::TH2 4::Hydro::6b2ad09f452a"; HYD_NEW = "existing_survivor::TH2 4::hydro existing::D2A"


def sum_abs(D, var, idx):
    if var not in D.data_vars:
        return pd.Series(0.0, index=idx)
    x = D[var]; tdim = [d for d in x.dims if d.endswith("snapshot")][0]; cdim = [d for d in x.dims if not d.endswith("snapshot")][0]
    s = pd.Series(np.abs(x).sum(tdim).transpose(cdim).values, index=[str(c) for c in x[cdim].values])
    return s.reindex(idx).fillna(0.0)


def first_row_abs(D, var, idx):
    x = D[var]; tdim = [d for d in x.dims if d.endswith("snapshot")][0]; cdim = [d for d in x.dims if not d.endswith("snapshot")][0]
    s = pd.Series(np.abs(x.isel({tdim: 0})).transpose(cdim).values, index=[str(c) for c in x[cdim].values])
    return s.reindex(idx).fillna(0.0)


def per_snapshot_abs(D, var):
    x = D[var]; tdim = [d for d in x.dims if d.endswith("snapshot")][0]; cdim = [d for d in x.dims if not d.endswith("snapshot")][0]
    return pd.DataFrame(np.abs(x.transpose(tdim, cdim).values), columns=[str(c) for c in x[cdim].values])


def main():
    out, rows = {}, []
    for rid, (d1run, sc) in RUNS.items():
        S = MAIN / "v4d1/smoke56" / d1run
        rec = json.loads((S / "SOLVE_RECEIPT.json").read_text())
        ns = pypsa.Network(str(S / f"{sc}_SMOKE_TEST_ONLY_solved.nc"))          # D1 solved (56 snapshots)
        n1 = pypsa.Network(str(MAIN / "v4d1/builds/main" / sc / f"{sc}_2920_3h_unsolved.nc"))   # D1 full
        n2 = pypsa.Network(str(MAIN / "v4d2a/builds/main" / sc / f"{sc}_2920_3h_unsolved.nc"))  # D2a full
        D = xr.open_dataset(S / "DUALS_BY_CONSTRAINT.nc")
        w = ns.snapshot_weightings.objective.to_numpy(float); T = len(ns.snapshots)
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
            pool_rows.append(dict(run=rid, store=s, e_initial_D1_mwh=a, e_initial_D2a_mwh=b, delta_annual_mwh=b - a, truncation_ratio=ratio, delta_truncated_mwh=d_tr,
                                  marginal_value_eur_per_mwh=val, lb_term_eur=-d_tr * val, e_end_D1_mwh=float(ns.stores_t.e[s].iloc[-1]) if s in ns.stores_t.e else None))
        terms["pools_rhs_lower_bound_eur"] = lb_pool
        # (b) PHS capacity of the TH2 4 group
        su1, su2 = n1.storage_units, n2.storage_units
        dp = float(su2.at[PHS_OLD, "p_nom"]) - float(su1.at[PHS_OLD, "p_nom"]) if PHS_OLD in su2.index else -float(su1.at[PHS_OLD, "p_nom"])
        cap_val = float(sum_abs(D, "StorageUnit-fix-p_dispatch-upper", [PHS_OLD]).iloc[0] + sum_abs(D, "StorageUnit-fix-p_store-upper", [PHS_OLD]).iloc[0]
                        + float(ns.storage_units.at[PHS_OLD, "max_hours"]) * sum_abs(D, "StorageUnit-fix-state_of_charge-upper", [PHS_OLD]).iloc[0])
        terms["phs_capacity_delta_mw"] = dp; terms["phs_capacity_value_eur_per_mw"] = cap_val; terms["phs_rhs_lower_bound_eur"] = -dp * cap_val
        # (c) TH reservoir inflows (existing units) + the new reservoir completion
        inf1, inf2 = n1.storage_units_t.inflow, n2.storage_units_t.inflow
        th = [u for u in su1.index if su1.at[u, "country"] == "TH" and su1.at[u, "carrier"] == "hydro existing" and u in inf1.columns]
        wv = per_snapshot_abs(D, "StorageUnit-energy_balance") if "StorageUnit-energy_balance" in D.data_vars else None
        snaps = ns.snapshots; lb_inflow = 0.0; infl_rows = []
        for u in th:
            d = (inf2[u].reindex(snaps).to_numpy(float) if u in inf2.columns else 0.0) - inf1[u].reindex(snaps).to_numpy(float)
            if not np.any(d):
                continue
            v = wv[u].to_numpy(float) if (wv is not None and u in wv.columns) else np.zeros(T)
            lb_u = float(-(d * v).sum())
            lb_inflow += lb_u
            infl_rows.append(dict(run=rid, unit=u, delta_inflow_energy_mwh=float((d * w).sum()), mean_water_value_eur_per_mwh=float(v.mean()), lb_term_eur=lb_u))
        terms["th_inflow_rhs_lower_bound_eur"] = lb_inflow
        node = str(su2.at[HYD_NEW, "bus"]) if HYD_NEW in su2.index else "TH2 4"
        lam_node = lam[node].reindex(snaps).to_numpy(float) if node in lam.columns else np.zeros(T)
        e_new = float((inf2[HYD_NEW].reindex(snaps).to_numpy(float) * w).sum()) if HYD_NEW in inf2.columns else 0.0
        p_new = float(su2.at[HYD_NEW, "p_nom"]) if HYD_NEW in su2.index else 0.0
        comp = -min(p_new * float((lam_node * w).sum()), float(lam_node.max()) * e_new) if p_new else 0.0
        terms["new_reservoir_completion_eur"] = comp; terms["new_reservoir_p_nom_mw"] = p_new; terms["new_reservoir_inflow_56snap_mwh"] = e_new
        terms["new_reservoir_node_price_mean_eur_per_mwh"] = float((lam_node * w).sum() / w.sum())
        # coefficient class: methanolisation efficiency3 / fuel-carbon efficiency4
        fo = 0.0; coef_rows = []
        for k in sorted(set(n1.links.index) & set(n2.links.index)):
            for col in ("efficiency3", "efficiency4"):
                if col not in n1.links.columns or col not in n2.links.columns:
                    continue
                a, b = float(n1.links.at[k, col]), float(n2.links.at[k, col])
                if not np.isfinite(a) or not np.isfinite(b) or a == b or k not in ns.links_t.p0.columns:
                    continue
                bus = str(n2.links.at[k, "bus" + col[-1]])
                price = lam[bus].reindex(snaps).to_numpy(float) if bus in lam.columns else np.zeros(T)
                p0 = ns.links_t.p0[k].reindex(snaps).to_numpy(float)
                # output at port j = -eff_j x p0 (sign convention: a negative efficiency is an input); cost change = -price x d(eff) x p0
                dz = float(-(price * (b - a) * p0 * w).sum())
                fo += dz
                coef_rows.append(dict(run=rid, link=k, column=col, eff_D1=a, eff_D2a=b, bus=bus, flow_p0_mwh=float((p0 * w).sum()), mean_bus_price=float((price * w).sum() / w.sum()), first_order_eur=dz))
        terms["coefficient_first_order_eur"] = fo; terms["coefficient_links"] = len(coef_rows)
        LB = lb_pool + terms["phs_rhs_lower_bound_eur"] + lb_inflow + comp
        tol = 1e-6 * abs(float(rec["objective"]))
        out[rid] = dict(d1_run=d1run, d1_objective_eur=float(rec["objective"]), d1_objective_lp_eur=float(rec.get("objective_lp", float("nan"))),
                        d1_network_sha256=(rec.get("input_network") or {}).get("sha256"), snapshots=T, weight_sum_h=float(w.sum()), terms=terms,
                        rhs_lower_bound_eur=LB, tolerance_eur=tol, alarm_line_eur=LB - tol - 2.0 * abs(fo),
                        rule="violated if dV = V_D2a - V_D1 < rhs_lower_bound - tolerance - 2 x |coefficient first order| (necessary condition, not a gate)",
                        expected_note=("INFERENCE: the ID / MY / TH EFB pools were fully used in D1 (positive marginal values), so dV is probably well above the lower bound; "
                                       "the PHS capacity loss and the reservoir re-sharing are small; the methanol coefficient term is tiny"),
                        pools=pool_rows, inflows=infl_rows, coefficients=coef_rows)
        rows.append(dict(run=rid, d1_objective_eur=float(rec["objective"]), pools_lb_eur=lb_pool, phs_lb_eur=terms["phs_rhs_lower_bound_eur"], inflow_lb_eur=lb_inflow,
                         new_reservoir_completion_eur=comp, rhs_lower_bound_eur=LB, coefficient_first_order_eur=fo, tolerance_eur=tol, alarm_line_eur=LB - tol - 2.0 * abs(fo)))
        print(rid, "LB", round(LB / 1e6, 3), "M EUR | pools", round(lb_pool / 1e6, 3), "phs", round(terms["phs_rhs_lower_bound_eur"] / 1e6, 3), "inflow", round(lb_inflow / 1e6, 3),
              "new res", round(comp / 1e6, 3), "| coef FO", round(fo / 1e6, 4), "| tol", round(tol / 1e6, 3), "| alarm", round((LB - tol - 2 * abs(fo)) / 1e6, 3), flush=True)
        D.close()
    (W / "evidence").mkdir(exist_ok=True); (W / "tables").mkdir(exist_ok=True)
    (W / "evidence/D2A_BOUNDS_PRE.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    pd.DataFrame(rows).to_csv(W / "tables/D2A_BOUNDS_PRE.csv", index=False, float_format="%.6f", lineterminator="\n")


if __name__ == "__main__":
    main()
