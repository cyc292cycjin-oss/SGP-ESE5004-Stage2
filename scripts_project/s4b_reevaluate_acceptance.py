"""S4B-0 item 2: re-evaluate finished smoke solves (S3B, S4A) under the decision-71 budgets; historical results are only read.

    python scripts_project/s4b_reevaluate_acceptance.py --solve-dir results_project/s4a/smoke/solves/integrated \
        --network results_project/s4a/smoke/builds/integrated/integrated_2920_3h_unsolved.nc --scenario integrated --output results_project/s4b/reeval/s4a_integrated

The linopy model is rebuilt from the unsolved network exactly as s2_solve.py builds it (truncation, decision-58 weights, research hooks,
objective constants removed when the run used scaling) only to recover the constraint / variable names of the exported LP rows and columns;
the rebuilt labels must equal the exported clabels / vlabels arrays, otherwise the script stops. No solver is called.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def main(a):
    import logging
    import pypsa
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    from s2_solve import set_representative_weights
    from assembly_components import install_research_constraint_hooks
    from phase4_static import config
    from s4b_acceptance import evaluate, all_passed
    t0 = time.time(); sd = Path(a.solve_dir); out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
    rec = json.loads((sd / "SOLVE_RECEIPT.json").read_text())
    n0 = pypsa.Network(str(a.network))
    N = int(rec["input_network"].get("truncated_to") or 0)
    if N:
        n0.set_snapshots(n0.snapshots[:N]); set_representative_weights(n0)
    n0.meta.update(solver_allowed=True, artifact_role=str(rec.get("label", "SMOKE_TEST_ONLY")) + "_UNSOLVED")   # as s2_solve.py before create_model (no solve here)
    m = n0.optimize.create_model(); install_research_constraint_hooks(n0)
    if (rec.get("scaling") or {}).get("objective_constants"):
        from s3b_scaling import remove_objective_constants
        remove_objective_constants(m)
    M = m.matrices
    cl, vl = np.load(sd / "lp" / "clabels.npy"), np.load(sd / "lp" / "vlabels.npy")
    same = bool(np.array_equal(np.asarray(M.clabels, dtype=np.int64), cl) and np.array_equal(np.asarray(M.vlabels, dtype=np.int64), vl))
    if not same:
        raise SystemExit("rebuilt LP labels differ from the exported arrays; names cannot be attached")
    solved = sorted(sd.glob("*_solved.nc"))[0]
    n = pypsa.Network(str(solved))
    cfg = config(a.repo, a.scenario); I = dict(cfg["research"]["solver"]["interior"])
    btol = float(rec.get("solver_parameters", {}).get("BarConvTol", 1e-8))
    gap = bool(n.meta.get("gap_diagnostic", {}).get("enabled"))
    res = evaluate(n, sd / "lp", sd / "solution", sd / "v5", I, btol, m=m, gap=gap)
    old = json.loads((sd / "V5_GATES.json").read_text())
    merged = dict(old); merged.update(res)
    summary = dict(source_solve_dir=str(sd), source_network=str(a.network), solved_network=str(solved), labels_verified=same, label=rec.get("label"), scenario=a.scenario,
                   old=dict(A1_A2=old.get("A1_A2", {}).get("passed"), A3=old.get("A3", {}).get("passed"), A5=old.get("A5", {}).get("passed"), B1=old.get("B1", {}).get("passed"), B3=old.get("B3", {}).get("passed"),
                            all_passed=all_passed(merged, "barconvtol")),
                   new=dict(A1_A2=res["A1_A2_S4B"]["passed"], A3=res["A3_S4B"]["passed"], A5=res["A5_S4B"]["passed"], B1=res.get("B1_S4B", {}).get("passed"), B3=res["B3_S4B"]["passed"],
                            all_passed=all_passed(merged, "solver_tolerances")),
                   seconds=time.time() - t0)
    (out / "V5_GATES_S4B_REEVALUATION.json").write_text(json.dumps(dict(summary=summary, gates_s4b=res), indent=1, default=float))
    print(json.dumps(summary, default=float))


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--repo", type=Path, default=HERE.parent); p.add_argument("--solve-dir", required=True); p.add_argument("--network", required=True)
    p.add_argument("--scenario", required=True); p.add_argument("--output", required=True)
    main(p.parse_args())
