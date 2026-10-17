"""S4E-0 data: registry fragment s4e_0 - the user answers (2026-10-17 13:11-13:12 SGT) to the eight decision items of the S4D report section 9.

    python scripts_project/s4e_0_data.py
"""
from __future__ import annotations

from d1_common import REG_DIR, Registry

SCRIPT = "scripts_project/s4e_0_data.py"
INSTRUCTION_SHA = "e5c184c12a91a89ac52e151661cf593a75139396436b95bb75ef0c1cfbb7e9db"
SRC = "S4E instruction v1 2026-10-17 13:20 SGT, section 'answers to S4D report section 9' (user decisions 2026-10-17 13:11-13:12 SGT)"
LOC = "work/p1_step4e_20261017/S4E_CLAUDE_CODE_INSTRUCTION.md"
ANSWERS = [
    ("s4e_answer_lao_destination", "S4D section 9 item 1: Lao transit destination - main: nearest physical coast (same reason as the coastal rule); nearest existing sea port "
     "(author WPI subset) as a sensitivity", "nearest_coast_main;existing_port_sensitivity", "93"),
    ("s4e_answer_lao_mode", "S4D section 9 item 2: Lao transit mode - main: rail (Stolaroff 2021 Table 2); truck as a sensitivity", "rail_main;truck_sensitivity", "93"),
    ("s4e_answer_lao_shipping", "S4D section 9 item 3: after the transit to the nearest coast, Lao CO2 may be shipped into the national stores of other ASEAN countries "
     "(decision 95 c)", "allowed", "95,93,92"),
    ("s4e_answer_storage_cost_basis", "S4D section 9 item 4: one storage cost basis for all geological storage (decision 95 a, S4E-2): PyPSA-Eur default 30 EUR/t for the "
     "national stores, the intra-ASEAN shipping receivers and the extra-ASEAN sink", "unified_30", "95,89"),
    ("s4e_answer_ship_distance", "S4D section 9 item 5: intra-ASEAN shipping distance - main: pair-specific sea-path distance (CO2_SHIP_ROUTES_S4D2.csv, decision 95 b); "
     "the single route factor 1.091 as a comparison switch", "pair_sea_path_main;factor_comparison", "95,92"),
    ("s4e_answer_corridors", "S4D section 9 item 6: complete the adjacent cross-border corridors (decision 94, S4E-1), no new download", "complete", "94,15"),
    ("s4e_answer_la_th_suboptimal", "S4D section 9 item 7: the {LA,TH} smoke ended SUBOPTIMAL - recorded, not re-run now; coalition run rule registered (decision 95 f)",
     "recorded", "95,91"),
    ("s4e_answer_lng_cap", "S4D section 9 item 8: LNG terminal cap sensitivity = no cap, cost only (7,018 EUR/MW/a, decision 95 e); override registered, not run",
     "uncapped_cost_only", "95,17,72"),
    ("coalition_run_rule", "Decision 95 f (coalition studies after delivery): a coalition run that ends non-optimal with profile A is re-run once with profile C "
     "(barrier_numericfocus2); if it is still non-optimal it is marked UNVERIFIED", "rerun_once_profile_C_then_unverified", "95,91"),
]


def main():
    reg = Registry(SCRIPT)
    for pid, desc, val, dec in ANSWERS:
        reg.add(pid, desc, val, "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref=dec, status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4e_0.csv")


if __name__ == "__main__":
    main()
