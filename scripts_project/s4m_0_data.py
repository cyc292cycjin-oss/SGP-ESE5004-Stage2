"""S4M-0 data: registry fragment s4m_0 - decisions 114, 115, 116 (confirmed 2026-10-19 12:12 SGT): main-run settings (dust cleanup on, crossover
dropped), biomass overflow cap share 0.98 as main (1.0 sensitivity), pilot before the batch.

    python scripts_project/s4m_0_data.py
"""
from __future__ import annotations

from d1_common import REG_DIR, ROOT, Registry, sha256

SCRIPT = "scripts_project/s4m_0_data.py"
INSTRUCTION_SHA = "e791015e2135845746e0ef47a50e15fae1d45d0cc586c723cc5c8197cc4c567c"
SRC = "S4M instruction v1 2026-10-19 12:20 SGT, sections S4M-0 .. S4M-5 (user decisions 114, 115, 116 confirmed 2026-10-19 12:12 SGT)"
LOC = "work/p1_step4m_20261019/S4M_CLAUDE_CODE_INSTRUCTION.md"
S4L = "research/06_scope_redesign/p1_step4l_20261019/S4L_REPORT.md"
CFG = "configs/research/baseline.yaml"


def main():
    reg = Registry(SCRIPT); s4l_sha = sha256(ROOT / S4L)
    reg.add("s4m_decision_114_main_settings", "Decision 114: research.numerics.dust_cleanup = on is the MAIN setting (corrected rule of S4L-1: near-zero objects removed, pools "
            "needed by a fixed demand kept; verified in the S4L-2 continuation - profile A optimal, objective 7e-8 from the S4K reference, country differences unchanged); "
            "off is the comparison (S4K state, L23 first batch); the S4L-2 profile formal_barrier_crossover is neither a formal nor a verification profile (it ended "
            "infeasible_or_unbounded in the simplex clean-up on all four runs); the formal profile stays A (formal_barrier)", "dust_cleanup_on;profile_A;no_crossover", "flag", "B",
            SRC, LOC, INSTRUCTION_SHA, decision_ref="114", status="REGISTERED")
    reg.add("s4m_decision_115_biomass_cap_share", "Decision 115: research.s2.industry.biomass_overflow_cap_share = 0.98 is the MAIN setting: in BN, SG and VN the decision-36 rule "
            "(fixed solid-biomass demand above the national potential moved to methane) left the demand exactly equal to the potential (S4L report section 10.1: demand before "
            "the rule 5.05 / 599 / 2.85 x the potential) - a boundary case created by the rule, with a grade-C potential and a 100 % yearly harvest that is not realistic; the "
            "main run caps the fixed biomass demand of the binding countries at 98 % of the potential and moves the remaining 2 % to methane by the same rule (S4L-5 "
            "diagnostic: both scenarios optimal, all gates passed, objective +1.8e-4 / +4.3e-4, binding-country biomass shadow prices 159-309 -> 57-81 EUR/MWh); 1.0 (cap = "
            "potential) is listed as a second-batch sensitivity. Supersedes the same-day decision recorded in s4l6_decision_biomass_zero_slack_kept", "0.98", "share", "B",
            SRC, LOC, INSTRUCTION_SHA, decision_ref="36,55,115", sensitivity_low=None, sensitivity_high=1.0, status="REGISTERED")
    reg.add("s4m_decision_116_pilot_first", "Decision 116: before the second cloud batch a single 365x24h integrated STEPS pilot with profile A (TimeLimit 14,400 s, wall-clock "
            "15,300 s): locally only if the S4M-4 resource condition holds (WSL MemTotal >= 24 GiB and MemAvailable >= 20 GiB, disk >= 20 GB; the S4M-4 check found "
            "MemTotal 10.7 GiB, .wslconfig memory=11GB, Windows physical memory 15.7 GiB -> condition not met, no local pilot), otherwise on the cloud under a separate "
            "authorisation; after the pilot the whole batch. Package rebuilt in S4M-3 with the S4L scripts (process-group kill, receipt check, cgroup quota), TimeLimit / "
            "wall-clock as run parameters GUROBI_TIME_LIMIT_S / WALL_CAP_S with defaults 14,400 / 15,300 s (L23 calibration, CLOUD_RESOURCE_ESTIMATE.md section 21), a "
            "speed probe script (56x3h integrated run on the instance, user authorisation required), second-batch sensitivities = the S4K 14 + numerics.dust_cleanup=off + "
            "s2.industry.biomass_overflow_cap_share=1.0; the S4K package 56d28358 is void", "pilot_then_batch", "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref="116", status="REGISTERED")
    reg.add("s4m_question_source_s4l", "S4M-0: the questions answered by decisions 114-116 are the S4L report section 9 items 1-4 and section 10 (PR #37)", "S4L_REPORT.md", "flag", "B",
            "S4L report sections 9 and 10 (PR #37)", S4L, s4l_sha, decision_ref="114,115,116", status="REFERENCE_ONLY")
    reg.add("s4m_scope_rule", "S4M scope: decisions 114-116 only (settings, builds, S4I review, local 56x3h smoke x3, package rebuild with the S4L scripts, speed probe script, "
            "conditional local pilot, report); other findings go to the report section 'found but not handled' without model change unless a stop condition is met; no cloud "
            "connection, no cloud run", "only_114_116", "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref="114,115,116", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4m_0.csv")
    print("registry fragment s4m_0 written:", len(reg.rows), "rows")


if __name__ == "__main__":
    main()
