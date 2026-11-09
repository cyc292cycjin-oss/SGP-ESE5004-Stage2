"""V4 W20 section 4/5: verdict of one coalition solve against the REGISTERED x(S) (evidence/W20_XS_PRE.json, committed before the solves).

    python w20_eval.py --run-dir <results_project/v4w20/solves/<name>> --name <coalition> --xs <evidence/W20_XS_PRE.json> --log <evidence/W20_RUN_VERDICTS.jsonl>

c(S) = objective of the coalition run incl. the objective constants (SOLVE_RECEIPT.json 'objective', the same total-cost definition as the integrated
objective that the 12 Owen shares sum to). Registered rule (decision 139): violation iff x(S) - c(S) > max(0.01 x c(S), 0.01 bn). Printed verdicts:
WITHIN (optimal, within the threshold), VIOLATION (stop the batch: report to the reviewer, nothing changed or retried), NOT_OPTIMAL_WITHIN /
NOT_OPTIMAL_VIOLATION (a non-optimal returned objective: recorded; a violation still stops the batch), INFEASIBLE, NO_RESULT. Exit 3 on a violation.
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
    X = json.loads(a.xs.read_text())["coalitions"][a.name]
    rp = a.run_dir / "SOLVE_RECEIPT.json"
    rec = dict(coalition=a.name, evaluated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), x_dual_eur=X["x_dual_eur"], x_market_eur=X["x_market_eur"])
    if not rp.exists():
        rec.update(verdict="NO_RESULT", note="no SOLVE_RECEIPT.json")
    else:
        R = json.loads(rp.read_text())
        cond = R.get("termination_condition"); st = R.get("status"); obj = R.get("objective")
        gl = R.get("gurobi_log_stats") or {}
        rec.update(termination_condition=cond, status=st, objective_eur=obj, objective_lp_eur=R.get("objective_lp"), solve_seconds=R.get("solve_seconds"),
                   peak_rss_gib=(R.get("peak_rss_bytes") or 0) / 2**30, barrier_line=(gl.get("lines") or {}).get("barrier"), result_line=(gl.get("lines") or {}).get("result"),
                   input_network_sha256=(R.get("input_network") or {}).get("sha256"), registered_network_sha256=X["network_sha256"], post_solve_errors=[e.get("step") for e in R.get("post_solve_errors") or []])
        if rec["input_network_sha256"] != X["network_sha256"]:
            rec.update(verdict="NO_RESULT", note="the solved network differs from the registered coalition network")
        elif obj is None or st != "ok":
            rec.update(verdict="INFEASIBLE" if "infeasible" in str(cond).lower() else "NO_RESULT", note="no objective returned")
        else:
            c = float(obj); x = float(X["x_dual_eur"]); thr = max(0.01 * c, FLOOR)
            viol = x - c
            rec.update(c_eur=c, margin_dual_eur=c - x, violation_dual_eur=max(0.0, viol), threshold_eur=thr, within=bool(viol <= thr),
                       margin_dual_alpha_min_eur=c - float(X["x_dual_alpha_max_eur"]), margin_market_eur=c - float(X["x_market_eur"]),
                       within_market=bool(float(X["x_market_eur"]) - c <= thr), c_d8_eur=c + float(X["d8_addback_eur"]), margin_dual_d8_eur=c + float(X["d8_addback_eur"]) - x)
            if X.get("loo_country"):
                rec.update(loo_country=X["loo_country"], c_N_minus_c_eur=float(X["c_N_eur"]) - c, x_i_eur=float(X["x_i_dual_eur"]),
                           margin_141_eur=float(X["x_i_dual_eur"]) - (float(X["c_N_eur"]) - c))
            opt = (cond == "optimal")
            rec["verdict"] = ("WITHIN" if rec["within"] else "VIOLATION") if opt else ("NOT_OPTIMAL_WITHIN" if rec["within"] else "NOT_OPTIMAL_VIOLATION")
    with open(a.log, "a") as f:
        f.write(json.dumps(rec, default=str) + "\n")
    print(f"VERDICT:{a.name}:{rec['verdict']}:" + (f"c={rec.get('c_eur', float('nan'))/1e9:.4f}bn:x={rec['x_dual_eur']/1e9:.4f}bn:margin={rec.get('margin_dual_eur', float('nan'))/1e9:+.4f}bn:thr={rec.get('threshold_eur', float('nan'))/1e9:.4f}bn" if "c_eur" in rec else rec.get("note", "")))
    return 3 if rec["verdict"] in ("VIOLATION", "NOT_OPTIMAL_VIOLATION") else 0


if __name__ == "__main__":
    sys.exit(main())
