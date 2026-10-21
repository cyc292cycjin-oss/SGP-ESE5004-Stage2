"""S4Q-4: light evidence JSON of the S4Q report (S4Q_EVIDENCE.json) from the committed evidence folder - profile definitions and the key-by-key check,
script / unit tests, the six runs (STATUS lines, receipts, C1), the S4Q-3 verdict (S4Q3_JUDGE.json) and the information items. READ ONLY.

    python s4q_collect_evidence.py --deliv <research/06_scope_redesign/p1_step4q_20261020> --repo <code> --out <S4Q_EVIDENCE.json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import yaml

SCEN = ("integrated", "disconnected", "integrated_nze")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def jl(p: Path) -> dict:
    return json.loads(p.read_text()) if p.exists() else {}


def status_lines(p: Path) -> dict:
    out = {}
    for ln in p.read_text().splitlines():
        k = ln.split(":", 1)[0]
        out.setdefault(k, []).append(ln)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--deliv", type=Path, required=True); ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(); D = a.deliv; E = D / "evidence"
    prof = yaml.safe_load((a.repo / "configs/research/baseline.yaml").read_text())["research"]["solver"]
    A = prof["profiles"]["formal_barrier"]
    keycheck = {}
    for n in ("formal_barrier_1e6", "formal_barrier_1e6_t16"):
        P = prof["profiles"][n]
        keycheck[n] = dict(parameters=P, same_keys_same_order=list(P) == list(A), differences={k: dict(profile_A=A[k], candidate=P[k]) for k in A if P.get(k) != A[k]},
                           equal_keys=[k for k in A if P.get(k) == A[k]])
    tests = {}
    for name, p in (("s4o_harness_rerun", E / "s4q_1/s4o4_rerun/TEST_RESULTS.txt"), ("s4q_cases", E / "s4q_1/results/TEST_RESULTS_s4q1.txt")):
        if p.exists():
            m = re.search(r"SUMMARY: pass=(\d+) fail=(\d+)", p.read_text()); tests[name] = dict(passed=int(m.group(1)), failed=int(m.group(2)), file=str(p.relative_to(D)))
    J = jl(E / "s4q_3/S4Q3_JUDGE.json")
    runs = {}
    for t in ("t8", "t16"):
        st = status_lines(E / f"s4q_2/{t}/STATUS.txt")
        rr = {}
        for sc in SCEN:
            d = E / f"s4q_2/{t}/{sc}"; rec = jl(d / "SOLVE_RECEIPT.json")
            rr[sc] = dict(termination=rec.get("termination_condition"), objective=rec.get("objective"), objective_lp=rec.get("objective_lp"), solver_profile=rec.get("solver_profile"),
                          solver_parameters=rec.get("solver_parameters"), solve_seconds=rec.get("solve_seconds"), peak_rss_gib=(rec.get("peak_rss_bytes") or 0) / 2**30,
                          input_network_sha256=(rec.get("input_network") or {}).get("sha256"), truncated_to=(rec.get("input_network") or {}).get("truncated_to"),
                          status_solve=next((x for x in st.get(f"SOLVE_{sc}", [])), None), status_run=next((x for x in st.get(f"RUN_{sc}", [])), None),
                          status_c1_pipeline=next((x for x in st.get(f"PRECISION_{sc}", [])), None), status_regrade_pipeline=st.get(f"REGRADE_{sc}", []),
                          status_gap=next((x for x in st.get(f"GAP_{sc}", [])), None),
                          receipt_sha256=sha(d / "SOLVE_RECEIPT.json") if (d / "SOLVE_RECEIPT.json").exists() else None)
        runs[t] = dict(profile=keycheck["formal_barrier_1e6" if t == "t8" else "formal_barrier_1e6_t16"]["parameters"], run_folder=(E / f"s4q_2/{t}/RUN_FOLDER.txt").read_text().strip(),
                       start=st.get("START", [None])[0], done=st.get("DONE", [None])[0], other_lines=[x for k in ("NO_STOP_FIXED_RUNS_INTEGRATED_NONOPTIMAL_C1_FAILED", "NO_GAP_DIAGNOSTIC_FIXED_RUNS_DISCONNECTED_NON_OPTIMAL", "STOP_INTEGRATED_NONOPTIMAL_C1_FAILED", "BATCH_REFERENCE") for x in st.get(k, [])],
                       results_tarball_sha256=next(iter((E / f"s4q_2/{t}").glob("results_*.tar.gz.sha256")), Path("/nonexistent")).read_text().split()[0] if any((E / f"s4q_2/{t}").glob("results_*.tar.gz.sha256")) else None,
                       runs=rr)
    out = dict(step="S4Q", decision="123", instruction=dict(file="S4Q_CLAUDE_CODE_INSTRUCTION.md", sha256=sha(D / "S4Q_CLAUDE_CODE_INSTRUCTION.md")),
               authorisation="six local 56x3h runs (candidate BarConvTol 1e-6 x two thread paths x three scenarios), 30 min stop-loss each, no retry, no cloud (user, 2026-10-20)",
               profile_A=A, production_default=prof["profile"], candidate_key_check=keycheck, tests=tests, driver_status=(E / "s4q_2/DRIVER_STATUS.txt").read_text().splitlines(),
               runs=runs, verdict=dict(level1_passed=J.get("level1_passed"), criteria={t: (J.get("paths") or {}).get(t, {}).get("criteria") for t in ("t8", "t16")}),
               judge=dict(file="evidence/s4q_3/S4Q3_JUDGE.json", sha256=sha(E / "s4q_3/S4Q3_JUDGE.json") if (E / "s4q_3/S4Q3_JUDGE.json").exists() else None),
               criteria_detail={t: {k: (J["paths"][t].get(k)) for k in ("criterion_1", "criterion_2", "criterion_3", "criterion_3_asean_pool_information", "criterion_4")} for t in (J.get("paths") or {})},
               information=dict(efficiency={t: J["paths"][t]["efficiency_information"] for t in (J.get("paths") or {})},
                                c1_s4m2_reference={t: J["paths"][t]["c1_s4m2_reference"] for t in (J.get("paths") or {})},
                                prices_co2_biomass={t: J["paths"][t]["information"] for t in (J.get("paths") or {})},
                                B6_bn_eur={t: J["paths"][t]["B6_bn_eur"] for t in (J.get("paths") or {})},
                                nze_minus_integrated_bn_eur={t: J["paths"][t]["nze_minus_integrated_bn_eur"] for t in (J.get("paths") or {})},
                                between_paths=J.get("between_paths")),
               consistency=J.get("consistency"),
               labels=dict(VERIFIED="receipts, logs, ledgers, C1 arrays", INFERENCE="C1 (c) country effect of KKT residuals; mechanism explanations in the report", PROPOSED="level-2 plan"))
    a.out.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(dict(level1_passed=out["verdict"]["level1_passed"], tests=tests), default=str))


if __name__ == "__main__":
    main()
