"""S4C-5 (decision 84): Kirchhoff row-normalisation equivalence test and solver-setting comparison table from s2_solve.py run directories.

Tolerances fixed before the runs (S4C-5 item 1): objective relative difference <= 1e-6; main quantities (capacity and annual generation per
carrier x country of generators, power links and storage units) |difference| <= max(1 MW or 1 MWh, 1e-3 x |value|). The comparison table
(item 3): status, barrier iterations, solve time, peak memory, last barrier iteration (primal / dual objective, primal / dual infeasibility,
complementarity), old (S3B BarConvTol) and new (S4B solver-tolerance) acceptance verdicts with the failing gates, objective and pairwise
relative differences, main capacities / generation by country, number of values below the reporting cleanup thresholds.

    python scripts_project/s4c_5_compare.py --run A_kvl_off=<dir> --run A=<dir> --run B=<dir> --run C=<dir> --equivalence A_kvl_off,A --output <dir>
"""
from __future__ import annotations

import argparse
import itertools
import json
import logging
import re
from pathlib import Path

import pandas as pd

REL_OBJ = 1e-6
ABS_Q, REL_Q = 1.0, 1e-3
BARRIER_LINE = re.compile(r"^\s*(\d+)\*?\s+([-+.\deE]+)\s+([-+.\deE]+)\s+([-+.\deE]+)\s+([-+.\deE]+)\s+([-+.\deE]+)\s+(\d+)s\s*$")
LINK_POWER = ["OCGT", "CCGT", "CCGT CC", "OCGT methanol", "H2 Electrolysis", "H2 Fuel Cell", "H2 turbine", "battery charger", "battery discharger", "DAC", "Fischer-Tropsch", "methanolisation"]


def load_json(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else {}


def last_barrier(log):
    last = None
    if Path(log).exists():
        for line in Path(log).read_text(errors="ignore").splitlines():
            m = BARRIER_LINE.match(line)
            if m:
                last = m
    if not last:
        return {}
    g = last.groups()
    return dict(iteration=int(g[0]), primal_objective=float(g[1]), dual_objective=float(g[2]), primal_infeasibility=float(g[3]), dual_infeasibility=float(g[4]),
                complementarity=float(g[5]), seconds=int(g[6]))


def quantities(n):
    w = n.snapshot_weightings.generators
    rows = []
    g = n.generators
    for (car, c), x in g.groupby(["carrier", "country"]):
        rows.append(dict(component="Generator", carrier=car, country=c, capacity_mw=float(x.p_nom_opt.sum()),
                         energy_mwh=float((n.generators_t.p[x.index].mul(w, axis=0)).sum().sum()) if len(x.index.intersection(n.generators_t.p.columns)) == len(x) else float("nan")))
    su = n.storage_units
    for (car, c), x in su.groupby(["carrier", "country"]):
        rows.append(dict(component="StorageUnit", carrier=car, country=c, capacity_mw=float(x.p_nom_opt.sum()),
                         energy_mwh=float((n.storage_units_t.p_dispatch[x.index].mul(w, axis=0)).sum().sum())))
    L = n.links[n.links.carrier.isin(LINK_POWER)]
    for (car, c), x in L.groupby(["carrier", "country"]):
        rows.append(dict(component="Link", carrier=car, country=c, capacity_mw=float((x.p_nom_opt * x.efficiency).sum()),
                         energy_mwh=float((-n.links_t.p1[x.index].mul(w, axis=0)).sum().sum())))
    return pd.DataFrame(rows).set_index(["component", "carrier", "country"]).sort_index()


def run_summary(tag, d):
    d = Path(d); r = load_json(d / "SOLVE_RECEIPT.json"); g = load_json(d / "V5_GATES.json"); ic = load_json(d / "INTERIOR_CHECKS.json")
    st = r.get("gurobi_log_stats", {})
    it = st.get("lines", {}).get("barrier", [])
    m = re.search(r"in (\d+) iterations", it[0]) if it else None
    cleanup = ic.get("cleanup_thresholds", {}).get("groups", {})
    a12 = g.get("A1_A2_S4B", {})
    fails_new = [k for k in ("A1_A2_S4B", "A3_S4B", "A4", "A5_S4B", "A6", "B1_S4B", "B2", "B3_S4B", "B8", "B11", "B12", "B13", "B14", "B15", "B1_BUNKERS") if isinstance(g.get(k), dict) and not g[k].get("passed", True)]
    fails_old = [k for k in ("A1_A2", "A3", "A4", "A5", "A6", "B1", "B2", "B3", "B8", "B11", "B12", "B13", "B14", "B15", "B1_BUNKERS") if isinstance(g.get(k), dict) and not g[k].get("passed", True)]
    return dict(run=tag, dir=str(d), profile=r.get("solver_profile"), kvl_normalisation=r.get("scaling", {}).get("kirchhoff_row_normalisation", {}).get("applied"),
                status=r.get("status"), termination=r.get("termination_condition"), barrier_iterations=int(m.group(1)) if m else None, barrier_lines=it,
                crossover_lines=st.get("lines", {}).get("crossover"), result_lines=st.get("lines", {}).get("result"),
                solve_seconds=r.get("solve_seconds"), peak_rss_gib=(r.get("peak_rss_bytes") or 0) / 2**30, objective=r.get("objective"),
                matrix_range=st.get("coefficient_statistics", {}).get("matrix"), rhs_range=st.get("coefficient_statistics", {}).get("rhs"),
                last_barrier_iteration=last_barrier(d / "GUROBI_LOG_SCRUBBED.txt"),
                acceptance_new_solver_tolerances=g.get("all_passed_solver_tolerances"), acceptance_old_barconvtol=g.get("all_passed_barconvtol"),
                failing_gates_new=fails_new, failing_gates_old=fails_old,
                a1a2_new=dict(row_fail_count=a12.get("row_fail_count"), row_max_ratio_to_budget=a12.get("row_max_ratio_to_budget"), stationarity_normalized_max=a12.get("stationarity_normalized_max"),
                              stationarity_fail_count=a12.get("stationarity_fail_count"), dual_sign_normalized_max=a12.get("dual_sign_normalized_max"), dual_sign_fail_count=a12.get("dual_sign_fail_count"),
                              relative_gap=a12.get("relative_gap"), complementarity_over_scale=a12.get("complementarity_over_scale")),
                b1_bunkers=(g.get("B1_BUNKERS") or {}).get("passed"),
                cleanup_below=int(sum(v.get("below", 0) for v in cleanup.values())), cleanup_nonzero=int(sum(v.get("nonzero", 0) for v in cleanup.values())),
                kvl=r.get("scaling", {}).get("kirchhoff_row_normalisation"), solved_network=r.get("solved_network"))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="append", required=True); ap.add_argument("--equivalence", default=None); ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    runs = dict(x.split("=", 1) for x in a.run)
    S = {k: run_summary(k, d) for k, d in runs.items()}
    import pypsa
    logging.disable(logging.WARNING)
    Q = {}
    for k, s in S.items():
        if s["status"] == "ok" and s["solved_network"] and Path(s["solved_network"]).exists():
            Q[k] = quantities(pypsa.Network(s["solved_network"]))
    pair = {}
    for x, y in itertools.combinations([k for k in S if S[k]["objective"] is not None], 2):
        ox, oy = S[x]["objective"], S[y]["objective"]
        pair[f"{x}|{y}"] = abs(ox - oy) / max(abs(ox), abs(oy))
    out = dict(runs=S, objective_pairwise_relative_difference=pair, tolerances=dict(objective_relative=REL_OBJ, quantity_abs=ABS_Q, quantity_rel=REL_Q))
    a.output.mkdir(parents=True, exist_ok=True)
    if Q:
        allq = pd.concat({k: v for k, v in Q.items()}, axis=1)
        allq.to_csv(a.output / "S4C5_QUANTITIES_BY_CARRIER_COUNTRY.csv")
    if a.equivalence:
        x, y = a.equivalence.split(",")
        eq = dict(pair=[x, y], objective_relative_difference=pair.get(f"{x}|{y}", pair.get(f"{y}|{x}")))
        if x in Q and y in Q:
            qx, qy = Q[x].align(Q[y], fill_value=0.0)
            res = {}
            for col in ["capacity_mw", "energy_mwh"]:
                dlt = (qx[col] - qy[col]).abs(); tol = (REL_Q * pd.concat([qx[col].abs(), qy[col].abs()], axis=1).max(axis=1)).clip(lower=ABS_Q)
                bad = dlt > tol
                res[col] = dict(items=int(len(dlt)), beyond_tolerance=int(bad.sum()), max_abs_difference=float(dlt.max()),
                                worst=[dict(key="|".join(map(str, i)), a=float(qx.at[i, col]), b=float(qy.at[i, col]), diff=float(dlt[i])) for i in dlt.sort_values(ascending=False).index[:8]])
            eq["quantities"] = res
            eq["equivalent"] = bool((eq["objective_relative_difference"] or 1) <= REL_OBJ and all(v["beyond_tolerance"] == 0 for v in res.values()))
        out["equivalence"] = eq
    (a.output / "S4C5_COMPARISON.json").write_text(json.dumps(out, indent=1, sort_keys=True, default=str))
    rows = []
    for k, s in S.items():
        lb = s["last_barrier_iteration"] or {}
        rows.append(dict(run=k, profile=s["profile"], kvl=s["kvl_normalisation"], status=s["status"], termination=s["termination"], barrier_iterations=s["barrier_iterations"],
                         solve_s=round(s["solve_seconds"] or 0, 1), peak_gib=round(s["peak_rss_gib"], 2), primal_inf=lb.get("primal_infeasibility"), dual_inf=lb.get("dual_infeasibility"),
                         compl=lb.get("complementarity"), new_thresholds=s["acceptance_new_solver_tolerances"], old_thresholds=s["acceptance_old_barconvtol"],
                         failing_new=";".join(s["failing_gates_new"]), failing_old=";".join(s["failing_gates_old"]), objective=s["objective"], matrix_range=s["matrix_range"],
                         cleanup_below=s["cleanup_below"], cleanup_nonzero=s["cleanup_nonzero"]))
    t = pd.DataFrame(rows); t.to_csv(a.output / "S4C5_COMPARISON_TABLE.csv", index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30)
    print(t.to_string()); print(json.dumps(pair)); print(json.dumps(out.get("equivalence"), default=str)[:2500])


if __name__ == "__main__":
    main()
