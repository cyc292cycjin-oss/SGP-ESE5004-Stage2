"""S4O-2 (decision 120): per-run precision evidence of decision 119 (C1) as a step of the run pipeline. READ ONLY - Python only, no solver call, the
solve results are not changed. Ported from the S4N pilot tool (research/06_scope_redesign/p1_step4n_20261019/scripts/s4n_c1_precision.py) with
(i) a replaceable reference for the per-country tolerance of (b) / (c), (ii) a re-grading step once the batch has its own reference, (iii) the
outputs registered in the run's EXPORTS.json and (iv) the run acceptance of decision 120 = Gurobi optimal + (a) + (b) + (c).

Uses the RETURNED solution (solution/X.npy, Pi.npy, RC.npy), the exported LP arrays (lp/), SOLVE_RECEIPT.json, V5_GATES.json, LEDGER_IDENTITY.json,
v5/kkt_summary.json, GUROBI_LOG_SCRUBBED.txt and the output of l23_violation_analysis.py (L23 report section 6 method; run it first):
  (a) total cost: primal / dual objective of the returned arrays (kkt_summary), absolute (bn EUR) and relative difference; standard <= 0.01 bn and
      <= 1e-5; the log line of the returned iterate, the best iteration before a first stall / restart and the restart are reported alongside.
  (b) primal violations: first-order cost sum |violation| x |dual| by country (cross-border rows "A|B" counted fully for both countries); standard
      per country <= max(1 % of the reference "disconnected - integrated" difference of that country, 0.01 bn); BN / SG / VN biomass-pool dominance.
  (c) prices: B16 ledger identity <= 1e-6; INFERENCE estimate of the KKT residuals' effect on the country settlements:
        stationarity  S_c = sum_{j in c} |(c_j - a_j' pi - rc_j) x_j|
        row compl.    R_c = sum_{i in c, inequality rows} |pi_i| x slack_i, slack_i = (a_i'x - l_i)+ for pi_i > 0, (u_i - a_i'x)+ for pi_i < 0
        column compl. K_c = sum_{j in c} |rc_j| x (x_j - l_j)+ for rc_j > 0, (u_j - x_j)+ for rc_j < 0; |rc_j x_j| where that bound is infinite
      standard per country S_c + R_c <= the same tolerance as (b); S + R + K (+ sign errors) reported as well.
  grade: (a)+(b) -> layer 1 (total cost) usable; (c) as well -> nodal-price settlements usable; otherwise price-settled results "provisional".
  The project solver-tolerance gates (V5_GATES.json) are reported as numerical information, not as a criterion (decision 120).

Reference of the tolerance: the batch's own "disconnected - integrated" ledger difference once both STEPS runs have results (`reference` +
`regrade`), before that the L23 365x24h difference (stated in the output).

    PYTHONHASHSEED=0 python s4o_c1_precision.py run --repo <code> --solve-dir <dir> --network <unsolved nc> --violations <json> [--reference <json>]
                                                [--scenario integrated] [--truncate N] [--label FORMAL_TRIAL_365X24H]
    python s4o_c1_precision.py reference --integrated <dir> --disconnected <dir> --out <json>
    python s4o_c1_precision.py regrade --solve-dir <dir> --reference <json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

L23_DIFF_BN = {"BN": 0.1143, "ID": 0.6693, "KH": 2.4261, "LA": 2.7403, "MM": 1.1328, "MY": 3.2101, "PH": 0.0099, "SG": 0.9319, "TH": 7.5101, "TL": 0.1237,
               "VN": 51.3202, "ASEAN": -1.2188}   # L23 365x24h, disconnected - integrated (L23_C9_SUMMARY.json ledger_difference.total_bn_eur); "ASEAN" = buses with country ASEAN (bunker account -1.2188, shared pool -0.0002)
L23_REFERENCE = dict(source="L23 365x24h ledger difference disconnected - integrated (research/06_scope_redesign/p1_l23_run1_20261019, L23_C9_SUMMARY.json "
                            "ledger_difference.total_bn_eur; SCREENING_UNVERIFIED runs, decision 112 a) - used until the batch has both STEPS runs", differences_bn=L23_DIFF_BN)
COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
ENTITIES = list(COUNTRIES) + ["ASEAN"]
COMP_TYPES = ("Bus", "Line", "Link", "Generator", "Store", "StorageUnit", "Load", "Transformer")
PAT = re.compile(r"^\s*(\d+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+(\d+)s\s*$")
STD = dict(a_abs_bn=0.01, a_rel=1e-5, country_pct=0.01, country_floor_bn=0.01, b16=1e-6)
OUT_FILES = ("PRECISION.json", "PRECISION.md")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def threshold_bn(c: str, ref: dict) -> float:
    return max(STD["country_pct"] * abs(float(ref["differences_bn"].get(c, 0.0) or 0.0)), STD["country_floor_bn"])


def parse_log(p: Path) -> list[dict]:
    rows = []
    if not p.exists():
        return rows
    for line in p.read_text(errors="replace").splitlines():
        mm = PAT.match(line)
        if mm:
            it, po, do, pr, dr, cg, t = mm.groups()
            rows.append(dict(iteration=int(it), primal_objective=float(po), dual_objective=float(do), primal_residual=float(pr), dual_residual=float(dr),
                             complementarity=float(cg), seconds=int(t)))
    return rows


def it_metrics(r: dict) -> dict:
    d = r["dual_objective"] - r["primal_objective"]
    return dict(r, difference_eur=d, difference_bn=d / 1e9, relative_difference=abs(d) / max(1.0, abs(r["primal_objective"])))


def log_section(log: list[dict], objective_lp) -> dict:
    """returned iterate (log line whose primal objective matches the receipt objective_lp), first restart, best iteration before it."""
    a_ = {}
    if not log:
        return a_
    P = np.array([r["primal_objective"] for r in log]); PR = np.array([r["primal_residual"] for r in log])
    olp = float(objective_lp) if objective_lp is not None else np.nan
    k_ret = int(np.argmin(np.abs(P - olp) / max(1.0, abs(olp)))) if np.isfinite(olp) else len(log) - 1
    k_rs = next((k for k in range(1, len(log)) if PR[k] > 1e6 * PR[:k].min()), None)   # restart: residual > 1e6 x the smallest one before
    first = log[: k_rs] if k_rs is not None else log
    k_best1 = int(np.argmin([r["primal_residual"] for r in first]))
    a_["log_iterations"] = len(log); a_["last_iteration"] = it_metrics(log[-1])
    a_["returned_iteration_by_log"] = dict(it_metrics(log[k_ret]), match_relative=float(abs(P[k_ret] - olp) / max(1.0, abs(olp))) if np.isfinite(olp) else None,
                                           tied_iterations=[int(log[k]["iteration"]) for k in np.flatnonzero(np.abs(P - P[k_ret]) == 0)])
    a_["restart"] = (dict(iteration=log[k_rs]["iteration"], seconds=log[k_rs]["seconds"], previous=log[k_rs - 1], at=log[k_rs]) if k_rs is not None else None)
    a_["best_before_first_stall"] = it_metrics(first[k_best1])
    a_["second_round_min_primal_residual"] = (it_metrics(min(log[k_rs:], key=lambda r: r["primal_residual"])) if k_rs is not None else None)
    return a_


def total_cost_check(kkt: dict, a_: dict) -> dict:
    """(a) on the returned arrays (kkt_summary: both objectives computed from X / Pi); the log line of the returned iterate as a fallback / cross-check."""
    a_["kkt_summary_returned_arrays"] = {k: kkt.get(k) for k in ("primal_objective", "dual_objective_numeric", "absolute_gap", "relative_gap", "complementarity_l1",
                                                                   "row_violation_max", "stationarity_max_original", "dual_sign_error_max_original", "source")}
    if kkt.get("primal_objective") is not None and kkt.get("dual_objective_numeric") is not None:
        diff = float(kkt["dual_objective_numeric"]) - float(kkt["primal_objective"])
        a_["returned_difference_eur"] = diff; a_["returned_difference_bn"] = diff / 1e9; a_["returned_relative"] = abs(diff) / max(1.0, abs(float(kkt["primal_objective"])))
        a_["basis"] = "v5/kkt_summary.json (returned arrays)"
    elif "returned_iteration_by_log" in a_:
        r = a_["returned_iteration_by_log"]; a_["returned_difference_eur"] = r["difference_eur"]; a_["returned_difference_bn"] = r["difference_bn"]; a_["returned_relative"] = r["relative_difference"]
        a_["basis"] = "Gurobi log line of the returned iterate"
    a_["passed"] = bool(abs(a_.get("returned_difference_bn", np.inf)) <= STD["a_abs_bn"] and a_.get("returned_relative", np.inf) <= STD["a_rel"])
    if "returned_iteration_by_log" in a_:
        r = a_["returned_iteration_by_log"]; a_["log_check_passed"] = bool(abs(r["difference_bn"]) <= STD["a_abs_bn"] and r["relative_difference"] <= STD["a_rel"])
    return a_


def kkt_terms(A, cost, x, pi, rc, lo, hi, cl, cu) -> dict:
    """per-column / per-row KKT residual terms of the returned solution (arrays in the exported LP order; formulas in the module docstring)."""
    lf, uf = np.isfinite(lo), np.isfinite(hi)
    act = A @ x
    resid = cost - A.T @ pi - rc
    S = np.abs(resid * x)
    eq = lf & uf & (lo == hi)
    slack = np.where(pi > 0, np.where(lf, np.maximum(act - lo, 0.0), np.nan), np.where(pi < 0, np.where(uf, np.maximum(hi - act, 0.0), np.nan), 0.0))
    row_sign_err = np.isnan(slack) & ~eq
    R = np.where(eq | np.isnan(slack), 0.0, np.abs(pi) * np.nan_to_num(slack))
    clf, cuf = np.isfinite(cl), np.isfinite(cu)
    cslack = np.where(rc > 0, np.where(clf, np.maximum(x - cl, 0.0), np.nan), np.where(rc < 0, np.where(cuf, np.maximum(cu - x, 0.0), np.nan), 0.0))
    col_sign = np.isnan(cslack)
    K = np.where(col_sign, 0.0, np.abs(rc) * np.nan_to_num(cslack)); KS = np.where(col_sign, np.abs(rc * x), 0.0)
    rv = np.maximum(np.maximum(np.where(lf, lo - act, 0.0), np.where(uf, act - hi, 0.0)), 0.0)
    return dict(act=act, S=S, R=R, K=K, KS=KS, row_violation=rv, row_sign_error_rows=int(row_sign_err.sum()))


def by_country(code_arr: np.ndarray, weights: np.ndarray, inv: dict) -> dict:
    s = np.bincount(code_arr, weights=weights, minlength=len(inv))
    return {inv[i]: float(s[i]) for i in range(len(inv)) if s[i] != 0}


def fold_cross_border(d: dict) -> dict:
    """country totals with every "A|B" entry counted fully for both A and B (conservative)."""
    out = {}
    for k, v in d.items():
        for c in str(k).split("|"):
            out[c] = out.get(c, 0.0) + v
    return out


def country_lookup(store, labels_exported: np.ndarray, maps: dict, codes: dict) -> np.ndarray:
    """country code per exported row / column (vectorised over the linopy label arrays)."""
    top = int(labels_exported.max()) + 1
    look = np.full(top, codes.setdefault("-", len(codes)), dtype=np.int32)
    for name in store:
        lab = store[name].labels; arr = np.asarray(lab.values)
        if arr.ndim == 0:
            mm = re.search(r"-(%s)$" % "|".join(COUNTRIES), str(name)); c = mm.group(1) if mm else "-"
            if 0 <= int(arr) < top:
                look[int(arr)] = codes.setdefault(c, len(codes))
            continue
        dims = list(lab.dims); comp = [d for d in dims if str(d).split("-")[0] in COMP_TYPES]
        if comp:
            d = comp[0]; t = str(d).split("-")[0]
            vals = pd.Index(map(str, lab.coords[d].values)) if d in lab.coords else pd.Index([])
            cv = maps[t].reindex(vals).fillna("-").to_numpy()
            vec = np.array([codes.setdefault(str(c), len(codes)) for c in cv], dtype=np.int32)
            shape = [1] * arr.ndim; shape[dims.index(d)] = len(vec)
            full = np.broadcast_to(vec.reshape(shape), arr.shape)
        else:
            mm = re.search(r"-(%s)$" % "|".join(COUNTRIES), str(name)); c = mm.group(1) if mm else "-"
            full = np.full(arr.shape, codes.setdefault(c, len(codes)), dtype=np.int32)
        flat = arr.ravel(); fc = full.ravel(); ok = (flat >= 0) & (flat < top)
        look[flat[ok]] = fc[ok]
    return look[labels_exported]


def gates_info(gates: dict) -> dict:
    """project solver-tolerance gates: numerical information only (decision 120)."""
    failing = sorted(k for k, v in gates.items() if isinstance(v, dict) and v.get("passed") is False)
    return dict(all_passed_solver_tolerances=gates.get("all_passed_solver_tolerances"), all_passed_barconvtol=gates.get("all_passed_barconvtol"),
                failing=failing, failing_excl_B12=[k for k in failing if k != "B12"],
                note="reported as numerical information, not as a go / no-go criterion (decision 120); B12 fails by construction for networks built before a config change")


def apply_reference(res: dict, ref: dict) -> dict:
    """(re)compute the per-country thresholds of (b) and (c), the grade and the acceptance from the stored per-country values."""
    res["reference"] = dict(source=ref["source"], differences_bn=ref["differences_bn"])
    b_, c_ = res.get("b_primal_violations"), res.get("c_prices")
    if b_ is not None:
        for c, v in b_["country_check"].items():
            v["threshold_bn"] = threshold_bn(c, ref); v["passed"] = bool(v["first_order_cost_bn"] <= v["threshold_bn"])
        b_["passed"] = bool(all(v["passed"] for v in b_["country_check"].values()))
    if c_ is not None:
        for c, v in c_["country_check"].items():
            v["threshold_bn"] = threshold_bn(c, ref); v["passed"] = bool(v["S_plus_R_bn"] <= v["threshold_bn"]); v["passed_all_terms"] = bool(v["all_terms_bn"] <= v["threshold_bn"])
        c_["passed_kkt"] = bool(all(v["passed"] for v in c_["country_check"].values())); c_["passed_kkt_all_terms"] = bool(all(v["passed_all_terms"] for v in c_["country_check"].values()))
        c_["passed"] = bool(c_["b16"]["passed"] and c_["passed_kkt"])
    a_ok = bool((res.get("a_total_cost") or {}).get("passed")); b_ok = bool(b_ and b_["passed"]); c_ok = bool(c_ and c_["passed"])
    grade = "layer1_total_cost_screening" if (a_ok and b_ok) else "not_layer1"
    if grade == "layer1_total_cost_screening" and c_ok:
        grade = "layer1_plus_nodal_price_settlement"
    res["grade"] = dict(grade=grade, a=a_ok, b=b_ok, c=c_ok, price_settled_results=("usable" if (a_ok and b_ok and c_ok) else "provisional"))
    optimal = res.get("termination") == "optimal"
    res["acceptance"] = dict(optimal=optimal, a=a_ok, b=b_ok, c=c_ok, accepted=bool(optimal and a_ok and b_ok and c_ok),
                             rule="decision 120: run accepted = Gurobi optimal + decision 119 (a)(b)(c); project gates are numerical information")
    return res


def update_exports(sd: Path, names=OUT_FILES + ("VIOLATIONS.json",)) -> dict:
    """add the precision outputs (bytes, SHA256) to the run's EXPORTS.json (created when absent)."""
    p = sd / "EXPORTS.json"
    ex = json.loads(p.read_text()) if p.exists() else {}
    for f in names:
        if (sd / f).exists():
            ex[f] = dict(bytes=(sd / f).stat().st_size, sha256=sha(sd / f), source="s4o_c1_precision.py (decision 120 pipeline step)")
    p.write_text(json.dumps(ex, indent=1))
    return ex


def compute(repo: Path, sd: Path, network: Path, violations: Path, ref: dict, scenario: str, truncate, label: str) -> dict:
    t0 = time.time()
    rec = json.loads((sd / "SOLVE_RECEIPT.json").read_text()) if (sd / "SOLVE_RECEIPT.json").exists() else {}
    res = dict(solve_dir=str(sd), scenario=scenario, label=label, termination=rec.get("termination_condition"), objective=rec.get("objective"),
               objective_lp=rec.get("objective_lp"), solver_profile=rec.get("solver_profile"), solver_parameters=rec.get("solver_parameters"),
               method_note="returned solution = solution/X.npy, Pi.npy, RC.npy (what Gurobi returned); no solver call; the solve results are unchanged")
    need = [sd / "solution" / "X.npy", sd / "solution" / "Pi.npy", sd / "solution" / "RC.npy", sd / "lp" / "MATH_PROBLEM.json", violations]
    missing = [str(p) for p in need if not p.exists()]
    if missing:
        res.update(computable=False, missing=missing, grade=dict(grade="not_computable", a=False, b=False, c=False, price_settled_results="provisional"),
                   acceptance=dict(optimal=res["termination"] == "optimal", a=False, b=False, c=False, accepted=False, rule="no returned solution / LP arrays"),
                   reference=dict(source=ref["source"], differences_bn=ref["differences_bn"]))
        res["gates_information"] = gates_info(json.loads((sd / "V5_GATES.json").read_text())) if (sd / "V5_GATES.json").exists() else None
        return res
    res["computable"] = True
    sys.path.insert(0, str(repo / "scripts_project"))
    import scipy.sparse as sp
    from l23_violation_analysis import build_model, decode
    from s4b_acceptance import ABS_FLOOR, budgets, country_gross_co2_flows, pool_capacities, special_references
    import pypsa
    gates = json.loads((sd / "V5_GATES.json").read_text()) if (sd / "V5_GATES.json").exists() else {}
    kkt = json.loads((sd / "v5" / "kkt_summary.json").read_text()) if (sd / "v5" / "kkt_summary.json").exists() else {}
    led = json.loads((sd / "LEDGER_IDENTITY.json").read_text()) if (sd / "LEDGER_IDENTITY.json").exists() else {}
    V = json.loads(violations.read_text())
    # ---------------- (a)
    res["a_total_cost"] = total_cost_check(kkt, log_section(parse_log(sd / "GUROBI_LOG_SCRUBBED.txt"), rec.get("objective_lp")))
    # ---------------- arrays, model, country maps
    lp = sd / "lp"; meta = json.loads((lp / "MATH_PROBLEM.json").read_text())
    Z = {k: np.load(lp / (k + ".npy")) for k in ["cost", "col_lower", "col_upper", "row_lower", "row_upper", "start", "index", "value", "clabels", "vlabels"]}
    x, pi, rc = [np.load(sd / "solution" / (k + ".npy")) for k in ("X", "Pi", "RC")]
    A = sp.csc_matrix((Z["value"], Z["index"], Z["start"]), shape=(meta["num_row"], meta["num_col"]))
    n, m, cfg = build_model(repo, network, scenario, truncate, label)
    solved = next(iter(sorted(sd.glob("*_solved.nc"))), None); ns = pypsa.Network(str(solved)) if solved else None
    bus_c = n.buses.country.astype(str); maps = {"Bus": bus_c}
    for t in ("Generator", "Load", "Store", "StorageUnit"):
        df = n.df(t); maps[t] = df.bus.map(bus_c).fillna("-").astype(str) if len(df) else pd.Series(dtype=str)
    for t in ("Line", "Link", "Transformer"):
        df = n.df(t)
        if len(df):
            b0 = df.bus0.map(bus_c).fillna("-").astype(str).to_numpy(); b1 = df.bus1.map(bus_c).fillna("-").astype(str).to_numpy()
            maps[t] = pd.Series([u if u == v else "|".join(sorted((u, v))) for u, v in zip(b0, b1)], index=df.index)
        else:
            maps[t] = pd.Series(dtype=str)
    codes: dict = {}
    rcode = country_lookup(m.constraints, Z["clabels"], maps, codes); ccode = country_lookup(m.variables, Z["vlabels"], maps, codes)
    inv = {v: k for k, v in codes.items()}
    T = kkt_terms(A, Z["cost"], x, pi, rc, Z["row_lower"], Z["row_upper"], Z["col_lower"], Z["col_upper"])
    # ---------------- (b) (same formulas as l23_violation_analysis.py; consistency check against its totals)
    gross = country_gross_co2_flows(ns) if ns is not None else {}; pools = pool_capacities(ns if ns is not None else n)
    row_ref, _, _ = special_references(m, ns if ns is not None else n, Z["clabels"], Z["vlabels"], gross, pools)
    B = budgets((cfg["research"].get("solver", {}) or {}).get("interior", {}), float(cfg["research"]["solver"]["profiles"]["formal_barrier"]["BarConvTol"]))
    lo, hi = Z["row_lower"], Z["row_upper"]; lf, uf = np.isfinite(lo), np.isfinite(hi); rv = T["row_violation"]
    rref = np.maximum.reduce([np.where(lf, np.abs(lo), 0.0), np.where(uf, np.abs(hi), 0.0), abs(A) @ np.abs(x), row_ref]); ratio = rv / (ABS_FLOOR + B["primal_relative"] * rref)
    foc = rv * np.abs(pi)
    b_ = dict(rows_violated=int((rv > 0).sum()), rows_over_budget=int((ratio > 1).sum()), row_violation_max=float(rv.max(initial=0)), row_max_ratio=float(ratio.max(initial=0)),
              first_order_cost_eur_all_rows=float(foc.sum()),
              budget_note="rows over budget: decision-71 budgets with profile A's BarConvTol as in the L23 section 6 method (count only, not a criterion)",
              consistency_with_l23_script=dict(rows_over_budget=V["totals"]["rows_over_budget"], first_order_cost_eur=V["totals"]["first_order_cost_eur"],
                                               equal=bool(V["totals"]["rows_over_budget"] == int((ratio > 1).sum()))))
    foc_c = by_country(rcode, foc, inv); b_["first_order_cost_eur_by_country_all_rows"] = foc_c
    folded = fold_cross_border(foc_c)
    b_["country_check"] = {c: dict(first_order_cost_bn=folded.get(c, 0.0) / 1e9) for c in ENTITIES}
    b_["unattributed_eur"] = folded.get("-", 0.0)
    b_["families_top"] = [dict(family=k, rows_over_budget=v["rows_over_budget"], max_violation=v["max_violation"], max_ratio_to_budget=v["max_ratio_to_budget"],
                               first_order_cost_eur=v["first_order_cost_eur"], countries_over_budget=v.get("countries_over_budget"),
                               top_row=(v["top"][0] if v.get("top") else None)) for k, v in list(V["by_family"].items())[:12]]
    pool_names = set(pools); over = np.flatnonzero(ratio > 1)
    store = m.constraints; names = list(store); gid = np.full(int(Z["clabels"].max()) + 1, -1, dtype=np.int64)
    for i, nm in enumerate(names):
        lab = np.asarray(store[nm].labels).ravel(); lab = lab[(lab >= 0) & (lab < len(gid))]; gid[lab] = i
    dec = decode(store, names, gid, Z["clabels"], over) if len(over) else []
    is_pool = np.array([any(str(v) in pool_names for k, v in co.items() if str(k).startswith("Store")) for (nm, co) in dec], dtype=bool) if len(dec) else np.zeros(0, bool)
    ctry = np.array([inv[int(c)] for c in rcode[over]]) if len(over) else np.array([])
    bsv = is_pool & np.isin(ctry, ["BN", "SG", "VN"]) if len(over) else np.zeros(0, bool)
    order = np.argsort(-ratio[over]) if len(over) else np.array([], int)
    top10 = [dict(family=dec[k][0], country=str(ctry[k]), coords={kk: vv for kk, vv in dec[k][1].items()}, violation=float(rv[over[k]]), ratio_to_budget=float(ratio[over[k]]),
                  biomass_pool=bool(is_pool[k])) for k in order[:10]]
    b_["biomass_pools_BN_SG_VN"] = dict(rows_over_budget_total=int(len(over)), rows_over_budget_on_BN_SG_VN_pools=int(bsv.sum()),
                                        share_of_rows_over_budget=(float(bsv.mean()) if len(over) else 0.0),
                                        rows_over_budget_on_any_pool=int(is_pool.sum()) if len(over) else 0,
                                        max_ratio_row_is_BN_SG_VN_pool=(bool(bsv[order[0]]) if len(over) else False),
                                        top10_rows_on_BN_SG_VN_pools=int(sum(bsv[k] for k in order[:10])) if len(over) else 0,
                                        first_order_cost_share_of_BN_SG_VN_pool_rows=(float(foc[over][bsv].sum() / max(foc[over].sum(), 1e-300)) if len(over) else 0.0),
                                        dominant=bool(len(over) and (bsv[order[0]] and bsv.mean() >= 0.5)),
                                        dominance_rule="dominant = the largest-ratio row is a BN / SG / VN pool row AND >= 50 % of the over-budget rows are such rows",
                                        top10=top10)
    res["b_primal_violations"] = b_
    # ---------------- (c)
    b16 = gates.get("B16_LEDGER", {})
    c_ = dict(b16=dict(relative_error=b16.get("relative_error"), tolerance=b16.get("tolerance"), passed_gate=b16.get("passed"),
                       ledger_identity=(led.get("identity") or {}).get("relative_error"),
                       passed=bool(b16.get("relative_error") is not None and float(b16["relative_error"]) <= STD["b16"])))
    Sc, Rc, Kc, KSc = (by_country(code, w, inv) for code, w in ((ccode, T["S"]), (rcode, T["R"]), (ccode, T["K"]), (ccode, T["KS"])))
    fS, fR, fK, fKS = (fold_cross_border(d) for d in (Sc, Rc, Kc, KSc))
    c_["formulas"] = dict(stationarity="S_c = sum_j |(c_j - a_j' pi - rc_j) x_j|", row_complementarity="R_c = sum_i |pi_i| (slack on the multiplier's bound)+, inequality rows",
                          column_complementarity="K_c = sum_j |rc_j| (x_j - bound)+; free-column dual-sign error |rc_j x_j| separately (KS_c)",
                          attribution="rows / columns by the component's bus country; cross-border components counted fully for both countries",
                          label="INFERENCE: first-order estimate of the effect of the KKT residuals on country settlements (EUR)")
    c_["totals_eur"] = dict(stationarity=float(T["S"].sum()), row_complementarity=float(T["R"].sum()), column_complementarity=float(T["K"].sum()),
                            column_dual_sign_error=float(T["KS"].sum()), row_dual_sign_rows=T["row_sign_error_rows"])
    c_["by_country_raw_eur"] = dict(stationarity=Sc, row_complementarity=Rc, column_complementarity=Kc, column_dual_sign_error=KSc)
    c_["country_check"] = {c: dict(stationarity_bn=fS.get(c, 0.0) / 1e9, row_complementarity_bn=fR.get(c, 0.0) / 1e9, S_plus_R_bn=(fS.get(c, 0.0) + fR.get(c, 0.0)) / 1e9,
                                   column_complementarity_bn=fK.get(c, 0.0) / 1e9, column_dual_sign_bn=fKS.get(c, 0.0) / 1e9,
                                   all_terms_bn=(fS.get(c, 0.0) + fR.get(c, 0.0) + fK.get(c, 0.0) + fKS.get(c, 0.0)) / 1e9) for c in ENTITIES}
    c_["unattributed_eur"] = dict(stationarity=fS.get("-", 0.0), row_complementarity=fR.get("-", 0.0), column_complementarity=fK.get("-", 0.0), column_dual_sign_error=fKS.get("-", 0.0))
    res["c_prices"] = c_
    res["gates_information"] = gates_info(gates)
    apply_reference(res, ref)
    res["seconds"] = time.time() - t0
    return res


def markdown(res: dict) -> str:
    g = res["grade"]; ac = res["acceptance"]; ref = res.get("reference") or {}
    L = [f"# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）", "",
         f"- 运行：`{res['solve_dir']}`（{res.get('scenario')}，{res.get('label')}，档案 {res.get('solver_profile')}）；终止 `{res.get('termination')}`；目标 {res.get('objective')}；基于**最终返回解**（solution/X、Pi、RC）。",
         f"- **验收（第 120 项 = optimal + (a)(b)(c)）：{ac['accepted']}**（optimal {ac['optimal']}，(a) {ac['a']}，(b) {ac['b']}，(c) {ac['c']}）",
         f"- 分级：**{g['grade']}**（按电价结算：{g['price_settled_results']}）",
         f"- 分国容差参照：{ref.get('source')}"]
    if res.get("grade_history"):
        L.append(f"- 重评记录：" + "；".join(f"{h['reference_source'][:60]}… → {h['grade']}（验收 {h['accepted']}）" for h in res["grade_history"]))
    gi = res.get("gates_information") or {}
    L += [f"- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` {gi.get('all_passed_solver_tolerances')}；不通过 {', '.join(gi.get('failing') or []) or '无'}", ""]
    if not res.get("computable", True):
        L += ["无法计算：缺少 " + "、".join(res.get("missing", [])), ""]
        return "\n".join(L) + "\n"
    a_ = res["a_total_cost"]
    L += ["## (a) 总成本精度", ""]
    for key, title in (("best_before_first_stall", "第一轮停滞前最好迭代（原始残差最小）"), ("returned_iteration_by_log", "最终返回解（日志中与回执 objective_lp 相同的迭代）"),
                       ("last_iteration", "最后一次迭代"), ("second_round_min_primal_residual", "重启后原始残差最小的迭代")):
        r = a_.get(key)
        if r:
            L.append(f"- {title}：第 {r['iteration']} 次，原始 {r['primal_objective']:.9e}，对偶 {r['dual_objective']:.9e}，差 {r['difference_eur']:.4g} EUR（相对 {r['relative_difference']:.2e}），"
                     f"原始残差 {r['primal_residual']:.3g}，对偶残差 {r['dual_residual']:.3g}，互补 {r['complementarity']:.3g}，{r['seconds']} s")
    if a_.get("restart"):
        L.append(f"- 重启：第 {a_['restart']['iteration']} 次（{a_['restart']['seconds']} s）")
    k = a_["kkt_summary_returned_arrays"]
    L += [f"- 返回数组的 KKT 摘要：原始 {k.get('primal_objective')}，对偶 {k.get('dual_objective_numeric')}，差 {a_.get('returned_difference_bn', float('nan')):.6f} bn，相对 {a_.get('returned_relative', float('nan')):.2e} → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**{a_['passed']}**", ""]
    b_ = res["b_primal_violations"]
    L += ["## (b) 原始违反（L23 §6 方法）", "",
          f"- 有正违反的行 {b_['rows_violated']:,}，超预算 {b_['rows_over_budget']:,}（与 `l23_violation_analysis.py` 一致：{b_['consistency_with_l23_script']['equal']}），最大违反 {b_['row_violation_max']:.4g}，最大为预算 {b_['row_max_ratio']:.4g} 倍；一阶影响合计 {b_['first_order_cost_eur_all_rows']:,.0f} EUR", "",
          "| 国 | 一阶影响 bn | 阈值 bn | 通过 |", "|---|---|---|---|"]
    L += [f"| {c} | {v['first_order_cost_bn']:.2e} | {v['threshold_bn']:.4f} | {v['passed']} |" for c, v in b_["country_check"].items()]
    bp = b_["biomass_pools_BN_SG_VN"]
    L += ["", f"- BN / SG / VN 生物质池行：超预算行中 {bp['rows_over_budget_on_BN_SG_VN_pools']} / {bp['rows_over_budget_total']}；最大倍数的行{'是' if bp['max_ratio_row_is_BN_SG_VN_pool'] else '不是'}此类行；仍占主导：**{bp['dominant']}**", ""]
    c_ = res["c_prices"]
    L += ["## (c) 价格质量", "", f"- B16 账本恒等式：相对误差 {c_['b16']['relative_error']}（≤ 1e-6）→ **{c_['b16']['passed']}**",
          f"- KKT 残差对分国结算的影响（INFERENCE；{c_['formulas']['attribution']}）：", "",
          "| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |", "|---|---|---|---|---|---|---|---|---|"]
    L += [f"| {c} | {v['stationarity_bn']:.2e} | {v['row_complementarity_bn']:.2e} | {v['S_plus_R_bn']:.2e} | {v['column_complementarity_bn']:.2e} | {v['column_dual_sign_bn']:.2e} | {v['threshold_bn']:.4f} | {v['passed']} | {v['passed_all_terms']} |"
          for c, v in c_["country_check"].items()]
    L += ["", f"- (c) 判定（B16 且每国 S+R ≤ 阈值）：**{c_['passed']}**（全部项：{c_['passed_kkt_all_terms']}）", "", f"用时 {res.get('seconds', 0):.0f} s。"]
    return "\n".join(L) + "\n"


def write(sd: Path, res: dict) -> None:
    (sd / "PRECISION.json").write_text(json.dumps(res, indent=1, default=str))
    (sd / "PRECISION.md").write_text(markdown(res))
    update_exports(sd)


def reference_from_ledgers(integrated: Path, disconnected: Path) -> dict:
    """the batch's own "disconnected - integrated" difference by country (bn EUR) from the two COUNTRY_COST_LEDGER.csv; ASEAN = ASEAN_* entities."""
    li = pd.read_csv(integrated / "COUNTRY_COST_LEDGER.csv", index_col=0)["total"]; ld = pd.read_csv(disconnected / "COUNTRY_COST_LEDGER.csv", index_col=0)["total"]
    d = (ld.reindex(li.index.union(ld.index)).fillna(0.0) - li.reindex(li.index.union(ld.index)).fillna(0.0)) / 1e9
    diffs = {c: float(d.get(c, 0.0)) for c in COUNTRIES}
    diffs["ASEAN"] = float(d[[k for k in d.index if str(k).startswith("ASEAN")]].sum())
    return dict(source=f"this batch: disconnected - integrated ledger difference ({disconnected} minus {integrated}, COUNTRY_COST_LEDGER.csv total)", differences_bn=diffs)


def regrade(sd: Path, ref: dict) -> dict:
    res = json.loads((sd / "PRECISION.json").read_text())
    if res.get("computable", True):
        hist = res.setdefault("grade_history", [])
        hist.append(dict(reference_source=(res.get("reference") or {}).get("source") or res.get("l23_reference_note"), grade=(res.get("grade") or {}).get("grade"),
                         accepted=(res.get("acceptance") or {}).get("accepted")))   # S4O supplement 01: also the S4N pilot's PILOT_PRECISION.json (no acceptance / reference keys)
        apply_reference(res, ref)
    else:
        res["reference"] = dict(source=ref["source"], differences_bn=ref["differences_bn"])
    write(sd, res)
    return res


def main():
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--repo", type=Path, required=True); r.add_argument("--solve-dir", type=Path, required=True); r.add_argument("--network", type=Path, required=True)
    r.add_argument("--violations", type=Path, required=True); r.add_argument("--reference", type=Path, default=None); r.add_argument("--scenario", default="integrated")
    r.add_argument("--truncate", type=int, default=None); r.add_argument("--label", default="FORMAL_TRIAL_365X24H")
    f = sub.add_parser("reference"); f.add_argument("--integrated", type=Path, required=True); f.add_argument("--disconnected", type=Path, required=True); f.add_argument("--out", type=Path, required=True)
    g = sub.add_parser("regrade"); g.add_argument("--solve-dir", type=Path, required=True); g.add_argument("--reference", type=Path, required=True)
    a = ap.parse_args()
    if a.cmd == "run":
        ref = json.loads(a.reference.read_text()) if a.reference else L23_REFERENCE
        res = compute(a.repo, a.solve_dir, a.network, a.violations, ref, a.scenario, a.truncate, a.label); write(a.solve_dir, res)
    elif a.cmd == "reference":
        res = reference_from_ledgers(a.integrated, a.disconnected); a.out.write_text(json.dumps(res, indent=1))
        print(json.dumps(res)); return
    else:
        res = regrade(a.solve_dir, json.loads(a.reference.read_text()))
    print(json.dumps(dict(grade=res["grade"], acceptance=res["acceptance"], reference=(res.get("reference") or {}).get("source", "")[:80], seconds=round(res.get("seconds", 0))), default=str))


if __name__ == "__main__":
    main()
