"""M12b section 3: the 11-country leave-one-out table and the pre-registered decision (no solve; reads the run outputs only).

For every country i (LOO_CHECK.json of m12_allocation.py loo, supplement 01 D8: c(N - i) gets back the remaining side's share of the removed
corridors' existing FOM; the raw value is reported alongside):
    c'(i) = c(N) - c(N - i);  test 1: Owen dual form phi_i >= c'(i);  test 2: market form >= c'(i) (reported alongside)
    violation = max(0, c'(i) - phi_i), tolerance = max(1 % of the country's B6 share, 0.01 bn) (C1 (b) threshold of the full run after the
    regrade with the batch reference of smoke_s01 = disconnected - integrated ledger difference of the country)
Pre-registered rule (instruction section 3, fixed before the results): all 11 violations within tolerance -> keep the model (cross-border
lines keep KVL); any violation above tolerance -> stop, change nothing, report the countries, violations and loops.

    python m12b_analysis.py --m12b <results_project/m12b> --loops <M12B_KVL_LOOPS.json> --out <evidence dir>
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")


def jl(p: Path) -> dict:
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return {}


def kvl_rows_per_snapshot(run: Path) -> float | None:
    f = run / "m12_owen" / "RHS_FAMILIES.csv"
    if not f.exists():
        return None
    with open(f) as h:
        rows = [r for r in csv.DictReader(h) if r["constraint"] == "Kirchhoff-Voltage-Law"]
    snaps = jl(run / "m12_owen" / "RHS_AUDIT.json").get("snapshots") or 56
    return sum(int(r["rows"]) for r in rows) / snaps if rows else 0.0


def rank_corr(x, y) -> dict:
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3 or np.std(x[ok]) == 0 or np.std(y[ok]) == 0:
        return dict(n=int(ok.sum()), pearson=None, spearman=None)
    rx = np.argsort(np.argsort(x[ok])); ry = np.argsort(np.argsort(y[ok]))
    return dict(n=int(ok.sum()), pearson=float(np.corrcoef(x[ok], y[ok])[0, 1]), spearman=float(np.corrcoef(rx, ry)[0, 1]))


def analyse(m12b: Path, loops: Path, out: Path) -> dict:
    L = jl(m12b / "LOO_CHECK" / "LOO_CHECK.json"); chk = (L.get("check") or {}).get("countries") or {}
    K = jl(loops); full_dir = m12b / "full_integrated"
    full_kvl = kvl_rows_per_snapshot(full_dir)
    O = jl(full_dir / "m12_owen" / "OWEN.json")
    rows = []
    for c in COUNTRIES:
        run = m12b / f"integrated_minus{c}"
        rec, prec, v6 = jl(run / "SOLVE_RECEIPT.json"), jl(run / "PRECISION.json"), jl(run / "V6_ACCEPTANCE.json")
        lp = (K.get("countries") or {}).get(c) or {}
        v = chk.get(c)
        r = dict(country=c, termination=rec.get("termination_condition"), status=rec.get("status"), solve_seconds=rec.get("solve_seconds"),
                 objective_c_N_minus_i=rec.get("objective"), c1_grade=(prec.get("grade") or {}).get("grade"), c1_a=(prec.get("grade") or {}).get("a"),
                 c1_b=(prec.get("grade") or {}).get("b"), c1_c=(prec.get("grade") or {}).get("c"), v6_label=v6.get("label") or v6.get("decision"),
                 variant_sha256=(rec.get("input_network") or {}).get("sha256"),
                 rhs_check_passed=jl(run / "m12_loo_rhs" / "LOO_RHS_CHECK.json").get("passed"),
                 dual_acceptance_loo_run=(jl(run / "m12_owen" / "OWEN.json").get("dual_acceptance") or {}).get("passed"),
                 kvl_loops_variant=lp.get("loops_variant"), kvl_rows_per_snapshot_lp=kvl_rows_per_snapshot(run), loops_removed=lp.get("loops_removed"),
                 domestic_loops=lp.get("domestic_loops"), loops_through_border=lp.get("loops_through_border"), crossing_branches=lp.get("crossing_branches"),
                 neighbours=" ".join(lp.get("neighbours") or []))
        if v is not None:
            tol = float(v["tolerance"]); cp = float(v["marginal_cost"]); cpr = float(v["marginal_cost_raw"]); phi = float(v["allocation"])
            mk = float(v["market_form_allocation_eur"])
            r.update(c_N_minus_i_raw=v["c_N_minus_i_raw"], addback_eur=v["addback_remaining_side_fom_eur"], c_prime=cp, c_prime_raw=cpr, phi_dual=phi,
                     phi_dual_interval_min=v.get("interval_min_eur"), market_form=mk, tolerance=tol,
                     violation_dual=max(0.0, cp - phi), violation_dual_raw=max(0.0, cpr - phi), violation_market=max(0.0, cp - mk),
                     margin_dual=phi - cp, margin_market=mk - cp,
                     within_dual=bool(max(0.0, cp - phi) <= tol), within_dual_raw=bool(max(0.0, cpr - phi) <= tol), within_market=bool(max(0.0, cp - mk) <= tol),
                     within_dual_at_interval_min=v.get("passed_at_interval_min"))
        rows.append(r)
    have = [r for r in rows if "c_prime" in r]
    exceed = [r["country"] for r in have if not r["within_dual"]]
    missing = [r["country"] for r in rows if "c_prime" not in r]
    if missing:
        decision = dict(rule_applicable=False, outcome="INCOMPLETE", note=f"no c(N - i) for {missing}: the pre-registered rule needs all 11")
    elif exceed:
        decision = dict(rule_applicable=True, outcome="STOP_VIOLATION", countries=exceed,
                        note="any violation above tolerance: stop, change nothing, report countries / violations / loops (reviewer and user decide)")
    else:
        decision = dict(rule_applicable=True, outcome="KEEP_MODEL", note="all 11 within tolerance: keep cross-border lines with KVL")
    decision.update(raw_c_prime_would_exceed=[r["country"] for r in have if not r["within_dual_raw"]],
                    market_form_exceeds=[r["country"] for r in have if not r["within_market"]],
                    runs_not_optimal=[r["country"] for r in rows if r["termination"] != "optimal"],
                    runs_c1_not_all_passed=[r["country"] for r in rows if not (r["c1_a"] and r["c1_b"] and r["c1_c"])],
                    runs_v6_not_accepted=[r["country"] for r in rows if r["v6_label"] != "ACCEPTED_LAYER2"])
    x = [r.get("loops_through_border") for r in have]
    res = dict(full=dict(objective=L.get("objective_full"), kvl_loops=(K.get("full") or {}).get("loops"), kvl_rows_per_snapshot_lp=full_kvl,
                         dual_acceptance=(O.get("dual_acceptance") or {}).get("passed"), usable_for_allocation=O.get("usable_for_allocation"),
                         c1=(jl(full_dir / "PRECISION.json").get("grade") or {})),
               tolerance_source=L.get("tolerance_source"), main_form=L.get("main_form"), adjustment=(L.get("check") or {}).get("adjustment"),
               indivisible_cost=(L.get("check") or {}).get("indivisible_cost"), indivisible_cost_sign=(L.get("check") or {}).get("indivisible_cost_sign"),
               indivisible_cost_raw=(L.get("check") or {}).get("indivisible_cost_raw"), indivisible_cost_sign_raw=(L.get("check") or {}).get("indivisible_cost_sign_raw"),
               scrb=L.get("scrb"), decision=decision, rows=rows,
               relation=dict(c_prime_minus_phi_vs_loops_through_border=rank_corr(x, [r["c_prime"] - r["phi_dual"] for r in have]),
                             c_prime_minus_market_vs_loops_through_border=rank_corr(x, [r["c_prime"] - r["market_form"] for r in have]),
                             c_prime_minus_phi_vs_loops_removed=rank_corr([r.get("loops_removed") for r in have], [r["c_prime"] - r["phi_dual"] for r in have])))
    out.mkdir(parents=True, exist_ok=True)
    (out / "M12B_RESULT.json").write_text(json.dumps(res, indent=1, default=str))
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(out / "M12B_LOO_TABLE.csv", "w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=keys); w.writeheader(); w.writerows(rows)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m12b", type=Path, required=True); ap.add_argument("--loops", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    r = analyse(a.m12b, a.loops, a.out)
    print(json.dumps(r["decision"], default=str))


if __name__ == "__main__":
    main()
