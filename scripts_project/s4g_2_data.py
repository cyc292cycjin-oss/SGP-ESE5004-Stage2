"""S4G-2 data (decision 99 a, b): registry fragment s4g_2 - Thai national store for the Lao transit existing_port sensitivity; apg_plans rule confirmed.

    python scripts_project/s4g_2_data.py
"""
from __future__ import annotations

from d1_common import REG_DIR, Registry

SCRIPT = "scripts_project/s4g_2_data.py"
INSTRUCTION_SHA = "2fd959e9134804a51aecc68b252b2ebe966813e65ed7dabd945ad3953a0d915c"
SRC = "S4G instruction S4G-2 (user decision 2026-10-17 18:49 SGT)"
LOC = "work/p1_step4g_20261017/S4G_CLAUDE_CODE_INSTRUCTION.md"


def main():
    reg = Registry(SCRIPT)
    reg.add("s4g2_lao_th_store", "Decision 99 b: research.co2.lao_transit_th_store = on - only with research.co2.lao_transit_destination = existing_port: LA nodes whose "
            "transit ends at a Thai port (Si Racha, coastal node TH2 3: LA2 1, LA2 2, LA2 3, LA2 5) get '<node> co2 transit to TH store' into 'co2 sequestered TH' "
            "by the rule of decision 97 c (land leg on the link, carrier 'CO2 transit rail', trade class maritime_trade; Thai store cost 30 EUR/t and annual cap on "
            "the store; ledger: freight to LA, storage service at the Thai store dual); main run (nearest_coast) unchanged", "on|off", "flag", "B", SRC, LOC,
            INSTRUCTION_SHA, decision_ref="99,97", status="REFERENCE_ONLY")
    reg.add("s4g2_apg_plans_rule_confirmed", "Decision 99 a: the apg_plans sensitivity rule (s4f1_apg_plan_caps: plan cap = larger of total_MW and the 2040 projection, "
            "#16 incl. merged #5, projects without a number keep the PyPSA-Eur limit) confirmed by the user", "confirmed", "flag", "B", SRC, LOC, INSTRUCTION_SHA,
            decision_ref="99,96", status="REFERENCE_ONLY")
    reg.add("s4g2_sensitivity_readjust_author", "Decision 98 / 99 c: second-batch sensitivity (registered, not packaged, not run): the author's electrical parameters of "
            "the 19 readjusted cross-border AC lines, override network.readjust_impedance=author", "author", "flag", "B", "S4G instruction S4G-4", LOC, INSTRUCTION_SHA,
            decision_ref="98,99", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4g_2.csv")


if __name__ == "__main__":
    main()
