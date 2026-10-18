"""S4I (item 103) section C: static coefficient-range warning on the LP of a frozen network - model build only, NO solve.

    python scripts_project/s4i_lp_ranges.py --network <nc> --snapshots 56 --out <dir>

The first N daily snapshots of the 365x24h network are kept with their 24 h weights (set_snapshots, no representative re-weighting),
so every coefficient has the value it takes in the full-year LP; only the number of rows / columns shrinks (annual rows keep their
coefficients). The model is built the way scripts_project/s2_solve.py builds it (create_model, research hooks, then the S3B / S4C-5
scaling: objective constants out, Store energy in GWh / kt, Kirchhoff row normalisation) and the Gurobi-style ranges (matrix, objective,
bounds, rhs over non-zero finite entries) are reported before and after the scaling, with the constraint / variable groups that hold
the extremes. Nothing is solved, written back or exported besides the JSON.
"""
from pathlib import Path
import argparse, json, logging, sys, time, warnings
import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from s4i_static_audit import jsonable, sha


def rng(a):
    a = np.abs(np.asarray(a, dtype=float)); a = a[np.isfinite(a) & (a > 0)]
    return dict(n=int(a.size), min=float(a.min()) if a.size else None, max=float(a.max()) if a.size else None, ratio=float(a.max() / a.min()) if a.size else None,
                below_1e_6=int((a < 1e-6).sum()), above_1e_6=int((a > 1e6).sum()))


def ranges(m):
    M = m.matrices
    A = M.A
    return dict(matrix=rng(A.data if A is not None else []), objective=rng(M.c), bounds=rng(np.r_[M.lb, M.ub]), rhs=rng(M.b), shape=[int(A.shape[0]), int(A.shape[1])], nnz=int(A.nnz))


def groups(m, top=12):
    rows = []
    for name in m.constraints:
        con = m.constraints[name]
        c = np.asarray(con.coeffs.values, dtype=float); v = np.asarray(con.vars.values)
        ok = (v != -1) & np.isfinite(c) & (c != 0)
        if not ok.any():
            continue
        a = np.abs(c[ok])
        rows.append(dict(constraint=name, nnz=int(ok.sum()), min=float(a.min()), max=float(a.max()), ratio=float(a.max() / a.min())))
    vr = []
    for name in m.variables:
        var = m.variables[name]
        for side in ("lower", "upper"):
            b = np.abs(np.asarray(getattr(var, side).values, dtype=float)); b = b[np.isfinite(b) & (b > 0)]
            if b.size:
                vr.append(dict(variable=name, side=side, min=float(b.min()), max=float(b.max())))
    by_min = sorted(rows, key=lambda r: r["min"])[:top]; by_max = sorted(rows, key=lambda r: -r["max"])[:top]; by_ratio = sorted(rows, key=lambda r: -r["ratio"])[:top]
    return dict(smallest_coefficients=by_min, largest_coefficients=by_max, widest_rows=by_ratio, bounds_smallest=sorted(vr, key=lambda r: r["min"])[:top], bounds_largest=sorted(vr, key=lambda r: -r["max"])[:top])


def objective_groups(m, top=10):
    obj = m.objective
    ov, oc = np.asarray(obj.vars).ravel(), np.asarray(obj.coeffs).ravel()
    ok = (ov != -1) & (oc != 0) & np.isfinite(oc)
    lab = {}
    for name in m.variables:
        lv = np.asarray(m.variables[name].labels.values).ravel()
        for l in lv[lv != -1]:
            lab[int(l)] = name
    out = {}
    for v, c in zip(ov[ok], np.abs(oc[ok])):
        g = lab.get(int(v), "?"); r = out.setdefault(g, [np.inf, 0.0, 0])
        r[0] = min(r[0], c); r[1] = max(r[1], c); r[2] += 1
    rows = [dict(variable=k, min=v[0], max=v[1], n=v[2]) for k, v in out.items()]
    return dict(smallest=sorted(rows, key=lambda r: r["min"])[:top], largest=sorted(rows, key=lambda r: -r["max"])[:top])


def main(a):
    warnings.filterwarnings("ignore"); logging.disable(logging.WARNING)
    import pypsa
    from assembly_components import install_research_constraint_hooks
    from s3b_scaling import remove_objective_constants, select_stores, scale_store_energy, normalise_kvl_rows, public
    t0 = time.time(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    n = pypsa.Network(str(a.network))
    full = int(len(n.snapshots)); w0 = n.snapshot_weightings.copy()
    n.set_snapshots(n.snapshots[: a.snapshots])
    keep = bool((n.snapshot_weightings.values == w0.loc[n.snapshots].values).all())
    n.meta.update(solver_allowed=True, artifact_role="S4I_LP_STATS_UNSOLVED", s2_solve_label="S4I_LP_STATS")
    m = n.optimize.create_model(); install_research_constraint_hooks(n)
    res = dict(script="scripts_project/s4i_lp_ranges.py", network=str(a.network), network_sha256=sha(a.network), snapshots_full=full, snapshots_kept=int(len(n.snapshots)),
               weights_unchanged=keep, weight_hours=float(n.snapshot_weightings.objective.iloc[0]), research_constraints=sorted(k for k in m.constraints if k.startswith("research_") or k.startswith("Research")),
               build_seconds=time.time() - t0)
    res["before_scaling"] = ranges(m); res["before_groups"] = groups(m); res["before_objective_groups"] = objective_groups(m)
    const = remove_objective_constants(m)
    sel = select_stores(n, ["biomass_pools", "sequestration", "capture_buffers"]); allst = sorted({s for v in sel.values() for s in v})
    st = scale_store_energy(m, allst, 1000.0)
    kv = normalise_kvl_rows(m)
    res["scaling"] = dict(objective_constants=public(const) if isinstance(const, dict) else const, store_energy=public(st), kirchhoff=public(kv), stores_by_group={k: len(v) for k, v in sel.items()})
    res["after_scaling"] = ranges(m); res["after_groups"] = groups(m); res["after_objective_groups"] = objective_groups(m)
    res["seconds"] = time.time() - t0
    try:
        import resource
        res["peak_rss_gib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20
    except Exception:
        pass
    (out / f"C_LP_RANGES_{Path(a.network).stem}_{a.snapshots}.json").write_text(json.dumps(jsonable(res), indent=1, sort_keys=True, default=str))
    print(json.dumps(dict(seconds=round(res["seconds"], 1), peak_rss_gib=round(res.get("peak_rss_gib", 0), 2), before=res["before_scaling"], after=res["after_scaling"]), default=str))


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--network", required=True, type=Path); p.add_argument("--snapshots", type=int, default=56); p.add_argument("--out", required=True, type=Path)
    sys.exit(main(p.parse_args()))
