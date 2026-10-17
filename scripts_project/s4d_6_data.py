"""S4D-6 data: registry fragment s4d_6 - the first-batch sensitivities registered (not packaged, not run) with the build overrides they need
(S4D instruction S4D-6 item 2; answers to S4C section 8 items 2 and 8), and the cloud package settings (profile A, ledger exports).

    python scripts_project/s4d_6_data.py
"""
from __future__ import annotations

from d1_common import REG_DIR, Registry

SCRIPT = "scripts_project/s4d_6_data.py"
INSTRUCTION_SHA = "a35fa7d52c0d645830562e57fb242563b864994682eeb1ce6a2a8d59f73b2586"
SRC = "S4D instruction S4D-6 item 2; answers to S4C section 8"
LOC = "work/p1_step4d_20261017/S4D_CLAUDE_CODE_INSTRUCTION.md"


def main():
    reg = Registry(SCRIPT)
    reg.add("s4d6_sensitivity_extra_asean_cost", "First-batch sensitivity (registered, not packaged, not run): extra-ASEAN CO2 storage unit cost -50 % / +50 % (registry "
            "co2_extra_asean_storage_cost 40.75 EUR2020/t), integrated and disconnected; build override co2.extra_asean_cost_scale=0.5 | 1.5 (key absent = 1.0; "
            "s4d_layers.extra_asean_cost_scale); at +50 % (61.1 EUR/t) intra-ASEAN shipping (>= 41.42 EUR/t) becomes competitive", "0.5|1.5", "flag", "B", SRC, LOC, INSTRUCTION_SHA,
            decision_ref="89,92", status="REFERENCE_ONLY")
    reg.add("s4d6_sensitivity_ship_route_factor", "First-batch sensitivity (registered, not packaged, not run): CO2 shipping route factor -25 % / +25 % (registry co2_ship_route_factor "
            "1.091), integrated and disconnected; build override co2.ship_route_factor_scale=0.75 | 1.25 (checked on the S4D-2 build integrated_route125)", "0.75|1.25", "flag",
            "B", SRC, LOC, INSTRUCTION_SHA, decision_ref="92", status="REFERENCE_ONLY")
    reg.add("s4d6_sensitivity_lng_cap", "First-batch sensitivity (registered, not packaged, not run): LNG terminal expansion cap (decision 17: 2.5 x existing per terminal node; binding "
            "in the S4C smoke), integrated and disconnected; build override s3.gas.lng_cap_factor=<value>; the value is a user decision (S4C section 8 item 8)",
            "user_value", "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref="17,72", status="REFERENCE_ONLY")
    reg.add("s4d6_cloud_package", "S4D cloud package: three runs (integrated STEPS, disconnected STEPS, integrated NZE) at the S4D final commit, run command "
            "'run_365x24h.sh --solver-profile formal_barrier' (profile A, user decision; the flag stays required with no default), exports incl. COUNTRY_COST_LEDGER.csv, "
            "COUNTRY_COST_LEDGER_DETAIL.csv, LEDGER_IDENTITY.json, NODAL_PRICES.csv; disconnected gap diagnostic packaged, run only if the disconnected main ends non-optimal",
            "profile_A", "flag", "B", "S4D instruction S4D-6 items 1, 3", "research/06_scope_redesign/p1_step4d_20261017/cloud_package", INSTRUCTION_SHA, decision_ref="84,91",
            status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4d_6.csv")


if __name__ == "__main__":
    main()
