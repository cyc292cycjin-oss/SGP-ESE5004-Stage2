"""V3 DIAG: structural scan of an exported LP (lp/ of s2_solve.py export_lp: CSC, original units, objective constants removed) for the
dual-reduction pattern that lets a presolve report INF_OR_UNBD without any barrier iteration - an improving column that can move to infinity
without violating any row. No solver, no licence.

Iterative rule (dual fixing / free column singletons, exact sign logic, no tolerances except the zero test of the cost):
  direction d = +1 (increase) or -1 (decrease) of column j is FREE when its bound in d is infinite and every ACTIVE row containing j is relaxed
  (or untouched) by the move: for d = +1, a_ij > 0 only in rows without an upper bound, a_ij < 0 only in rows without a lower bound (d = -1 mirrored);
  equality rows block both directions.
  - cost 0 and FREE in d  -> every active row containing j can always be satisfied by j: those rows are dropped (redundant), repeat
  - cost * d < 0 and FREE in d -> an unbounded improving ray (if the LP is feasible it is unbounded) -> reported with label, cost, bound
The rule is sufficient, not necessary: rays through several columns are not searched.

    python lp_scan.py <lp dir> <out.json> [--zero-cost-abs 0]
"""
import json
import sys
import time

import numpy as np


def main(lp, out, zero=0.0):
    t0 = time.time()
    L = lambda k: np.load(f"{lp}/{k}.npy")
    c = L("cost"); lb = L("col_lower"); ub = L("col_upper"); rl = L("row_lower"); ru = L("row_upper")
    start = L("start"); idx = L("index"); val = L("value"); vl = L("vlabels"); cl = L("clabels")
    ncol, nrow = len(c), len(rl)
    col_of = np.repeat(np.arange(ncol, dtype=np.int64), np.diff(start))
    has_up = np.isfinite(ru)[idx]; has_lo = np.isfinite(rl)[idx]
    # an entry blocks the increase of its column when (a>0 and the row has an upper bound) or (a<0 and the row has a lower bound)
    blk_up = ((val > 0) & has_up) | ((val < 0) & has_lo)
    blk_dn = ((val < 0) & has_up) | ((val > 0) & has_lo)
    del has_up, has_lo
    active = np.ones(nrow, dtype=bool)
    czero = np.abs(c) <= zero
    hist = []
    for it in range(200):
        act_e = active[idx]
        bu = np.bincount(col_of, weights=(blk_up & act_e), minlength=ncol) > 0
        bd = np.bincount(col_of, weights=(blk_dn & act_e), minlength=ncol) > 0
        free_up = (~bu) & np.isinf(ub) & (ub > 0)
        free_dn = (~bd) & np.isinf(lb) & (lb < 0)
        slack_cols = czero & (free_up | free_dn)
        # rows touched by a zero-cost free column (in a relaxing direction) are redundant
        drop_e = act_e & slack_cols[col_of] & (val != 0)
        rows_drop = np.unique(idx[drop_e])
        n_new = int(active[rows_drop].sum())
        hist.append(dict(iteration=it, active_rows=int(active.sum()), zero_cost_free_columns=int(slack_cols.sum()), rows_dropped=n_new))
        if n_new == 0:
            break
        active[rows_drop] = False
    imp_up = free_up & (c < -zero)
    imp_dn = free_dn & (c > zero)
    rays = []
    for j in np.flatnonzero(imp_up | imp_dn)[:500]:
        rows = idx[start[j]:start[j + 1]]
        rays.append(dict(col=int(j), label=int(vl[j]), cost=float(c[j]), direction=("+" if imp_up[j] else "-"), lb=float(lb[j]), ub=float(ub[j]),
                         rows_total=int(len(rows)), rows_active=int(active[rows].sum()), row_labels=[int(cl[r]) for r in rows[:12]]))
    tiny = np.flatnonzero((c != 0) & (np.abs(c) < 1e-9))
    res = dict(lp_dir=lp, num_col=int(ncol), num_row=int(nrow), nnz=int(len(val)), iterations=hist, improving_free_columns=int((imp_up | imp_dn).sum()),
               rays=rays, tiny_cost_columns=int(len(tiny)), tiny_cost_examples=[dict(label=int(vl[j]), cost=float(c[j])) for j in tiny[:50]],
               negative_cost_columns=int((c < 0).sum()), negative_cost_infinite_ub=int(((c < 0) & np.isinf(ub)).sum()),
               positive_cost_infinite_lb=int(((c > 0) & np.isinf(lb) & (lb < 0)).sum()), free_columns=int((np.isinf(lb) & np.isinf(ub)).sum()),
               seconds=round(time.time() - t0, 1))
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ("rays", "tiny_cost_examples", "iterations")} | dict(iterations=len(hist))))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 0.0)
