"""S4L-6 data: registry fragment s4l_6 - the user decisions of 2026-10-19 after the S4L report (sections 9 and 10): cleanup adopted for the
second-batch main run (research.numerics.dust_cleanup on, corrected rule), profile A, crossover profile abandoned, biomass zero-slack kept.

    python scripts_project/s4l_6_data.py [--package-commit <sha>]
"""
from __future__ import annotations

import argparse

from d1_common import REG_DIR, ROOT, Registry, sha256

SCRIPT = "scripts_project/s4l_6_data.py"
SRC = "User decision 2026-10-19 after the S4L report (sections 9 and 10): adopt the cleanup for the second-batch main run (dust_cleanup on, corrected rule), profile A, abandon the crossover profile, keep the biomass zero slack"
LOC = "research/06_scope_redesign/p1_step4l_20261019/S4L_REPORT.md"
CFG = "configs/research/baseline.yaml"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--package-commit", default=""); a = ap.parse_args()
    reg = Registry(SCRIPT); cfg_sha = sha256(ROOT / CFG); rep_sha = sha256(ROOT / LOC)
    reg.add("s4l6_decision_dust_cleanup_on", "User decision 2026-10-19 (S4L report section 9 item 1): the second-batch main run uses research.numerics.dust_cleanup = on with the "
            "corrected rule (fixed-demand guard s4l1_pool_fixed_demand_guard); baseline.yaml default changed off -> on; verified in S4L-2 continuation: profile A optimal on both "
            "scenarios, objective relative difference 7.3e-8 / 6.8e-8 to the S4K reference, B16 <= 8e-12, every country's disconnected - integrated difference unchanged (0.0000 bn "
            "EUR), AC nodal prices identical bus by bus; LP rows -7.1 % / -7.4 %", "on", "flag", "B", SRC, LOC, rep_sha, decision_ref="113", status="REGISTERED")
    reg.add("s4l6_decision_profile_a", "User decision 2026-10-19 (S4L report section 9 items 1-2): the formal solver profile of the second batch is A (formal_barrier, Crossover 0); "
            "the S4L-2 profile formal_barrier_crossover (Gurobi Crossover -1) is ABANDONED after ending infeasible_or_unbounded in the simplex clean-up on all four runs; it stays in "
            "baseline.yaml only as the record of those runs and is not to be used", "formal_barrier", "flag", "B", SRC, CFG, cfg_sha, decision_ref="113", status="REGISTERED")
    reg.add("s4l6_decision_biomass_zero_slack_kept", "User decision 2026-10-19 (S4L report section 9 item 4 / section 10): the zero slack of the BN / SG / VN solid-biomass balances "
            "(decision-36 rule capping the fixed biomass demand at the potential) is kept as is; research.s2.industry.biomass_overflow_cap_share stays 1.0 (main); the 98 % diagnostic "
            "network and its two runs remain diagnostic only; the solid-biomass shadow prices of these three countries are not used for conclusions. SUPERSEDED the same day by "
            "decision 115 (S4M instruction 12:20 SGT): main biomass_overflow_cap_share 0.98, 1.0 as a second-batch sensitivity", "1.0", "share", "B", SRC, LOC,
            rep_sha, decision_ref="36,55,113,115", status="REFERENCE_ONLY")
    reg.add("s4l6_package_s4l", "S4L-6: the four deployment networks (integrated STEPS, disconnected STEPS, integrated NZE, disconnected gap diagnostic; 2920x3h + 365x24h) were "
            "built with dust_cleanup on (corrected rule) at commit 1655e623 (results_project/s4l/s4l6, static validation passed, integrated / disconnected identical to the S4L-1 "
            "builds component by component, tests/research 534 passed) but NOT packaged: the S4M instruction (decision 115, biomass_overflow_cap_share 0.98) changes the main "
            "setting again and rebuilds the package in S4M-3 with the S4L scripts; the S4K package 56d28358 stays the last packaged one until S4M-3"
            + (f"; package code {a.package_commit}" if a.package_commit else ""), (a.package_commit or "built_not_packaged_superseded_by_S4M"), "flag", "B", SRC, LOC, rep_sha, decision_ref="113,116", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4l_6.csv")
    print("registry fragment s4l_6 written:", len(reg.rows), "rows")


if __name__ == "__main__":
    main()
