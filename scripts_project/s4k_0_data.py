"""S4K-0 data: registry fragment s4k_0 - decision 108 (AC lines: linear loss proxy instead of the PyPSA piecewise tangents, confirmed 2026-10-18
22:37 SGT) and the handling of the S4J report section 12 items 2 and 3, and the S4K scope rule (only decision 108).

    python scripts_project/s4k_0_data.py
"""
from __future__ import annotations

from d1_common import REG_DIR, ROOT, Registry, sha256

SCRIPT = "scripts_project/s4k_0_data.py"
INSTRUCTION_SHA = "a803f1653736640f1358659b156e6d9dbf7c72be61b9455863f793dea75825d5"
SRC = "S4K instruction v1 2026-10-18 22:45 SGT, sections S4K-0 and S4K-1 (user decision 108 confirmed 2026-10-18 22:37 SGT)"
LOC = "work/p1_step4k_20261018/S4K_CLAUDE_CODE_INSTRUCTION.md"
S4J = "research/06_scope_redesign/p1_step4j_20261018/S4J_REPORT.md"
S4J_SRC = "S4J report sections 8.6, 11 (items 3, 8, 9) and 12 (PR #34)"
ANSWERS = [
    ("s4k_answer_108_ac_loss_proxy", "S4J section 12 item 1 (PyPSA piecewise tangent line losses with tangent points on s_nom_max and a resistance that does not fall "
     "with the extension: zero loss below 3.5-13 GW, 16 lines built exactly to the zero-loss limit in the S4J smoke) -> decision 108: every AC line (stock and "
     "candidates, domestic and cross-border, both scenarios) gets a linear loss proxy l >= lambda * p, l >= -lambda * p, l <= lambda * s_max_pu * s_nom, half of "
     "the loss withdrawn at each end (PyPSA structure); lambda = sqrt(3) * I_ref * R / v_nom with R = r_per_km * L of one circuit and I_ref = alpha * s_max_pu * "
     "i_nom, main alpha = 0.5; PyPSA transmission_losses = 0 at solve time; switches research.network.ac_losses: linear_proxy | pypsa_tangent | none and "
     "research.network.ac_loss_reference_loading: 0.5 (sensitivity 1.0); DC and pipeline losses unchanged (S4J-2) (S4K-1)", "linear_proxy;alpha_0.5", "108"),
    ("s4k_answer_s4j12_2_b2b_disconnected", "S4J section 12 item 2 (the two TH-MY converter B2B in the disconnected scenario) -> keep the S4H state (domestic links, "
     "2,000 MW, zero flow in the S4J smoke); no model change", "keep_s4h_state", "107,108"),
    ("s4k_answer_s4j12_3_th_my_switch", "S4J section 12 item 3 (research.network.th_my_hvdc = s4h as a second-batch sensitivity) -> keep the switch only, not "
     "listed in the second batch", "switch_only", "107,108"),
    ("s4k_ledger_s4i_entry", "S4K-0: the project ledger research/STAGE2_PROJECT_LEDGER.md gets the S4I entry (pre-cloud static audit, PR #33) that the S4I "
     "delivery did not write (S4J report section 11 item 10)", "added", "103,108"),
    ("s4k_scope_rule", "S4K scope: only decision 108 is implemented; other findings go to the report section 'found but not handled' without model change "
     "unless a stop condition is met; after S4K the model state is the version of the first formal runs unless the user decides otherwise", "only_108", "108"),
]


def main():
    reg = Registry(SCRIPT)
    for pid, desc, val, dec in ANSWERS:   # the answers are in the S4K instruction (S4K-0); the S4J report is the question
        reg.add(pid, desc, val, "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref=dec, status="REFERENCE_ONLY")
    s4j_sha = sha256(ROOT / S4J)
    reg.add("s4k_question_source_s4j", "S4K-0: the questions answered here are the S4J report section 12 items 1-3 (and section 11 item 10)", "S4J_REPORT.md", "flag", "B",
            S4J_SRC, S4J, s4j_sha, decision_ref="108", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4k_0.csv")
    print("registry fragment s4k_0 written:", len(ANSWERS) + 1, "rows")


if __name__ == "__main__":
    main()
