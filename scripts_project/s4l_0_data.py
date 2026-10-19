"""S4L-0 data: registry fragment s4l_0 - decision 112 a / b (confirmed 2026-10-19 09:57 SGT): the four L23 first-batch runs are labelled
SCREENING_UNVERIFIED, the separately recovered NZE outputs are accepted as the batch NZE result, and the S4L scope rule.

    python scripts_project/s4l_0_data.py
"""
from __future__ import annotations

from d1_common import REG_DIR, ROOT, Registry, sha256

SCRIPT = "scripts_project/s4l_0_data.py"
INSTRUCTION_SHA = "03508400f675304cd0bdfd40ccbd0c61005644e7b2a122dffbe2048e6a5d529b"
SRC = "S4L instruction v1 2026-10-19 10:10 SGT, sections S4L-0 .. S4L-4 (user decisions 112 and 113 confirmed 2026-10-19 09:57 SGT)"
LOC = "work/p1_step4l_20261019/S4L_CLAUDE_CODE_INSTRUCTION.md"
L23 = "research/06_scope_redesign/p1_l23_run1_20261019/L23_RUN1_REPORT.md"
L23_SRC = "L23 first-round report sections 1-2, 6, 7 (items 3, 4) and 9 (PR #36)"
NZE_TARBALL = "nze_late_outputs_20261018T180030Z_5623.tar.gz"
NZE_SHA = "78a6ea15d369788f93c5fe20294e21fefd168db50d908ebad25f231c2001c33b"
RESULTS_SHA = "39b9c9ddc5fee0cf4a63381b2bde98798e9f29ae7bcb19a34acc7a991015ae7f"
ANSWERS = [
    ("s4l_l23_runs_screening_unverified",
     "L23 first cloud batch (365x24h day resolution, package code 56d28358, profile A formal_barrier, serial, result label FORMAL_TRIAL_365X24H): "
     "integrated STEPS / disconnected STEPS / disconnected gap diagnostic / integrated NZE ended SUBOPTIMAL / SUBOPTIMAL / SUBOPTIMAL / TIME_LIMIT, "
     "all_passed_solver_tolerances False in all four (primal violations 1e-8..1e-6 relative on near-zero quantities, dual side not converged) -> "
     "decision 112 a: the four runs are labelled SCREENING_UNVERIFIED; usable are the primal-side totals (objective values, B6 = 68.97 bn EUR, "
     "NZE - integrated = -90.46 bn EUR, first-order primal impact <= 4e-7); the nodal-price-dependent country settlements (congestion rent, "
     "cross-border settlement, subject split) and the small-country differences (PH 0.01, BN 0.11, TL 0.12 bn EUR) are not used for conclusions",
     "SCREENING_UNVERIFIED", "112"),
    ("s4l_l23_nze_late_outputs_accepted",
     "decision 112 b: the NZE outputs recovered separately from the instance (" + NZE_TARBALL + ", 21 files, 74,285,069 B, SHA256 " + NZE_SHA + "; "
     "local copy work/p1_step4k_20261018/cloud_results/20261018T180030Z_5623/nze_late/, outside the packed results tarball " + RESULTS_SHA + ") "
     "are accepted as the L23 NZE result: the 3 h wall-clock kill of run_365x24h.sh ended only the /usr/bin/time layer, s2_solve.py kept running "
     "and wrote the post-solve receipt, gates, ledger and solved network 09:00:52-09:03:02 SGT (L23 report section 1.3, finding 3); same label "
     "SCREENING_UNVERIFIED (TIME_LIMIT at Gurobi iteration 247, returned iterate = the one with the smallest primal residual, iteration 132)",
     NZE_SHA, "112"),
    ("s4l_l23_ledger_entry",
     "S4L-0: the project ledger research/STAGE2_PROJECT_LEDGER.md gets the L23 entry (first cloud batch, PR #36) that the L23 delivery did not "
     "write, carrying the SCREENING_UNVERIFIED label of decision 112 a and the NZE source note of decision 112 b",
     "added", "112"),
    ("s4l_scope_rule",
     "S4L scope (decisions 112 c, 113 (1), 113 (2)): near-zero quantity inventory and cleanup behind the switch research.numerics.dust_cleanup "
     "(S4L-1), new solver profile formal_barrier_crossover added next to profile A (profile A unchanged) and a local 56x3h diagnostic matrix of "
     "2 networks x 2 profiles x 2 scenarios = 8 runs with a comparison standard fixed before the runs (S4L-2), deployment script corrections "
     "run_365x24h.sh / preflight.sh / CLOUD_RESOURCE_ESTIMATE.md tested locally without rebuilding the package (S4L-3); no cloud action, no "
     "download, no 365x24h solve, no retry; other findings go to the report section 'found but not handled' without model change",
     "112c;113_1;113_2", "112,113"),
]


def main():
    reg = Registry(SCRIPT)
    for pid, desc, val, dec in ANSWERS:   # the answers are in the S4L instruction (S4L-0); the L23 report section 9 is the question
        unit = "sha256" if pid == "s4l_l23_nze_late_outputs_accepted" else "flag"
        reg.add(pid, desc, val, unit, "B", SRC, LOC, INSTRUCTION_SHA, decision_ref=dec, status="REFERENCE_ONLY")
    reg.add("s4l_question_source_l23", "S4L-0: the questions answered here are the L23 first-round report section 9 items 1-3 (treatment of the four "
            "non-optimal runs, archiving of the recovered NZE outputs, timing of the run_365x24h.sh / preflight.sh corrections)", "L23_RUN1_REPORT.md",
            "flag", "B", L23_SRC, L23, sha256(ROOT / L23), decision_ref="112", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4l_0.csv")
    print("registry fragment s4l_0 written:", len(ANSWERS) + 1, "rows")


if __name__ == "__main__":
    main()
