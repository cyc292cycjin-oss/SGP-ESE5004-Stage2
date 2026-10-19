"""L23 C9 (user supplement 2026-10-19): read-only primal-violation analysis of a non-optimal solve (no solver call, no parameter change).

For one solve output directory (lp/ arrays, solution/X.npy Pi.npy RC.npy, the solved network) and its unsolved network:
  * rebuild the same linopy model as s2_solve.py up to the LP export (create_model + research hooks + objective constants out; no solve) and check
    that its constraint / variable labels are exactly the exported ones;
  * row and column primal violations with the decision-71 budgets of s4b_acceptance (absolute floor 1e-3 + 1e-5 x reference, the same row /
    column references incl. the net-zero gross flows and the biomass pool capacities);
  * every violated row mapped to its constraint family, country and snapshot; by family and by country: counts, budget failures, maxima, the
    violation relative to the right-hand side, and the first-order cost sum(|violation| x |dual|) (INFERENCE: the objective change if the
    violations were repaired at the current marginal prices);
  * the last 20 barrier iterations from GUROBI_LOG_SCRUBBED.txt.

    python l23_violation_analysis.py --repo <code dir> --solve-dir <run output dir> --network <unsolved .nc> --scenario integrated --out <json>
           [--truncate 56] [--label FORMAL_TRIAL_365X24H]
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
COMP_TYPES = ("Bus", "Line", "Link", "Generator", "Store", "StorageUnit", "Load", "Transformer")


def gurobi_tail(path: Path, k: int = 20) -> dict:
    rows, summary = [], []
    pat = re.compile(r"^\s*(\d+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+(\d+)s\s*$")
    for line in path.read_text(errors="replace").splitlines():
        mm = pat.match(line)
        if mm:
            it, po, do, pr, dr, cg, t = mm.groups()
            rows.append(dict(iteration=int(it), primal_objective=float(po), dual_objective=float(do), primal_residual=float(pr), dual_residual=float(dr),
                             complementarity=float(cg), seconds=int(t)))
        elif re.search(r"Barrier performed|termination|Optimal objective|Sub-optimal|Time limit", line):
            summary.append(line.strip())
    return dict(last=rows[-k:], iterations=len(rows), summary=summary)


def build_model(repo: Path, network: Path, scenario: str, truncate: int | None, label: str):
    """The same model as s2_solve.py main() up to export_lp (no solve, no scaling of stores or Kirchhoff rows, which come after the export)."""
    sys.path.insert(0, str(repo / "scripts_project"))
    import pypsa
    from assembly_components import install_research_constraint_hooks
    from phase4_static import config
    from s2_solve import set_representative_weights
    n = pypsa.Network(str(network))
    if truncate:
        n.set_snapshots(n.snapshots[:truncate]); set_representative_weights(n)
    n.meta.update(solver_allowed=True, artifact_role=label + "_UNSOLVED", s2_solve_label=label)
    cfg = config(repo, scenario)
    tl = int((n.meta.get("research_transmission_losses") or {}).get("ac_transmission_losses", 0))
    m = n.optimize.create_model(transmission_losses=tl); install_research_constraint_hooks(n)
    SV = cfg["research"].get("solver", {})
    if SV.get("scaling", {}).get("objective_constants_out", True):
        from s3b_scaling import remove_objective_constants
        remove_objective_constants(m)
    return n, m, cfg


def decode(store, names_by_gid, gid, labels, idx):
    """For exported positions idx: (group name, {dim: coordinate}) via the linopy label arrays."""
    out = [None] * len(idx)
    by_g = pd.Series(range(len(idx))).groupby(gid[labels[idx]])
    for g, sel in by_g:
        if g < 0:
            continue
        name = names_by_gid[g]; lab = store[name].labels
        if lab.ndim == 0:   # single-row constraint (e.g. a country CO2 limit)
            for s in sel.values:
                out[s] = (name, {})
            continue
        flat = np.asarray(lab.values).ravel()
        pos = np.flatnonzero(flat >= 0); labs = flat[pos]; order = np.argsort(labs, kind="stable"); labs_s = labs[order]
        tgt = labels[idx[sel.values]]; k = np.searchsorted(labs_s, tgt); fp = pos[order[k]]
        ii = np.unravel_index(fp, lab.shape)
        for j, s in enumerate(sel.values):
            out[s] = (name, {d: str(lab.coords[d].values[ii[di][j]]) if d in lab.coords else int(ii[di][j]) for di, d in enumerate(lab.dims)})
    return out


def country_of(n, coords: dict, name: str) -> str:
    for d, v in coords.items():
        t = str(d).split("-")[0]
        if t not in COMP_TYPES:
            continue
        if t == "Bus" and v in n.buses.index:
            return str(n.buses.at[v, "country"])
        df = n.df(t)
        if v not in df.index:
            continue
        if t in ("Line", "Link", "Transformer"):
            a, b = str(n.buses.at[df.at[v, "bus0"], "country"]), str(n.buses.at[df.at[v, "bus1"], "country"])
            return a if a == b else "|".join(sorted((a, b)))
        if "bus" in df:
            return str(n.buses.at[df.at[v, "bus"], "country"])
    mm = re.search(r"-(%s)$" % "|".join(COUNTRIES), str(name))
    return mm.group(1) if mm else "-"


def main():
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--solve-dir", type=Path, required=True); ap.add_argument("--network", type=Path, required=True)
    ap.add_argument("--scenario", required=True); ap.add_argument("--out", type=Path, required=True); ap.add_argument("--truncate", type=int, default=None)
    ap.add_argument("--label", default="FORMAL_TRIAL_365X24H"); ap.add_argument("--top", type=int, default=5)
    a = ap.parse_args(); t0 = time.time()
    import scipy.sparse as sp
    sd = a.solve_dir; lp = sd / "lp"; meta = json.loads((lp / "MATH_PROBLEM.json").read_text())
    A_ = {k: np.load(lp / (k + ".npy")) for k in ["col_lower", "col_upper", "row_lower", "row_upper", "start", "index", "value", "clabels", "vlabels"]}
    x, pi = np.load(sd / "solution/X.npy"), np.load(sd / "solution/Pi.npy")
    nr, nc = meta["num_row"], meta["num_col"]
    A = sp.csc_matrix((A_["value"], A_["index"], A_["start"]), shape=(nr, nc))
    n, m, cfg = build_model(a.repo, a.network, a.scenario, a.truncate, a.label)
    sys.path.insert(0, str(a.repo / "scripts_project"))
    from s4b_acceptance import ABS_FLOOR, budgets, country_gross_co2_flows, label_groups, pool_capacities, special_references
    import pypsa
    solved = next(iter(sorted(sd.glob("*_solved.nc"))), None)
    ns = pypsa.Network(str(solved)) if solved else None
    rl, cl = A_["clabels"], A_["vlabels"]
    rgroup, cgroup = label_groups(m, rl, "row"), label_groups(m, cl, "col")
    n_valid_rows = int(sum(int((np.asarray(m.constraints[k].labels) >= 0).sum()) for k in m.constraints))
    check = dict(exported_rows=nr, model_rows=n_valid_rows, rows_without_group=int((rgroup == "?").sum()), columns_without_group=int((cgroup == "?").sum()))
    if check["rows_without_group"] or check["columns_without_group"]:
        raise SystemExit("label mismatch between the rebuilt model and the exported LP: " + json.dumps(check))
    gross = country_gross_co2_flows(ns) if ns is not None else {}; pools = pool_capacities(ns if ns is not None else n)
    row_ref, col_ref, _ = special_references(m, ns if ns is not None else n, rl, cl, gross, pools)
    interior = (cfg["research"].get("solver", {}) or {}).get("interior", {})
    B = budgets(interior, float(cfg["research"]["solver"]["profiles"]["formal_barrier"]["BarConvTol"]))
    act = A @ x; mag = abs(A) @ np.abs(x)
    lo, hi = A_["row_lower"], A_["row_upper"]; lf, uf = np.isfinite(lo), np.isfinite(hi)
    vlo = np.where(lf, lo - act, 0.0); vhi = np.where(uf, act - hi, 0.0)
    rv = np.maximum(np.maximum(vlo, vhi), 0.0); side_hi = vhi >= vlo; rhs = np.where(side_hi, hi, lo)
    rref = np.maximum.reduce([np.where(lf, np.abs(lo), 0.0), np.where(uf, np.abs(hi), 0.0), mag, row_ref])
    rtol = ABS_FLOOR + B["primal_relative"] * rref; ratio = rv / rtol
    cost = rv * np.abs(pi)
    clo, chi = A_["col_lower"], A_["col_upper"]; clf, cuf = np.isfinite(clo), np.isfinite(chi)
    cv = np.maximum(np.maximum(np.where(clf, clo - x, 0.0), np.where(cuf, x - chi, 0.0)), 0.0)
    cref = np.maximum.reduce([np.abs(x), np.where(clf, np.abs(clo), 0.0), np.where(cuf, np.abs(chi), 0.0), col_ref]); cratio = cv / (ABS_FLOOR + B["primal_relative"] * cref)
    viol_idx = np.flatnonzero(rv > 0)
    # decode every row with a violation above 1 % of its budget (country and snapshot), the rest only by family
    dec_idx = np.flatnonzero(ratio > 0.01)
    store = m.constraints; names = list(store); gid = np.full(int(rl.max()) + 1, -1, dtype=np.int64)
    for i, nm in enumerate(names):
        lab = np.asarray(store[nm].labels).ravel(); lab = lab[(lab >= 0) & (lab < len(gid))]; gid[lab] = i
    rows = []
    for (nm, co), i in zip(decode(store, names, gid, rl, dec_idx), dec_idx):
        snap = co.get("snapshot", "-")
        rows.append(dict(index=int(i), family=nm, country=country_of(n, co, nm), snapshot=snap, coords={k: v for k, v in co.items() if k != "snapshot"},
                         violation=float(rv[i]), rhs=float(rhs[i]), relative_to_rhs=(float(rv[i] / abs(rhs[i])) if rhs[i] != 0 else None),
                         relative_to_reference=float(rv[i] / rref[i]) if rref[i] > 0 else None, budget=float(rtol[i]), ratio_to_budget=float(ratio[i]),
                         dual=float(pi[i]), first_order_cost_eur=float(cost[i])))
    R = pd.DataFrame(rows)
    fam = {}
    G = pd.DataFrame(dict(family=rgroup[viol_idx], rv=rv[viol_idx], ratio=ratio[viol_idx], cost=cost[viol_idx]))
    for f, g in G.groupby("family"):
        top = R[R.family == f].sort_values("ratio_to_budget", ascending=False).head(a.top) if len(R) else pd.DataFrame()
        fam[str(f)] = dict(rows_in_family=int((rgroup == f).sum()), rows_violated=int(len(g)), rows_over_budget=int((g.ratio > 1).sum()),
                           max_violation=float(g.rv.max()), max_ratio_to_budget=float(g.ratio.max()), sum_violation=float(g.rv.sum()),
                           first_order_cost_eur=float(g.cost.sum()),
                           countries_over_budget=(R[(R.family == f) & (R.ratio_to_budget > 1)].country.value_counts().to_dict() if len(R) else {}),
                           top=top.to_dict(orient="records"),
                           top_by_violation=(R[R.family == f].sort_values("violation", ascending=False).head(3).to_dict(orient="records") if len(R) else []),
                           top_by_cost=(R[R.family == f].sort_values("first_order_cost_eur", ascending=False).head(3).to_dict(orient="records") if len(R) else []),
                           snapshots_over_budget=(R[(R.family == f) & (R.ratio_to_budget > 1)].snapshot.str[:10].value_counts().head(5).to_dict() if len(R) else {}))
    fam = dict(sorted(fam.items(), key=lambda kv: -kv[1]["max_ratio_to_budget"]))
    by_country = {}
    if len(R):
        for c, g in R.groupby("country"):
            by_country[str(c)] = dict(rows_decoded=int(len(g)), rows_over_budget=int((g.ratio_to_budget > 1).sum()), max_ratio_to_budget=float(g.ratio_to_budget.max()),
                                      first_order_cost_eur=float(g.first_order_cost_eur.sum()),
                                      families_over_budget=g[g.ratio_to_budget > 1].family.value_counts().to_dict())
    cfam = {}
    CV = pd.DataFrame(dict(family=cgroup[cv > 0], cv=cv[cv > 0], ratio=cratio[cv > 0]))
    for f, g in CV.groupby("family"):
        cfam[str(f)] = dict(columns_violated=int(len(g)), columns_over_budget=int((g.ratio > 1).sum()), max_violation=float(g.cv.max()), max_ratio_to_budget=float(g.ratio.max()))
    log = sd / "GUROBI_LOG_SCRUBBED.txt"
    receipt = json.loads((sd / "SOLVE_RECEIPT.json").read_text())
    res = dict(solve_dir=str(sd), network=str(a.network), termination=receipt.get("termination_condition"), objective=receipt.get("objective"),
               label_check=check, budgets=B, rows=nr, columns=nc,
               totals=dict(rows_violated=int(len(viol_idx)), rows_over_budget=int((ratio > 1).sum()), row_violation_max=float(rv.max(initial=0)),
                           row_max_ratio_to_budget=float(ratio.max(initial=0)), first_order_cost_eur=float(cost.sum()),
                           first_order_cost_over_budget_rows_eur=float(cost[ratio > 1].sum()),
                           columns_violated=int((cv > 0).sum()), columns_over_budget=int((cratio > 1).sum()), column_violation_max=float(cv.max(initial=0))),
               by_family=fam, by_country=by_country, column_families=dict(sorted(cfam.items(), key=lambda kv: -kv[1]["max_ratio_to_budget"])),
               gurobi=gurobi_tail(log) if log.exists() else None, seconds=time.time() - t0,
               note="first_order_cost = sum |violation| x |dual| (EUR): INFERENCE, the objective change if the violations were repaired at the current marginal prices")
    a.out.write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(dict(label_check=check, totals=res["totals"], families=[(k, v["rows_over_budget"], round(v["max_ratio_to_budget"], 2), round(v["first_order_cost_eur"]))
                                                                             for k, v in list(fam.items())[:15]], seconds=round(res["seconds"])), default=str))


if __name__ == "__main__":
    main()
