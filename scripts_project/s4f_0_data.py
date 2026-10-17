"""S4F-0 data: registry fragment s4f_0 - the user answers (2026-10-17 14:43 SGT) to the seven decision items of the S4E report section 7.

    python scripts_project/s4f_0_data.py
"""
from __future__ import annotations

from d1_common import REG_DIR, Registry

SCRIPT = "scripts_project/s4f_0_data.py"
INSTRUCTION_SHA = "28d7458d47e282df6aaf5fa324e3772b886a67f9b178dd728696c5eac7216f03"
SRC = "S4F instruction v1 2026-10-17 14:50 SGT, section 'answers to S4E report section 7' (user decisions 2026-10-17 14:43 SGT)"
LOC = "work/p1_step4f_20261017/S4F_CLAUDE_CODE_INSTRUCTION.md"
ANSWERS = [
    ("s4f_answer_corridor_caps", "S4E section 7 item 1: capacity of the new candidate corridors - main: the PyPSA-Eur individual line / link extension limit "
     "(decision 96, S4F-1); APG / AIMS planned or projected capacities as a conservative sensitivity", "pypsa_eur_main;apg_plans_sensitivity", "96,94"),
    ("s4f_answer_th_my_stock", "S4E section 7 item 2: TH-MY stock - remove the four suspected duplicate HVDC links (OSM 250878579, 491.4 MW each) and align the 2025 "
     "TH-MY total to the APG 380 MW (decision 97 a, S4F-2)", "remove_duplicates_align_apg_380", "97,15"),
    ("s4f_answer_apg4_endpoint", "S4E section 7 item 3: APG #4 Indonesian endpoint moved to ID_Sumatra3 3 (Pekanbaru) (decision 97 b); #16 keeps the Batam end",
     "ID_Sumatra3 3", "97,94"),
    ("s4f_answer_coalition_scope", "S4E section 7 item 4: coalition study scope - decided after delivery together with item 14 by the senior colleague "
     "(decision 97 f); not done in S4F", "deferred_with_item_14", "97,91,14"),
    ("s4f_answer_lao_to_vn_store", "S4E section 7 item 5: Lao CO2 may enter the Vietnamese national store after the rail transit to the Vietnamese coast "
     "(decision 97 c): land leg + VN storage 30 EUR/t, inside the VN annual injection limit, trade (not cross-border network), both scenarios", "allowed", "97,95,93"),
    ("s4f_answer_sg_vn_kh", "S4E section 7 item 6: SG-VN and SG-KH (other initiatives) stay out of the main run; second-batch sensitivity (decision 97 d)",
     "second_batch_sensitivity", "97,94"),
    ("s4f_answer_ph_value", "S4E section 7 item 7: negative PH interconnection value and the separation of corridor effects - no first-batch cloud run; analysed "
     "from the country ledger detail of the formal results, second batch if needed (decision 97 e)", "ledger_analysis_after_formal_results", "97,91"),
]


def main():
    reg = Registry(SCRIPT)
    for pid, desc, val, dec in ANSWERS:
        reg.add(pid, desc, val, "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref=dec, status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4f_0.csv")


if __name__ == "__main__":
    main()
