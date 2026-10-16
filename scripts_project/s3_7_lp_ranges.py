"""S3-7 (user supplement 2026-10-16, item 2): coefficient ranges of the 56x3h smoke LP (no solve).

Builds the linopy model exactly as s2_solve.py does (truncate to N snapshots, representative weights 8760/N, research constraint hooks)
and reports min/max absolute nonzero values of the constraint matrix, the objective and the right-hand side, the ratio max/min, and which
(constraint, variable) names carry the extreme coefficients. Writes <output>.json.

    python scripts_project/s3_7_lp_ranges.py --network <nc> --scenario integrated --truncate 56 --output <json>
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def main():
    p = argparse.ArgumentParser(); p.add_argument("--repo", type=Path, default=HERE.parent); p.add_argument("--network", type=Path, required=True); p.add_argument("--scenario", required=True)
    p.add_argument("--truncate", type=int, default=56); p.add_argument("--output", type=Path, required=True); p.add_argument("--top", type=int, default=12)
    a = p.parse_args()
    import pypsa, logging
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    from s2_solve import set_representative_weights
    from assembly_components import install_research_constraint_hooks
    n = pypsa.Network(str(a.network))
    if a.truncate:
        n.set_snapshots(n.snapshots[:a.truncate])
        set_representative_weights(n)
    n.meta["solver_allowed"] = True
    m = n.optimize.create_model(); install_research_constraint_hooks(n)
    M = m.matrices
    A = M.A.tocoo(); b = np.asarray(M.b, dtype=float); c = np.asarray(M.c, dtype=float)
    vl = np.asarray(M.vlabels); cl = np.asarray(M.clabels)
    vname = {}; cname = {}

    def var_name(label):
        if label not in vname:
            try:
                vname[label] = m.variables.get_name_by_label(int(label))
            except Exception:
                vname[label] = "?"
        return vname[label]

    def con_name(label):
        if label not in cname:
            try:
                cname[label] = m.constraints.get_name_by_label(int(label))
            except Exception:
                cname[label] = "?"
        return cname[label]

    absA = np.abs(A.data); nz = absA > 0
    out = dict(network=str(a.network), scenario=a.scenario, snapshots=int(len(n.snapshots)), weight_h=float(n.snapshot_weightings.generators.iloc[0]),
               size=dict(num_col=int(A.shape[1]), num_row=int(A.shape[0]), nnz=int(nz.sum())))

    def extremes(vals, rows, cols, k, name):
        order = np.argsort(vals)
        small = order[:k]; large = order[-k:][::-1]
        def describe(idx):
            res = []
            for i in idx:
                res.append(dict(value=float(vals[i]), constraint=con_name(cl[rows[i]]) if rows is not None else None, variable=var_name(vl[cols[i]]) if cols is not None else None))
            return res
        def groups(idx):
            cnt = Counter((con_name(cl[rows[i]]) if rows is not None else "-", var_name(vl[cols[i]]) if cols is not None else "-") for i in idx)
            return [dict(constraint=k_[0], variable=k_[1], count=v) for k_, v in cnt.most_common(8)]
        q = np.quantile(vals, [0.0, 0.01, 0.5, 0.99, 1.0])
        # groups of the smallest 1 % and largest 1 %
        lo = order[: max(1, int(0.01 * len(order)))]; hi = order[-max(1, int(0.01 * len(order))):]
        return {name: dict(min=float(q[0]), p01=float(q[1]), median=float(q[2]), p99=float(q[3]), max=float(q[4]), ratio_max_min=float(q[4] / q[0]) if q[0] > 0 else None,
                           smallest=describe(small), largest=describe(large), groups_smallest_1pct=groups(lo), groups_largest_1pct=groups(hi))}

    out.update(extremes(absA[nz], A.row[nz], A.col[nz], a.top, "matrix"))
    bnz = np.abs(b) > 0
    out.update(extremes(np.abs(b[bnz]), np.arange(len(b))[bnz], None, a.top, "rhs"))
    cnz = np.abs(c) > 0
    out.update(extremes(np.abs(c[cnz]), None, np.arange(len(c))[cnz], a.top, "objective"))
    # variable bounds (finite, nonzero)
    lb = np.asarray(M.lb, dtype=float); ub = np.asarray(M.ub, dtype=float)
    fin = np.isfinite(ub) & (np.abs(ub) > 0)
    out["bounds"] = dict(finite_nonzero_ub=int(fin.sum()), ub_min=float(np.abs(ub[fin]).min()) if fin.any() else None, ub_max=float(np.abs(ub[fin]).max()) if fin.any() else None,
                         ub_largest=[dict(value=float(ub[i]), variable=var_name(vl[i])) for i in np.argsort(-np.where(fin, np.abs(ub), -1))[: a.top]])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=1, default=str))
    for k in ["matrix", "rhs", "objective"]:
        d = out[k]
        print(f"== {k}: min {d['min']:.3e} p01 {d['p01']:.3e} median {d['median']:.3e} p99 {d['p99']:.3e} max {d['max']:.3e} ratio {d['ratio_max_min']:.3e}")
        print("   smallest groups:", [(g['constraint'], g['variable'], g['count']) for g in d['groups_smallest_1pct'][:5]])
        print("   largest groups:", [(g['constraint'], g['variable'], g['count']) for g in d['groups_largest_1pct'][:5]])
    print("== bounds:", {k: v for k, v in out["bounds"].items() if k != "ub_largest"}, [(x["variable"], "%.3e" % x["value"]) for x in out["bounds"]["ub_largest"][:5]])


if __name__ == "__main__":
    main()
