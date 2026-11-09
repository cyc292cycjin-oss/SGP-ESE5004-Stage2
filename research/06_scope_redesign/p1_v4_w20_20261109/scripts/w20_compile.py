"""V4 W20 section 5: compile CORE_CHECK_V4_56.csv, CHECKPOINTS.csv and EVIDENCE.json from the solve folders, the per-run verdicts and the registered x(S).

    python w20_compile.py --solves <results_project/v4w20/solves> --work <work/p1_v4_w20_20261109> --m12b <work/p1_m12b_20261021/evidence/M12B_LOO_TABLE.csv>

Read only. Margins: c(S) - x(S) (positive = the coalition pays more on its own than its Owen share: the core condition holds strictly).
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/home/jin/wt_v4_w20/scripts_project")
from v4_coalition import COALITION_ORDER, coalitions, sha  # noqa: E402

FLOOR = 1e7


def barrier(R):
    ln = " ".join(((R.get("gurobi_log_stats") or {}).get("lines") or {}).get("barrier") or [])
    m = re.search(r"in (\d+) iterations and ([0-9.]+) seconds", ln)
    return (int(m.group(1)), float(m.group(2))) if m else (None, None)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--solves", type=Path, required=True); ap.add_argument("--work", type=Path, required=True); ap.add_argument("--m12b", type=Path, required=True)
    a = ap.parse_args()
    XS = json.loads((a.work / "evidence/W20_XS_PRE.json").read_text())
    st = (a.solves / "STATUS.txt").read_text().splitlines() if (a.solves / "STATUS.txt").exists() else []
    wall = {}
    for ln in st:
        m = re.match(r"END_(\w+):[^:]+:[^:]+:[^:]+:exit=(-?\d+):(\d+)s:", ln)
        if m:
            wall[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    m12b = {r["country"]: r for r in csv.DictReader(open(a.m12b))} if a.m12b.exists() else {}
    rows, cps = [], []
    for name in COALITION_ORDER:
        X = XS["coalitions"][name]; d = a.solves / name; rp = d / "SOLVE_RECEIPT.json"
        r = dict(coalition=name, n_members=X["n_members"], members=X["members"], network_sha256=X["network_sha256"], x_dual_eur=X["x_dual_eur"],
                 x_dual_alpha_min_eur=X["x_dual_alpha_min_eur"], x_dual_alpha_max_eur=X["x_dual_alpha_max_eur"], x_market_eur=X["x_market_eur"], d8_addback_eur=X["d8_addback_eur"])
        if not rp.exists():
            r.update(termination="not_run"); rows.append(r); continue
        R = json.loads(rp.read_text()); it, bs = barrier(R)
        P = json.loads((d / "PRECISION.json").read_text()) if (d / "PRECISION.json").exists() else {}
        pa = P.get("a_total_cost") or {}
        r.update(termination=R.get("termination_condition"), status=R.get("status"), gurobi_result=" ".join(((R.get("gurobi_log_stats") or {}).get("lines") or {}).get("result") or []),
                 barrier_iterations=it, barrier_seconds=bs, solve_seconds=R.get("solve_seconds"), wall_seconds=(wall.get(name) or (None, None))[1], exit_code=(wall.get(name) or (None, None))[0],
                 peak_rss_gib=(R.get("peak_rss_bytes") or 0) / 2**30, lp_cols=(R.get("lp") or {}).get("num_col"), lp_rows=(R.get("lp") or {}).get("num_row"),
                 post_solve_errors=" ".join(e.get("step", "") for e in R.get("post_solve_errors") or []),
                 c1_grade=(P.get("grade") or {}).get("grade") if isinstance(P.get("grade"), dict) else P.get("grade"),
                 c1_a=(P.get("grade") or {}).get("a") if isinstance(P.get("grade"), dict) else None, c1_b=(P.get("grade") or {}).get("b") if isinstance(P.get("grade"), dict) else None,
                 c1_c=(P.get("grade") or {}).get("c") if isinstance(P.get("grade"), dict) else None,
                 c1_primal_minus_dual_eur=((pa.get("returned_iteration_by_log") or pa.get("last_iteration") or {}).get("difference_eur")))
        if R.get("status") == "ok" and R.get("objective") is not None:
            c = float(R["objective"]); thr = max(0.01 * c, FLOOR)
            mg = c - X["x_dual_eur"]; mga = c - X["x_dual_alpha_max_eur"]; mm = c - X["x_market_eur"]
            r.update(c_eur=c, objective_lp_eur=R.get("objective_lp"), margin_dual_eur=mg, threshold_eur=thr, violation_dual_eur=max(0.0, -mg),
                     verdict=("strict" if mg >= 0 else ("within_tolerance" if -mg <= thr else "VIOLATION")),
                     margin_dual_alpha_worst_eur=mga, margin_market_eur=mm, verdict_market=("strict" if mm >= 0 else ("within_tolerance" if -mm <= thr else "VIOLATION")),
                     c_d8_eur=c + X["d8_addback_eur"], margin_dual_d8_eur=c + X["d8_addback_eur"] - X["x_dual_eur"], margin_relative=mg / c)
            if X.get("loo_country"):
                i = X["loo_country"]; cN = float(X["c_N_eur"])
                r.update(loo_country=i, c_N_eur=cN, c_N_minus_c_eur=cN - c, x_i_dual_eur=X["x_i_dual_eur"], x_i_market_eur=X["x_i_market_eur"],
                         margin_141_eur=X["x_i_dual_eur"] - (cN - c), margin_141_market_eur=X["x_i_market_eur"] - (cN - c))
                if i in m12b:
                    r.update(m12b_v2_margin_dual_eur=float(m12b[i]["margin_dual"]), m12b_v2_margin_market_eur=float(m12b[i]["margin_market"]), m12b_v2_c_prime_eur=float(m12b[i]["c_prime"]),
                             m12b_v2_phi_dual_eur=float(m12b[i]["phi_dual"]), m12b_v2_loops_through_border=int(float(m12b[i]["loops_through_border"])))
        rows.append(r)
        cps.append(dict(step="W20-3", item=f"solve {name}", result=r.get("verdict", r.get("termination")), detail=f"{r.get('termination')} c={r.get('c_eur', float('nan'))/1e9:.4f} bn margin={r.get('margin_dual_eur', float('nan'))/1e9:+.4f} bn", file=f"results_project/v4w20/solves/{name}/SOLVE_RECEIPT.json"))
    cols = []
    for r in rows:
        cols += [k for k in r if k not in cols]
    with open(a.work / "CORE_CHECK_V4_56.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})
    done = [r for r in rows if "c_eur" in r]
    summ = dict(solves=len([r for r in rows if r.get("termination") not in (None, "not_run")]), evaluated=len(done),
                optimal=len([r for r in rows if r.get("termination") == "optimal"]), strict=len([r for r in done if r["verdict"] == "strict"]),
                within_tolerance=len([r for r in done if r["verdict"] == "within_tolerance"]), violations=[r["coalition"] for r in done if r["verdict"] == "VIOLATION"],
                market_all_hold=bool(done) and all(r["verdict_market"] != "VIOLATION" for r in done), market_strict=len([r for r in done if r["verdict_market"] == "strict"]),
                min_margin=min(((r["margin_dual_eur"], r["coalition"]) for r in done), default=None), max_margin=max(((r["margin_dual_eur"], r["coalition"]) for r in done), default=None),
                min_margin_market=min(((r["margin_market_eur"], r["coalition"]) for r in done), default=None),
                min_relative_margin=min(((r["margin_relative"], r["coalition"]) for r in done), default=None),
                solve_seconds_total=sum(float(r.get("solve_seconds") or 0) for r in rows), wall_seconds_total=sum(float(r.get("wall_seconds") or 0) for r in rows),
                peak_rss_gib_max=max((r.get("peak_rss_gib") or 0) for r in rows))
    ev = dict(step="V4 W20", decision="228", instruction=dict(file="V4_W20_INSTRUCTION.md", sha256="f4419a8347be3fa00cd7fec8e8fd508a2999dc91b56ee47304b5236f62a6f97b"),
              model="claude-opus-5-5", branch="asean/v4-w20-20261109", registration_commit="ad7b7f1a64237998745e2955aa2f06aed2446d13", tool_commit="a312974d",
              base_network=dict(file="hpc_package_v4/networks/integrated_2920_3h_unsolved.nc", sha256="86f6d6a0fce2f0e04d12ee7993aee885256fcaadadaeeca308414017738c801d"),
              x_source=dict(owen=XS["owen"], owen_sha256=XS["owen_sha256"], identity=XS["identity"]), threshold_rule=XS["threshold_rule"], summary=summ,
              coalitions={r["coalition"]: {k: v for k, v in r.items() if k != "coalition"} for r in rows}, solver_calls=summ["solves"],
              stop_conditions=dict(violation=bool(summ["violations"])))
    (a.work / "EVIDENCE.json").write_text(json.dumps(ev, indent=1, default=str) + "\n")
    with open(a.work / "CHECKPOINTS.csv", "w", newline="") as f:
        base = [dict(step="W20-0", item="instruction SHA256", result="match", detail="f4419a83... = V4_W20_SHA256.txt", file="V4_W20_SHA256.txt"),
                dict(step="W20-0", item="session model / start conditions", result="ok", detail="claude-opus-5-5 effort xhigh; W19a stopped; no Gurobi process; 9 GiB available", file="PROGRESS.md"),
                dict(step="W20-0", item="26c2e47d ancestor of ac75354c, diff only W14 delivery", result="ok", detail="0 files outside research/06_scope_redesign/p1_v4_w14_20261109", file="PROGRESS.md"),
                dict(step="W20-1", item="tests test_v4_coalition.py", result="25 passed", detail="(a)(b)(c)(d) + toy", file="logs/tests_v4_coalition.txt"),
                dict(step="W20-1", item="tests A2 fallback + M08a A7", result="10 passed", detail="default build path unchanged", file="logs/tests_a2_a7.txt"),
                dict(step="W20-1", item="17 networks built", result="17/17", detail="SHA256 in tables/W20_COALITION_BUILD.csv", file="logs/build_nets56.txt"),
                dict(step="W20-1", item="static checks", result="17/17 pass", detail="zero-slack gate, net-zero rows with removal ports, no new NaN", file="evidence/STATIC_CHECKS_W20.json"),
                dict(step="W20-1", item="LP identity pre-cut vs --truncate 56", result="identical", detail="12 LP arrays byte-identical, solver not called", file="logs/lpcheck.txt"),
                dict(step="W20-2", item="registration committed before solves", result="ad7b7f1a", detail="identity -4,519 EUR <= 0.01 bn", file="CORE_CHECK_V4_56.md")]
        w = csv.DictWriter(f, fieldnames=["step", "item", "result", "detail", "file"], lineterminator="\n"); w.writeheader()
        for r in base + cps:
            w.writerow(r)
    print(json.dumps(summ, indent=1, default=str))


if __name__ == "__main__":
    main()
