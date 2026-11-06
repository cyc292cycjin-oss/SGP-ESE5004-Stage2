"""V4 D1 section 7.2 (decision 214 item 5): bounds of the objective change of the D1 networks against the W08 networks, registered BEFORE the D1 solves.

    PYTHONHASHSEED=0 <env python> scripts/d1_bounds_pre.py

Change set (C8 of d1_static_extra.py): the five oil_palm_trunk Store marginal costs 0 -> proxy (cost class); no right-hand-side change (potentials,
loads, caps, fixed capacities identical), so the feasible set is the same.
  cost class: V(c) = min c'x is concave in c, so V(c + dc) <= V(c) + dc'x_W08 (x_W08 = the W08 smoke solution, feasible for the D1 LP): upper bound
              U = proxy x sum_t w_t p_trunk(t) (w = objective snapshot weighting of the solved 56-snapshot network); and dc >= 0 with p_trunk >= 0
              (discharge-only Stores) gives V(c + dc) >= V(c): lower bound 0.
  right-hand-side class: none -> the W08-dual lower-bound term is 0 (combination: the two classes would be added, each with its own bound; here only
              the cost class is present).
  numerical tolerance (fixed here): +-1e-6 x |V_W08| (barrier convergence 1e-6 of profile formal_barrier_1e6_t16).
Writes evidence/D1_BOUNDS_PRE.json and tables/D1_BOUNDS_PRE.csv.
"""
import json
from pathlib import Path

import pandas as pd
import pypsa

W = Path(__file__).resolve().parents[1]
R = Path("/home/jin/wt_v4_d1")
S8 = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/smoke56")
TRUNK = [f"{c} biomass oil_palm_trunk" for c in ("ID", "KH", "MY", "PH", "TH")]
RUNS = {"R1_v4d1_F1": ("v4_F1", "integrated"), "R2_v4d1_F2": ("v4_F2", "no_new_xb")}


def main():
    reg = pd.read_csv(R / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    proxy = float(reg.at["biomass_missing_cost_proxy", "value"])
    diff = json.loads((W / "evidence/D1_NETWORK_DIFF.json").read_text())
    out, rows = {}, []
    for rid, (w08, sc) in RUNS.items():
        assert diff[f"{sc}_2920_3h"]["C8_only_trunk_store_cost_differs"], f"{sc}: the networks differ in more than the trunk costs - the bound rule above does not apply"
        rec = json.loads((S8 / w08 / "SOLVE_RECEIPT.json").read_text())
        n = pypsa.Network(str(S8 / w08 / f"{sc}_SMOKE_TEST_ONLY_solved.nc"))
        w = n.snapshot_weightings.objective
        per = {s: float((n.stores_t.p[s] * w).sum()) for s in TRUNK}
        pot = {s: float(n.stores.at[s, "e_initial"]) for s in TRUNK}
        mc8 = {s: float(n.stores.at[s, "marginal_cost"]) for s in TRUNK}
        U = proxy * sum(per.values())
        tol = 1e-6 * abs(float(rec["objective"]))
        out[rid] = dict(w08_run=w08, w08_objective_eur=float(rec["objective"]), w08_objective_lp_eur=float(rec.get("objective_lp", float("nan"))),
                        w08_network_sha256=(rec.get("input_network") or {}).get("sha256"), proxy_eur_per_mwh=proxy, w08_trunk_marginal_cost=mc8,
                        trunk_energy_weighted_mwh=per, trunk_e_initial_mwh=pot, snapshots=int(len(n.snapshots)), weight_sum_h=float(w.sum()),
                        lower_bound_eur=0.0, upper_bound_eur=U, tolerance_eur=tol, registered_interval_eur=[-tol, U + tol],
                        expected_note="INFERENCE: the trunk pools were fully used in W08 at positive biomass prices far above the proxy, so x_W08 probably stays optimal and dV = U up to the barrier tolerance",
                        expected_objective_range_eur=[float(rec["objective"]) - tol, float(rec["objective"]) + U + tol])
        for s in TRUNK:
            rows.append(dict(run=rid, store=s, w08_weighted_dispatch_mwh=per[s], e_initial_mwh=pot[s], used_share=(per[s] / pot[s] if pot[s] else None), proxy=proxy, dV_upper_eur=proxy * per[s]))
        print(rid, "W08 objective", rec["objective"], "upper bound", U, "tol", tol, {s.split()[0]: round(per[s] / pot[s], 6) for s in TRUNK})
    (W / "evidence/D1_BOUNDS_PRE.json").write_text(json.dumps(out, indent=1) + "\n")
    (W / "tables").mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(W / "tables/D1_BOUNDS_PRE.csv", index=False, float_format="%.6f", lineterminator="\n")


if __name__ == "__main__":
    main()
