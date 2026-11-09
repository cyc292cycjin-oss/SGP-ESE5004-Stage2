"""V4 W20b section 4/5: verdict of one run against the REGISTERED allocations (evidence/W20B_XS_PRE.json, committed before the solves).

    python w20b_eval.py --run-dir <results_project/v4w20b/solves/<run>> --name <run> --xs <evidence/W20B_XS_PRE.json> --log <evidence/W20B_RUN_VERDICTS.jsonl>

c(S) = objective of the run incl. the objective constants (SOLVE_RECEIPT.json 'objective'; the total-cost definition the Owen shares sum to).
x(S): R0 -> x(N \\ B) = sum of the 11 countries' shares; ports coalitions -> x^m(S) = sum over S of (x_i + x_{B,i}). Registered rule (decision 139):
violation iff x(S) - c(S) > max(0.01 x c(S), 0.01 bn). Verdicts: STRICT (optimal, x <= c), WITHIN (optimal, 0 < x - c <= threshold), VIOLATION (stop the
batch: report to the reviewer, nothing changed or retried), NOT_OPTIMAL_* (non-optimal returned objective: recorded; a violation still stops the batch),
INFEASIBLE, NO_RESULT. Exit 3 on a violation. R0: D = c(N \\ B) - x(N \\ B); x(N \\ B) <= c(N \\ B) <=> the bunker pays at least its incremental cost.
Reading only: margin / merged Owen benefit of S (LOO: of the removed country i), and the bunker increment against W20 (same countries, no bunker):
Delta_S = c^m(S) - c_W20(S), D_S = x_B(S) - Delta_S (the integrated bunker payment of S above its incremental cost inside S).
"""
import argparse
import json
import sys
import time
from pathlib import Path

FLOOR = 1e7


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run-dir", type=Path, required=True); ap.add_argument("--name", required=True)
    ap.add_argument("--xs", type=Path, required=True); ap.add_argument("--log", type=Path, required=True)
    a = ap.parse_args()
    XS = json.loads(a.xs.read_text()); X = XS["runs"][a.name]
    rp = a.run_dir / "SOLVE_RECEIPT.json"
    rec = dict(run=a.name, network=X["network"], include_bunker=X["include_bunker"], evaluated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               x_dual_eur=X["x_dual_eur"], x_market_eur=X["x_market_eur"], x_bunker_part_eur=X["x_bunker_part_eur"])
    if not rp.exists():
        rec.update(verdict="NO_RESULT", note="no SOLVE_RECEIPT.json")
    else:
        R = json.loads(rp.read_text())
        cond = R.get("termination_condition"); st = R.get("status"); obj = R.get("objective")
        gl = R.get("gurobi_log_stats") or {}
        rec.update(termination_condition=cond, status=st, objective_eur=obj, objective_lp_eur=R.get("objective_lp"), solve_seconds=R.get("solve_seconds"),
                   peak_rss_gib=(R.get("peak_rss_bytes") or 0) / 2**30, barrier_line=(gl.get("lines") or {}).get("barrier"), result_line=(gl.get("lines") or {}).get("result"),
                   input_network_sha256=(R.get("input_network") or {}).get("sha256"), registered_network_sha256=X["network_sha256"],
                   post_solve_errors=[e.get("step") for e in R.get("post_solve_errors") or []])
        if rec["input_network_sha256"] != X["network_sha256"]:
            rec.update(verdict="NO_RESULT", note="the solved network differs from the registered network")
        elif obj is None or st != "ok":
            rec.update(verdict="INFEASIBLE" if "infeasible" in str(cond).lower() else "NO_RESULT", note="no objective returned")
        else:
            c = float(obj); x = float(X["x_dual_eur"]); thr = max(0.01 * c, FLOOR); viol = x - c
            rec.update(c_eur=c, margin_dual_eur=c - x, violation_dual_eur=max(0.0, viol), threshold_eur=thr, within=bool(viol <= thr), strict=bool(viol <= 0.0),
                       margin_relative_to_c=(c - x) / c, margin_dual_alpha_worst_eur=c - float(X["x_dual_alpha_max_eur"]), margin_market_eur=c - float(X["x_market_eur"]),
                       within_market=bool(float(X["x_market_eur"]) - c <= thr), c_d8_eur=c + float(X["d8_addback_eur"]), margin_dual_d8_eur=c + float(X["d8_addback_eur"]) - x,
                       owen_benefit_merged_eur=float(X["owen_benefit_merged_eur"]),
                       margin_over_benefit=((c - x) / float(X["owen_benefit_merged_eur"]) if float(X["owen_benefit_merged_eur"]) != 0 else None))
            if X.get("w20_c_eur") is not None:
                d_s = c - float(X["w20_c_eur"])
                rec.update(w20_c_eur=float(X["w20_c_eur"]), w20_margin_eur=float(X["w20_margin_eur"]), bunker_increment_eur=d_s,
                           bunker_payment_above_increment_eur=float(X["x_bunker_part_eur"]) - d_s, margin_change_vs_w20_eur=(c - x) - float(X["w20_margin_eur"]))
            if a.name == "R0":
                rec.update(D_eur=c - x, bunker_pays_at_least_incremental_cost=bool(c - x >= 0.0))
            if X.get("loo_country"):
                bi = float(X["b_i_merged_eur"])
                rec.update(loo_country=X["loo_country"], x_i_merged_eur=float(X["x_i_merged_eur"]), b_i_merged_eur=bi,
                           margin_over_b_i_merged=((c - x) / bi if bi != 0 else None))
            opt = (cond == "optimal")
            v = ("STRICT" if rec["strict"] else "WITHIN") if rec["within"] else "VIOLATION"
            rec["verdict"] = v if opt else "NOT_OPTIMAL_" + v
    with open(a.log, "a") as f:
        f.write(json.dumps(rec, default=str) + "\n")
    print(f"VERDICT:{a.name}:{rec['verdict']}:" + (f"c={rec['c_eur']/1e9:.4f}bn:x={rec['x_dual_eur']/1e9:.4f}bn:margin={rec['margin_dual_eur']/1e9:+.4f}bn:thr={rec['threshold_eur']/1e9:.4f}bn"
                                                   if "c_eur" in rec else rec.get("note", "")))
    return 3 if rec["verdict"] in ("VIOLATION", "NOT_OPTIMAL_VIOLATION") else 0


if __name__ == "__main__":
    sys.exit(main())
