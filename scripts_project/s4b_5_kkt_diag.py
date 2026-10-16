"""S4B-5 diagnostic of the decision-71 gate failures of a finished smoke solve (read-only; no solver call): rebuilds the linopy model from the
unsolved network exactly as s2_solve.py does (labels must equal the exported clabels / vlabels), recomputes the A1/A2 residual arrays of
s4b_acceptance.gate_a1_a2_solver_tol and attributes every failing row / column to its constraint or variable, component and carrier.

    python scripts_project/s4b_5_kkt_diag.py --solve-dir results_project/s4b/s4b5/solves/integrated \
        --network results_project/s4b/s4b5/builds/integrated/integrated_2920_3h_unsolved.nc --scenario integrated --output <json>
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

COMP = {"Link": "links", "Generator": "generators", "StorageUnit": "storage_units", "Store": "stores", "Line": "lines", "Bus": "buses"}


def attribute(store, labels, idx, n):
    """(group, component name, carrier) for the exported positions idx."""
    out = []
    for i in idx:
        lab = int(labels[i])
        try:
            name, coord = store.get_label_position(lab)
        except Exception:
            out.append(("?", None, None)); continue
        comp = next((k for k in COMP if str(name).startswith(k + "-")), None)
        cname = None
        if comp is not None:
            dim = next((d for d in coord if str(d).startswith(comp)), None)
            cname = str(coord[dim]) if dim else None
        carrier = None
        if cname is not None:
            df = getattr(n, COMP[comp])
            if cname in df.index and "carrier" in df:
                carrier = str(df.at[cname, "carrier"])
        out.append((str(name), cname, carrier))
    return out


def main(a):
    import logging
    import pypsa
    import scipy.sparse as sp
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    from s2_solve import set_representative_weights
    from assembly_components import install_research_constraint_hooks
    from phase4_static import config
    from s4b_acceptance import budgets, ABS_FLOOR, country_gross_co2_flows, pool_capacities, special_references
    t0 = time.time(); sd = Path(a.solve_dir)
    rec = json.loads((sd / "SOLVE_RECEIPT.json").read_text())
    n0 = pypsa.Network(str(a.network))
    N = int(rec["input_network"].get("truncated_to") or 0)
    if N:
        n0.set_snapshots(n0.snapshots[:N]); set_representative_weights(n0)
    n0.meta.update(solver_allowed=True, artifact_role=str(rec.get("label", "SMOKE_TEST_ONLY")) + "_UNSOLVED")
    m = n0.optimize.create_model(); install_research_constraint_hooks(n0)
    if (rec.get("scaling") or {}).get("objective_constants"):
        from s3b_scaling import remove_objective_constants
        remove_objective_constants(m)
    M = m.matrices
    cl, vl = np.load(sd / "lp" / "clabels.npy"), np.load(sd / "lp" / "vlabels.npy")
    if not (np.array_equal(np.asarray(M.clabels, dtype=np.int64), cl) and np.array_equal(np.asarray(M.vlabels, dtype=np.int64), vl)):
        raise SystemExit("rebuilt LP labels differ from the exported arrays")
    n = pypsa.Network(str(sorted(sd.glob("*_solved.nc"))[0]))
    cfg = config(a.repo, a.scenario); B = budgets(dict(cfg["research"]["solver"]["interior"]), float(rec.get("solver_parameters", {}).get("BarConvTol", 1e-8)))
    row_ref, col_ref, _ = special_references(m, n, cl, vl, country_gross_co2_flows(n), pool_capacities(n))
    lp = sd / "lp"; meta = json.loads((lp / "MATH_PROBLEM.json").read_text())
    A_ = {k: np.load(lp / (k + ".npy")) for k in ["cost", "col_lower", "col_upper", "row_lower", "row_upper", "start", "index", "value"]}
    x, pi, rc = [np.load(sd / "solution" / (k + ".npy")) for k in ["X", "Pi", "RC"]]
    nc, nr = meta["num_col"], meta["num_row"]
    A = sp.csc_matrix((A_["value"], A_["index"], A_["start"]), shape=(nr, nc)); absA = abs(A)
    act = A @ x; mag = absA @ np.abs(x); lo, hi = A_["row_lower"], A_["row_upper"]; lf, uf = np.isfinite(lo), np.isfinite(hi)
    rv = np.zeros(nr); rv[lf] = np.maximum(lo[lf] - act[lf], 0); rv[uf] = np.maximum(rv[uf], act[uf] - hi[uf])
    rref = np.maximum.reduce([np.where(lf, np.abs(lo), 0.0), np.where(uf, np.abs(hi), 0.0), mag, row_ref]); rtol = ABS_FLOOR + B["primal_relative"] * rref
    aty = A.T @ pi; absaty = absA.T @ np.abs(pi)
    resid = A_["cost"] - aty - rc; scale = np.maximum(1.0, np.abs(A_["cost"]) + absaty + np.abs(rc)); stat = np.abs(resid) / scale
    clf, cuf = np.isfinite(A_["col_lower"]), np.isfinite(A_["col_upper"])
    cs = np.where(~clf, np.maximum(rc, 0), 0) + np.where(~cuf, np.maximum(-rc, 0), 0); cs_n = cs / scale
    dt = B["dual_normalized"]
    out = dict(solve_dir=str(sd), budgets=B, seconds=None)
    for key, mask, store, labels, val in [("row_primal", rv > rtol, m.constraints, cl, rv / rtol), ("stationarity", stat > dt, m.variables, vl, stat / dt),
                                          ("column_dual_sign", cs_n > dt, m.variables, vl, cs_n / dt)]:
        idx = np.flatnonzero(mask)
        att = attribute(store, labels, idx, n)
        df = pd.DataFrame(att, columns=["group", "component", "carrier"]); df["ratio"] = val[idx]
        if key == "column_dual_sign":
            df["reduced_cost"] = rc[idx]; df["x"] = x[idx]
        if key == "row_primal":
            df["violation"] = rv[idx]
        out[key] = dict(count=int(len(idx)), by_group_carrier={f"{g} | {c}": int(k) for (g, c), k in df.groupby(["group", "carrier"], dropna=False).size().sort_values(ascending=False).head(25).items()},
                        components=int(df.component.nunique()), worst=df.sort_values("ratio", ascending=False).head(15).to_dict("records"))
    out["seconds"] = round(time.time() - t0, 1)
    Path(a.output).parent.mkdir(parents=True, exist_ok=True); Path(a.output).write_text(json.dumps(out, indent=1, default=str))
    for k in ["row_primal", "stationarity", "column_dual_sign"]:
        print(k, out[k]["count"], json.dumps(out[k]["by_group_carrier"])[:900])


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--repo", type=Path, default=HERE.parent); p.add_argument("--solve-dir", required=True); p.add_argument("--network", required=True)
    p.add_argument("--scenario", required=True); p.add_argument("--output", required=True)
    main(p.parse_args())
