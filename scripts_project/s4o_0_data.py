"""S4O-1 data: registry fragment s4o_0 - decisions 118 (S4M report section 9 items 2-5), 119 (S4N supplement 02: precision evidence instead of the
solver label, solver profile calibration) and 120 (production solver profile pypsa_eur_default with two registered adaptations, per-run acceptance).

    python scripts_project/s4o_0_data.py
"""
from __future__ import annotations

from d1_common import REG_DIR, ROOT, Registry, sha256

SCRIPT = "scripts_project/s4o_0_data.py"
S4O_SHA = "b5f4d099f2afe2e4e4d93cd2dee94ce42857b3a26f62d2622657d78b068af6aa"
S4O_SRC = "S4O instruction v1 2026-10-19 20:00 SGT, sections S4O-1 .. S4O-7 (user decision 120 confirmed 2026-10-19 19:40 SGT)"
S4O_LOC = "work/p1_step4o_20261019/S4O_CLAUDE_CODE_INSTRUCTION.md"
S4M = "research/06_scope_redesign/p1_step4m_20261019/S4M_REPORT.md"
S4N = "research/06_scope_redesign/p1_step4n_20261019/S4N_REPORT.md"
SUP02 = "research/06_scope_redesign/p1_step4n_20261019/S4N_SUPPLEMENT_02.md"


def main():
    reg = Registry(SCRIPT)
    reg.add("s4n_decision_118_s4m_open_items", "Decision 118 (user, 2026-10-19 before the S4N session; recorded in S4M report section 9 items 2-5 and the ledger by "
            "b3b3e5d2, registry row added in S4O-1): (2) the cloud probe and pilot are run by a later S4N instruction in a new session, no cloud action in S4M; "
            "(3) dual / cost-split export convention accepted (dual file stores the raw LP row duals per weighted snapshot, marginal_price divided by the snapshot "
            "weight by the PyPSA convention); (4) assign_all_duals=True kept (s2_solve.py and package f50c8850 as they are); (5) PRs #37 and #38 stay draft, "
            "not merged", "s4n_new_session;duals_accepted;assign_all_duals_kept;prs_draft", "flag", "B",
            "S4M report section 9 items 2-5 (PR #38, commit b3b3e5d2)", S4M, sha256(ROOT / S4M), decision_ref="118", status="REGISTERED")
    reg.add("s4n_decision_119_precision_over_label", "Decision 119 (user, 2026-10-19 16:37 SGT; S4N supplement 02): whether a run can be used is judged by the "
            "precision the research question needs, not by the solver termination label; a non-optimal run is not re-solved or changed but quantified first: "
            "(a) total-cost precision |primal - dual objective| <= 0.01 bn EUR and <= 1e-5 relative; (b) first-order country impact of the primal violations "
            "(L23 section 6 method, cross-border rows counted in both countries) per country <= max(1 % of that country's 'disconnected - integrated' "
            "difference, 0.01 bn EUR), with the BN / SG / VN biomass-pool rows checked for dominance; (c) price quality: B16 ledger identity <= 1e-6 relative "
            "and the KKT-residual impact on the country settlements (stationarity x value, dual x slack; INFERENCE) per country <= max(1 %, 0.01 bn); grading: "
            "(a)(b) pass -> tier 1 (total cost) usable as a screening result, (c) also pass -> nodal-price settlements usable, otherwise price-based settlements "
            "provisional. Also (C2): a solver profile pypsa_eur_default copied key by key from PyPSA-Eur v2025.07.0 gurobi-default is calibrated against "
            "profile A on the S4M-1 56x3h network with the decision-107 standard. Applied in S4N: the 365x24h integrated STEPS pilot (profile A, optimal) "
            "passed (a)(b)(c); the three calibration runs were optimal and passed the decision-107 standard", "precision_criteria_a_b_c", "flag", "B",
            "S4N supplement 02 v1 2026-10-19 16:50 SGT (user decision 119 confirmed 2026-10-19 16:37 SGT); results in the S4N report sections 7 and 9 (PR #39)",
            SUP02, sha256(ROOT / SUP02), decision_ref="107,119", status="REGISTERED")
    reg.add("s4o_decision_120_production_profile", "Decision 120 (user, 2026-10-19 19:40 SGT): the production solver profile for the 365x24h batch, the 2920x3h "
            "formal runs and the coalition runs is pypsa_eur_default = PyPSA-Eur v2025.07.0 gurobi-default (config.default.yaml lines 1056-1064) with two "
            "registered adaptations: (1) key names capitalised as in the code convention (Method, Crossover, Threads) - Gurobi parameters are case-insensitive, "
            "so the solve is unchanged, only the s2_solve.py gate-path detection is fixed (S4N finding 10); (2) Threads 8 instead of 32 - a hardware setting, "
            "PyPSA-Eur's 32 belongs to its cluster, 8 equals profile A for comparability; the other keys (Method 2, Crossover 0, BarConvTol 1e-5, Seed 123, "
            "AggFill 0, PreDual 0, GURO_PAR_BARDENSETHRESH 200) unchanged; profile A (formal_barrier) unchanged and kept as the verification reference. "
            "Acceptance of every run = Gurobi optimal + decision 119 (a)(b)(c) computed automatically after the solve (C1 post-processing in the run pipeline); "
            "the project solver-tolerance gates are still computed and reported as numerical information, not as a go / no-go criterion",
            "pypsa_eur_default;Threads_8;capitalised_keys", "flag", "B", S4O_SRC, S4O_LOC, S4O_SHA, decision_ref="107,119,120", status="REGISTERED")
    reg.add("s4o_question_source_s4n", "S4O-0: decision 120 answers the S4N report section 12 items 2 (production profile), 5 (S4N branch, draft PR, archiving) and 6 "
            "(decision-118 registry row); item 3 (the cloud batch) is prepared in S4O-4 / S4O-5 and run in S4O-6 only under a separate user authorisation",
            "S4N_REPORT.md", "flag", "B", "S4N report section 12 (PR #39)", S4N, sha256(ROOT / S4N), decision_ref="118,119,120", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4o_0.csv")
    print("registry fragment s4o_0 written:", len(reg.rows), "rows")


if __name__ == "__main__":
    main()
