"""S4N supplement 02 C1 (decision 119): precision evidence of the pilot solve (READ ONLY; Python only, no solver call, the pilot results are not changed).

Uses the RETURNED solution (solution/X.npy, Pi.npy, RC.npy = what Gurobi returned), the exported LP arrays (lp/), the receipt, V5_GATES.json,
LEDGER_IDENTITY.json, v5/kkt_summary.json, the scrubbed Gurobi log and the output of l23_violation_analysis.py (L23 report section 6 method).

  (a) total cost: final primal / dual objective of the returned solution (log line matching the receipt objective_lp; kkt_summary computed from the
      returned arrays); absolute (bn EUR) and relative difference; standard |diff| <= 0.01 bn and relative <= 1e-5. The best iteration before the
      first stall / restart is reported alongside (log values only).
  (b) primal violations: families, magnitudes, first-order cost sum|violation| x |dual| by country (rows decoded by l23_violation_analysis.py;
      cross-border rows "A|B" are counted fully for both countries); standard per country <= max(1 % of the country's disconnected - integrated
      difference, 0.01 bn); the pilot has only the integrated run, so the L23 365x24h differences are the reference (stated). Whether BN / SG / VN
      biomass-pool rows still dominate (decision 118 point 1).
  (c) prices: (1) B16 ledger identity with the pilot nodal prices (relative error <= 1e-6); (2) INFERENCE estimates of the price error on the
      country settlements from the KKT residuals of the returned solution, by country:
        stationarity  S_c = sum_{j in c} |(c_j - a_j' pi - rc_j) x_j|
        row compl.    R_c = sum_{i in c, inequality rows} |pi_i| x slack_i, slack_i = (a_i'x - l_i)+ for pi_i > 0, (u_i - a_i'x)+ for pi_i < 0
        column compl. K_c = sum_{j in c} |rc_j| x (x_j - l_j)+ for rc_j > 0, (u_j - x_j)+ for rc_j < 0; |rc_j x_j| where that bound is infinite
                      (dual-sign error of free columns), reported separately
      standard per country S_c + R_c <= max(1 %, 0.01 bn) (as written in the supplement); S_c + R_c + K_c is reported as well.
  grading: (a)+(b) pass -> layer 1 (total cost only) usable as 365x24h screening result; (c) also passes -> nodal-price settlement usable;
           otherwise price-settled results are "provisional".

    PYTHONHASHSEED=0 python s4n_c1_precision.py --repo <code> --solve-dir <run>/integrated --network <unsolved nc> --violations <json> --out-json <json> --out-md <md>
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

L23_DIFF_BN = {"BN": 0.1143, "ID": 0.6693, "KH": 2.4261, "LA": 2.7403, "MM": 1.1328, "MY": 3.2101, "PH": 0.0099, "SG": 0.9319, "TH": 7.5101, "TL": 0.1237,
               "VN": 51.3202, "ASEAN": -1.2188}   # L23 365x24h, disconnected - integrated (L23_C9_SUMMARY.json ledger_difference.total_bn_eur); "ASEAN" = buses with country ASEAN (bunker account -1.2188, shared pool -0.0002)
COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
COMP_TYPES = ("Bus", "Line", "Link", "Generator", "Store", "StorageUnit", "Load", "Transformer")
PAT = re.compile(r"^\s*(\d+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+(\d+)s\s*$")


def threshold_bn(c: str) -> float:
    return max(0.01 * abs(L23_DIFF_BN.get(c, 0.0)), 0.01)


def parse_log(p: Path) -> list[dict]:
    rows = []
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


def country_lookup(store, labels_exported: np.ndarray, n, maps: dict, codes: dict) -> np.ndarray:
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


def main():
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--solve-dir", type=Path, required=True); ap.add_argument("--network", type=Path, required=True)
    ap.add_argument("--violations", type=Path, required=True); ap.add_argument("--out-json", type=Path, required=True); ap.add_argument("--out-md", type=Path, required=True)
    ap.add_argument("--scenario", default="integrated"); ap.add_argument("--truncate", type=int, default=None); ap.add_argument("--label", default="FORMAL_TRIAL_365X24H")
    a = ap.parse_args(); t0 = time.time(); sd = a.solve_dir
    sys.path.insert(0, str(a.repo / "scripts_project"))
    import scipy.sparse as sp
    from l23_violation_analysis import build_model, decode
    from s4b_acceptance import ABS_FLOOR, budgets, country_gross_co2_flows, pool_capacities, special_references
    import pypsa
    rec = json.loads((sd / "SOLVE_RECEIPT.json").read_text()); gates = json.loads((sd / "V5_GATES.json").read_text())
    kkt = json.loads((sd / "v5" / "kkt_summary.json").read_text()) if (sd / "v5" / "kkt_summary.json").exists() else {}
    led = json.loads((sd / "LEDGER_IDENTITY.json").read_text()) if (sd / "LEDGER_IDENTITY.json").exists() else {}
    V = json.loads(a.violations.read_text())
    res = dict(solve_dir=str(sd), termination=rec.get("termination_condition"), objective=rec.get("objective"), objective_lp=rec.get("objective_lp"),
               method_note="returned solution = solution/X.npy, Pi.npy, RC.npy (what Gurobi returned); no solver call; pilot results unchanged",
               l23_reference_note="the pilot has only the integrated run: per-country thresholds use the L23 365x24h disconnected - integrated differences (bn EUR)",
               l23_differences_bn=L23_DIFF_BN)
    # ---------------- (a)
    log = parse_log(sd / "GUROBI_LOG_SCRUBBED.txt")
    a_ = {}
    if log:
        P = np.array([r["primal_objective"] for r in log]); PR = np.array([r["primal_residual"] for r in log])
        olp = float(rec.get("objective_lp") or np.nan)
        k_ret = int(np.argmin(np.abs(P - olp) / max(1.0, abs(olp)))) if np.isfinite(olp) else len(log) - 1
        # first restart: an iteration whose primal residual exceeds 1e6 x the smallest residual seen before it
        k_rs = next((k for k in range(1, len(log)) if PR[k] > 1e6 * PR[:k].min()), None)
        first = log[: k_rs] if k_rs is not None else log
        k_best1 = int(np.argmin([r["primal_residual"] for r in first]))
        a_["log_iterations"] = len(log); a_["last_iteration"] = it_metrics(log[-1])
        a_["returned_iteration_by_log"] = dict(it_metrics(log[k_ret]), match_relative=float(abs(P[k_ret] - olp) / max(1.0, abs(olp))), tied_iterations=[int(log[k]["iteration"]) for k in np.flatnonzero(np.abs(P - P[k_ret]) == 0)])
        a_["restart"] = (dict(iteration=log[k_rs]["iteration"], seconds=log[k_rs]["seconds"], previous=log[k_rs - 1], at=log[k_rs]) if k_rs is not None else None)
        a_["best_before_first_stall"] = it_metrics(first[k_best1])
        a_["second_round_min_primal_residual"] = (it_metrics(min(log[k_rs:], key=lambda r: r["primal_residual"])) if k_rs is not None else None)
    a_["kkt_summary_returned_arrays"] = {k: kkt.get(k) for k in ("primal_objective", "dual_objective_numeric", "absolute_gap", "relative_gap", "complementarity_l1",
                                                                   "row_violation_max", "stationarity_max_original", "dual_sign_error_max_original", "source")}
    # criterion on the returned solution: the KKT summary of the returned arrays (both sides computed from the arrays); the log line of the returned
    # iterate as a cross-check
    if kkt.get("primal_objective") is not None and kkt.get("dual_objective_numeric") is not None:
        diff = float(kkt["dual_objective_numeric"]) - float(kkt["primal_objective"])
        a_["returned_difference_eur"] = diff; a_["returned_difference_bn"] = diff / 1e9; a_["returned_relative"] = abs(diff) / abs(float(kkt["primal_objective"]))
        a_["basis"] = "v5/kkt_summary.json (returned arrays)"
    elif "returned_iteration_by_log" in a_:
        r = a_["returned_iteration_by_log"]; a_["returned_difference_eur"] = r["difference_eur"]; a_["returned_difference_bn"] = r["difference_bn"]; a_["returned_relative"] = r["relative_difference"]
        a_["basis"] = "Gurobi log line of the returned iterate"
    a_["passed"] = bool(abs(a_.get("returned_difference_bn", np.inf)) <= 0.01 and a_.get("returned_relative", np.inf) <= 1e-5)
    if "returned_iteration_by_log" in a_:
        r = a_["returned_iteration_by_log"]; a_["log_check_passed"] = bool(abs(r["difference_bn"]) <= 0.01 and r["relative_difference"] <= 1e-5)
    res["a_total_cost"] = a_
    # ---------------- model, arrays, country maps
    lp = sd / "lp"; meta = json.loads((lp / "MATH_PROBLEM.json").read_text())
    Z = {k: np.load(lp / (k + ".npy")) for k in ["cost", "col_lower", "col_upper", "row_lower", "row_upper", "start", "index", "value", "clabels", "vlabels"]}
    x, pi, rc = [np.load(sd / "solution" / (k + ".npy")) for k in ("X", "Pi", "RC")]
    nr, nc = meta["num_row"], meta["num_col"]
    A = sp.csc_matrix((Z["value"], Z["index"], Z["start"]), shape=(nr, nc))
    n, m, cfg = build_model(a.repo, a.network, a.scenario, a.truncate, a.label)
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
    rcode = country_lookup(m.constraints, Z["clabels"], n, maps, codes); ccode = country_lookup(m.variables, Z["vlabels"], n, maps, codes)
    inv = {v: k for k, v in codes.items()}
    act = A @ x
    # ---------------- (b) (same formulas as l23_violation_analysis.py; consistency check against its totals)
    gross = country_gross_co2_flows(ns) if ns is not None else {}; pools = pool_capacities(ns if ns is not None else n)
    row_ref, col_ref, _ = special_references(m, ns if ns is not None else n, Z["clabels"], Z["vlabels"], gross, pools)
    interior = (cfg["research"].get("solver", {}) or {}).get("interior", {})
    B = budgets(interior, float(cfg["research"]["solver"]["profiles"]["formal_barrier"]["BarConvTol"]))
    lo, hi = Z["row_lower"], Z["row_upper"]; lf, uf = np.isfinite(lo), np.isfinite(hi)
    rv = np.maximum(np.maximum(np.where(lf, lo - act, 0.0), np.where(uf, act - hi, 0.0)), 0.0)
    mag = abs(A) @ np.abs(x)
    rref = np.maximum.reduce([np.where(lf, np.abs(lo), 0.0), np.where(uf, np.abs(hi), 0.0), mag, row_ref]); ratio = rv / (ABS_FLOOR + B["primal_relative"] * rref)
    foc = rv * np.abs(pi)
    b_ = dict(rows_violated=int((rv > 0).sum()), rows_over_budget=int((ratio > 1).sum()), row_violation_max=float(rv.max(initial=0)), row_max_ratio=float(ratio.max(initial=0)),
              first_order_cost_eur_all_rows=float(foc.sum()),
              consistency_with_l23_script=dict(rows_over_budget=V["totals"]["rows_over_budget"], first_order_cost_eur=V["totals"]["first_order_cost_eur"],
                                               equal=bool(V["totals"]["rows_over_budget"] == int((ratio > 1).sum()))))
    foc_c = by_country(rcode, foc, inv); b_["first_order_cost_eur_by_country_all_rows"] = foc_c
    folded = fold_cross_border(foc_c)
    b_["country_check"] = {c: dict(first_order_cost_bn=folded.get(c, 0.0) / 1e9, threshold_bn=threshold_bn(c), passed=bool(folded.get(c, 0.0) / 1e9 <= threshold_bn(c)))
                           for c in list(COUNTRIES) + ["ASEAN"]}
    b_["unattributed_eur"] = folded.get("-", 0.0)
    b_["passed"] = bool(all(v["passed"] for v in b_["country_check"].values()))
    b_["families_top"] = [dict(family=k, rows_over_budget=v["rows_over_budget"], max_violation=v["max_violation"], max_ratio_to_budget=v["max_ratio_to_budget"],
                               first_order_cost_eur=v["first_order_cost_eur"], countries_over_budget=v.get("countries_over_budget"),
                               top_row=(v["top"][0] if v.get("top") else None)) for k, v in list(V["by_family"].items())[:12]]
    # biomass pools of BN / SG / VN among the rows over budget
    pool_names = set(pools)
    over = np.flatnonzero(ratio > 1)
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
    c_ = {}
    b16 = gates.get("B16_LEDGER", {})
    c_["b16"] = dict(relative_error=b16.get("relative_error"), tolerance=b16.get("tolerance"), passed_gate=b16.get("passed"),
                     ledger_identity=(led.get("identity") or {}).get("relative_error"),
                     passed=bool(b16.get("relative_error") is not None and float(b16["relative_error"]) <= 1e-6))
    aty = A.T @ pi; resid = Z["cost"] - aty - rc
    S = np.abs(resid * x)
    eq = lf & uf & (lo == hi)
    slack = np.where(pi > 0, np.where(lf, np.maximum(act - lo, 0.0), np.nan), np.where(pi < 0, np.where(uf, np.maximum(hi - act, 0.0), np.nan), 0.0))
    row_sign_err = np.isnan(slack) & ~eq
    Rr = np.where(eq | np.isnan(slack), 0.0, np.abs(pi) * np.nan_to_num(slack))
    cl, cu = Z["col_lower"], Z["col_upper"]; clf, cuf = np.isfinite(cl), np.isfinite(cu)
    cslack = np.where(rc > 0, np.where(clf, np.maximum(x - cl, 0.0), np.nan), np.where(rc < 0, np.where(cuf, np.maximum(cu - x, 0.0), np.nan), 0.0))
    col_sign = np.isnan(cslack)
    K = np.where(col_sign, 0.0, np.abs(rc) * np.nan_to_num(cslack)); Ksign = np.where(col_sign, np.abs(rc * x), 0.0)
    Sc, Rc, Kc, KSc = (by_country(code, w, inv) for code, w in ((ccode, S), (rcode, Rr), (ccode, K), (ccode, Ksign)))
    fS, fR, fK, fKS = (fold_cross_border(d) for d in (Sc, Rc, Kc, KSc))
    c_["formulas"] = dict(stationarity="S_c = sum_j |(c_j - a_j' pi - rc_j) x_j|", row_complementarity="R_c = sum_i |pi_i| (slack on the multiplier's bound)+, inequality rows",
                          column_complementarity="K_c = sum_j |rc_j| (x_j - bound)+; free-column dual-sign error |rc_j x_j| separately (KS_c)",
                          attribution="rows / columns by the component's bus country; cross-border components counted fully for both countries",
                          label="INFERENCE: first-order estimate of the effect of the KKT residuals on country settlements (EUR)")
    c_["totals_eur"] = dict(stationarity=float(S.sum()), row_complementarity=float(Rr.sum()), column_complementarity=float(K.sum()), column_dual_sign_error=float(Ksign.sum()),
                            row_dual_sign_rows=int(row_sign_err.sum()))
    c_["by_country_raw_eur"] = dict(stationarity=Sc, row_complementarity=Rc, column_complementarity=Kc, column_dual_sign_error=KSc)
    cc = {}
    for c in list(COUNTRIES) + ["ASEAN"]:
        s, r_, k_, ks = fS.get(c, 0.0), fR.get(c, 0.0), fK.get(c, 0.0), fKS.get(c, 0.0)
        thr = threshold_bn(c)
        cc[c] = dict(stationarity_bn=s / 1e9, row_complementarity_bn=r_ / 1e9, S_plus_R_bn=(s + r_) / 1e9, column_complementarity_bn=k_ / 1e9, column_dual_sign_bn=ks / 1e9,
                     all_terms_bn=(s + r_ + k_ + ks) / 1e9, threshold_bn=thr, passed=bool((s + r_) / 1e9 <= thr), passed_all_terms=bool((s + r_ + k_ + ks) / 1e9 <= thr))
    c_["country_check"] = cc
    c_["unattributed_eur"] = dict(stationarity=fS.get("-", 0.0), row_complementarity=fR.get("-", 0.0), column_complementarity=fK.get("-", 0.0), column_dual_sign_error=fKS.get("-", 0.0))
    c_["passed_kkt"] = bool(all(v["passed"] for v in cc.values())); c_["passed_kkt_all_terms"] = bool(all(v["passed_all_terms"] for v in cc.values()))
    c_["passed"] = bool(c_["b16"]["passed"] and c_["passed_kkt"])
    res["c_prices"] = c_
    grade = ("layer1_total_cost_screening" if (a_["passed"] and b_["passed"]) else "not_layer1")
    if grade == "layer1_total_cost_screening" and c_["passed"]:
        grade = "layer1_plus_nodal_price_settlement"
    res["grade"] = dict(grade=grade, a=a_["passed"], b=b_["passed"], c=c_["passed"],
                        price_settled_results=("usable" if (a_["passed"] and b_["passed"] and c_["passed"]) else "provisional"))
    res["seconds"] = time.time() - t0
    a.out_json.write_text(json.dumps(res, indent=1, default=str))
    # ---------------- markdown
    L = [f"# PILOT_PRECISION（S4N 补充 02 C1，第 119 项；只读，未启动 Gurobi）", "",
         f"- 运行：`{sd}`；终止 `{res['termination']}`；目标 {res['objective']}；基于**最终返回解**（solution/X、Pi、RC）。",
         f"- 分级：**{grade}**（(a) {a_['passed']}，(b) {b_['passed']}，(c) {c_['passed']}；按电价结算：{res['grade']['price_settled_results']}）", "",
         "## (a) 总成本精度", ""]
    if "returned_iteration_by_log" in a_:
        for key, title in (("best_before_first_stall", "第一轮停滞前最好迭代（原始残差最小）"), ("returned_iteration_by_log", "最终返回解（日志中与回执 objective_lp 相同的迭代）"),
                           ("last_iteration", "最后一次迭代"), ("second_round_min_primal_residual", "重启后原始残差最小的迭代")):
            r = a_.get(key)
            if r:
                L.append(f"- {title}：第 {r['iteration']} 次，原始 {r['primal_objective']:.9e}，对偶 {r['dual_objective']:.9e}，差 {r['difference_eur']:.4g} EUR（{r['difference_bn']:.6f} bn，相对 {r['relative_difference']:.2e}），"
                         f"原始残差 {r['primal_residual']:.3g}，对偶残差 {r['dual_residual']:.3g}，互补 {r['complementarity']:.3g}，{r['seconds']} s")
        if a_.get("restart"):
            L.append(f"- 重启：第 {a_['restart']['iteration']} 次（{a_['restart']['seconds']} s）")
        ti = a_["returned_iteration_by_log"].get("tied_iterations") or []
        if len(ti) > 1:
            L.append(f"- 注：日志只有 9 位有效数字，第 {ti[0]}–{ti[-1]} 次（共 {len(ti)} 次）的原始目标相同，返回解对应的迭代号取第一个；判定以返回数组的 KKT 摘要为准")
    k = a_["kkt_summary_returned_arrays"]
    L += [f"- 返回数组的 KKT 摘要：原始 {k.get('primal_objective')}，对偶 {k.get('dual_objective_numeric')}，差 {a_.get('returned_difference_bn', float('nan')):.6f} bn，相对 {a_.get('returned_relative', float('nan')):.2e} → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**{a_['passed']}**", "",
          "## (b) 原始违反（L23 §6 方法）", "",
          f"- 有正违反的行 {b_['rows_violated']:,}，超预算 {b_['rows_over_budget']:,}（与 `l23_violation_analysis.py` 一致：{b_['consistency_with_l23_script']['equal']}），最大违反 {b_['row_violation_max']:.4g}，最大为预算 {b_['row_max_ratio']:.4g} 倍；一阶影响合计 {b_['first_order_cost_eur_all_rows']:,.0f} EUR",
          "- 分国一阶影响（跨境行计入两国；阈值 = max(L23 365×24h 分国差额 1 %, 0.01 bn)，试点只有一体化，差额参照 L23）：", "",
          "| 国 | 一阶影响 bn | 阈值 bn | 通过 |", "|---|---|---|---|"]
    L += [f"| {c} | {v['first_order_cost_bn']:.2e} | {v['threshold_bn']:.4f} | {v['passed']} |" for c, v in b_["country_check"].items()]
    bp = b_["biomass_pools_BN_SG_VN"]
    L += ["", f"- BN / SG / VN 生物质池行：超预算行中 {bp['rows_over_budget_on_BN_SG_VN_pools']} / {bp['rows_over_budget_total']}（{bp['share_of_rows_over_budget']:.1%}）；最大倍数的行{'是' if bp['max_ratio_row_is_BN_SG_VN_pool'] else '不是'}此类行；前 10 行中 {bp['top10_rows_on_BN_SG_VN_pools']} 行；一阶影响占比 {bp['first_order_cost_share_of_BN_SG_VN_pool_rows']:.1%} → 仍占主导：**{bp['dominant']}**（{bp['dominance_rule']}）", "",
          "## (c) 价格质量", "",
          f"- B16 账本恒等式（试点节点价格分国结算）：相对误差 {c_['b16']['relative_error']}（≤ 1e-6）→ **{c_['b16']['passed']}**",
          f"- KKT 残差对分国结算的影响（INFERENCE；{c_['formulas']['stationarity']}；{c_['formulas']['row_complementarity']}；{c_['formulas']['column_complementarity']}；{c_['formulas']['attribution']}）：", "",
          "| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |", "|---|---|---|---|---|---|---|---|---|"]
    L += [f"| {c} | {v['stationarity_bn']:.2e} | {v['row_complementarity_bn']:.2e} | {v['S_plus_R_bn']:.2e} | {v['column_complementarity_bn']:.2e} | {v['column_dual_sign_bn']:.2e} | {v['threshold_bn']:.4f} | {v['passed']} | {v['passed_all_terms']} |"
          for c, v in cc.items()]
    L += ["", f"- 合计（EUR）：驻点 {c_['totals_eur']['stationarity']:,.0f}；行互补 {c_['totals_eur']['row_complementarity']:,.0f}；列互补 {c_['totals_eur']['column_complementarity']:,.0f}；自由列符号误差 {c_['totals_eur']['column_dual_sign_error']:,.0f}；未归属（'-'）见 JSON",
          f"- (c) 判定（B16 且每国 S+R ≤ 阈值）：**{c_['passed']}**（含列互补与符号误差的全部项：{c_['passed_kkt_all_terms']}）", "",
          f"用时 {res['seconds']:.0f} s。"]
    a.out_md.write_text("\n".join(L) + "\n")
    print(json.dumps(dict(grade=res["grade"], a=dict(diff_bn=a_.get("returned_difference_bn"), rel=a_.get("returned_relative")), b=dict(over=b_["rows_over_budget"], consistent=b_["consistency_with_l23_script"]["equal"],
                          worst=max(((c, v["first_order_cost_bn"] / v["threshold_bn"]) for c, v in b_["country_check"].items()), key=lambda t: t[1])), biomass=bp["dominant"],
                          c=dict(b16=c_["b16"]["relative_error"], worst=max(((c, v["S_plus_R_bn"] / v["threshold_bn"]) for c, v in cc.items()), key=lambda t: t[1])), seconds=round(res["seconds"])), default=str))


if __name__ == "__main__":
    main()
