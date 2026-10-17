"""S4C-3 data (decision 88, modifying decision 10): registry fragment s4c_3 - bunker attribution switch, the bunker CO2 account rule, the bunker
demand totals (from the report table of scripts_project/s4c_3_bunker_report.py, registered by SHA) and the config-key correction.

    python scripts_project/s4c_3_data.py --report results_project/s4c/s4c3/report
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from d1_common import REG_DIR, Registry, sha256

SCRIPT = "scripts_project/s4c_3_data.py"
INSTRUCTION_SHA = "e1bad922b036bcb425cb9b77853e5cc4f9ca771c59c90da1a23321b89a1dcdd3"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--report", type=Path, required=True); a = ap.parse_args()
    tab = a.report / "BUNKER_ATTRIBUTION_S4C3_BY_COUNTRY.csv"; tsha = sha256(tab)
    t = pd.read_csv(tab).set_index("country")
    reg = Registry(SCRIPT); cfg = "configs/research/baseline.yaml"
    reg.add("bunker_attribution_main", "Decision 88 (modifying decision 10): international aviation and shipping bunker demand is kept but attributed to no single country - "
            "two ASEAN loads on the regional liquid buses (decision 44; regional in both scenarios): kerosene via a fossil meter from 'ASEAN oil' and a non-fossil twin "
            "from 'ASEAN oil non-fossil', shipping methanol from 'ASEAN methanol'; fossil combustion booked in the separate 'co2 bunkers ASEAN' account",
            "asean_pool", "flag", "B", "S4C instruction S4C-3 items 1-3", f"{cfg} research.bunkers.attribution; scripts_project/s4c_layers.apply_bunker_attribution", f"instruction:{INSTRUCTION_SHA}|table:{tsha}", decision_ref="88,10,44")
    reg.add("bunker_attribution_switch", "research.bunkers.attribution values: asean_pool (main) | bunkering_country (former state, decision 10: loads on the nodes of the bunkering "
            "country, fossil kerosene in its atmosphere, offset by its own removals) | excluded (demand and emissions not bound; drives research.s2.demand.international_bunkers to false)",
            "asean_pool|bunkering_country|excluded", "flag", "B", "S4C instruction S4C-3 item 3", cfg, INSTRUCTION_SHA, decision_ref="88", status="REFERENCE_ONLY")
    reg.add("bunker_account_net_zero", "Bunker CO2 account 'co2 bunkers ASEAN': same Store contract as the national atmospheres; final level <= 0 on its own (hook research_bunker_net_zero, "
            "row research_bunker_co2_limit, gate B1_BUNKERS); every port is an emission port (validate_bunker_account refuses removals), so no country's negative emissions are "
            "transferred (decision 9) and fossil bunker fuel is 0 in any feasible solution - the account is met with non-fossil kerosene (FT, BtL, electrobiofuels, FT import) and methanol",
            0.0, "tCO2/a", "B", "S4C instruction S4C-3 item 2", "scripts_project/s4c_layers.py install_bunker_net_zero", INSTRUCTION_SHA, decision_ref="88,9")
    reg.add("bunker_methanol_carbon_rule", "Limitation / convention: bunker methanol is zero at use under origin_neutral (decision 64) - its carbon is booked at synthesis in the producing "
            "country (fossil-captured CO2) or nets to zero (DAC / biogenic CO2), not in the bunker account; asean_pool refuses producer_credit (the capture credit would stay in the producing country)",
            "origin_neutral_only", "flag", "B", "S3-5 add_fuel_carbon_mode; S4C-3", "scripts_project/s4c_layers.bunker_mode", INSTRUCTION_SHA, decision_ref="88,64", status="REFERENCE_ONLY")
    reg.add("bunker_demand_aviation_2050", "International aviation bunker kerosene 2050 (sum of the D1 rows InternationalAviationBunker over 11 countries; SG 103.2, TH 55.1, MY 29.7, PH 20.1 TWh)",
            float(t.at["ASEAN_TOTAL", "aviation_kerosene_twh"]) * 1e6, "MWh/a", "B", "D1 DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv via the S4C-3 builds", str(tab.name), tsha, decision_ref="88,10", status="REFERENCE_ONLY")
    reg.add("bunker_demand_shipping_methanol_2050", "International shipping bunker methanol 2050 (oil-equivalent D1 rows InternationalShippingBunker x PyPSA-Eur 2050 shares (methanol 1) x "
            "shipping_oil_efficiency / shipping_methanol_efficiency; SG 465.5 TWh of 485.6)", float(t.at["ASEAN_TOTAL", "shipping_methanol_twh"]) * 1e6, "MWh/a", "B",
            "S3-4 shipping layer via the S4C-3 builds", str(tab.name), tsha, decision_ref="88,10", status="REFERENCE_ONLY")
    reg.add("config_cost_layer_registry_key_position", "Correction: configs/research/baseline.yaml research.cost_layer.registry sat under research.corridors from 077ebd0b (S4C-1) to 9a5ea111 "
            "(S4C-2) because the corridors block was inserted above it; no script reads the key (builders use the fixed path research_inputs/registry_v5/DATA_REGISTRY.csv); "
            "full comparisons of the S4C-1 / S4C-2 builds with corrected-config builds: identical static attributes, time series and cost table",
            "moved_back", "flag", "B", "user instruction 2026-10-17 item 2", "results_project/s4c/s4c3/config_key_check", INSTRUCTION_SHA, decision_ref="82,83", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4c_3.csv")
    print(t.round(3).to_string())


if __name__ == "__main__":
    main()
