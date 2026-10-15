"""S3-5 (decision 64): registry fragment for the fuel carbon attribution modes and the PyPSA-Eur fuel-origin check.

PyPSA-Eur v2025.07.0 does not track the origin of liquid fuels: one oil bus (add_carrier_buses) and one methanol bus; every consumer link books
the fossil CO2 intensity in the single European atmosphere (e.g. shipping oil efficiency2 = costs oil CO2 intensity, lines 5261-5270; shipping
methanol 1/MWh_MeOH_per_tCO2, lines 5218-5227; industry methanol 4617-4626); producers credit the carbon: Fischer-Tropsch and methanolisation take
CO2 from the captured-CO2 bus 'co2 stored' (lines 4628-4645), BtL and biomass-to-methanol book -CO2 intensity of biomass + CO2 stored to the
atmosphere (add_biomass_to_methanol 983-1002), biogas upgrading -CO2 intensity of gas, Sabatier takes co2 stored. With a single atmosphere the
producer credit and the consumer emission cancel; with 11 national atmospheres they do not, which is why decision 64 defines origin_neutral.

    python scripts_project/s3_5_fuel_carbon_data.py
"""
from __future__ import annotations

from d1_common import REG_DIR, ROOT, SRC_DIR, Registry, sha256, write_json

SCRIPT = "scripts_project/s3_5_fuel_carbon_data.py"
PE_SCRIPT = SRC_DIR / "pypsa_eur_v2025.07.0_prepare_sector_network.py"
TD = ROOT / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv"


def main():
    pe_sha, td_sha = sha256(PE_SCRIPT), sha256(TD)
    reg = Registry(SCRIPT)
    reg.add("fuel_carbon_mode", "Main fuel carbon attribution = origin_neutral (decision 64): non-fossil liquid fuels zero at combustion and no producer credit; fossil-captured synfuels booked in the producer atmosphere at synthesis; imported green fuels zero; "
            "sensitivity producer_credit = S2 behaviour (switch research.s3.fuel_carbon_mode)", "origin_neutral", "flag", "B", "S3 instruction S3-5", "configs/research/baseline.yaml research.s3.fuel_carbon_mode", pe_sha, decision_ref="64")
    reg.add("fuel_carbon_liquid_buses", "Oil split into a fossil pool (ASEAN oil + node oil buses, consumer meters with the fossil EF) and a non-fossil pool (ASEAN oil non-fossil + node 'oil non-fossil' buses fed by Fischer-Tropsch, BtL and FT imports, twin consumer meters without atmosphere port); "
            "methanol: no fossil production route in the 2050 technology set, so the single regional methanol bus is the non-fossil bus", "fossil|non-fossil", "structure", "B", "s3_layers.add_fuel_carbon_mode", "S3-5", pe_sha, decision_ref="64")
    reg.add("fuel_carbon_synthesis_port", "Synthesis books the output carbon in the producer atmosphere: Fischer-Tropsch +0.2571 x 0.754 tCO2 per MWh_H2, methanolisation +0.8787/4.0321 = 0.2179 tCO2 per MWh_H2; BtL and biomass-to-methanol production credits removed. "
            "Equivalent to tracking the origin of co2 stored: fossil-captured CO2 is booked once at the producer, DAC/biogenic capture credits are offset by the same amount at synthesis (INFERENCE: identical port for both origins, so no buffer split is needed)",
            "+carbon_at_synthesis", "method", "B", "s3_layers.add_fuel_carbon_mode", "S3-5", td_sha, decision_ref="64")
    reg.add("fuel_carbon_gas_asymmetry", "Gas remains a network carrier with the PyPSA-Eur treatment: biogas upgrading credits -0.198 tCO2/MWh at the producer (97 links), gas consumers book the fossil EF; Sabatier/methanation is not active in the S3 network (upstream option methanation false); the origin of pipeline gas is not traceable (asymmetry stated)",
            "producer_credit_for_gas", "method", "B", "PyPSA-Eur v2025.07.0 prepare_sector_network.py", "biogas upgrading / Sabatier links", pe_sha, decision_ref="64")
    reg.add("fuel_carbon_pypsa_eur_origin_tracking", "PyPSA-Eur v2025.07.0 has no fuel-origin tracking: single oil and methanol buses, consumers book the fossil EF (shipping oil 5261-5270, shipping methanol 5218-5227, industry methanol 4617-4626), producers credit (FT/methanolisation from co2 stored 4628-4645, "
            "biomass-to-methanol 983-1002, biogas upgrading, Sabatier); with one European atmosphere the credit and the emission cancel, with 11 national atmospheres they do not (decision 64)", "none", "finding", "B",
            "PyPSA-Eur v2025.07.0 prepare_sector_network.py", "lines cited", pe_sha, decision_ref="64", status="REFERENCE_ONLY")
    reg.add("fuel_carbon_imports_zero", "Imported green carriers (FT fuel on ASEAN oil non-fossil, methanol on ASEAN methanol, ammonia, liquid H2) carry no CO2 port and their consumers book zero (origin_neutral); producer_credit caps imported methanol at 0 (no regional atmosphere to credit)",
            0.0, "tCO2/MWh", "B", "s3_layers.add_imports / add_fuel_carbon_mode", "S3-2 / S3-5", pe_sha, decision_ref="64")
    reg.add("fuel_carbon_sg_bunker_example", "Singapore international bunker methanol 465.5 TWh/a: origin_neutral books 0 in SG (carbon booked at the producing node's synthesis or zero for imports); producer_credit would book 465.5 TWh x 0.2482 = 115.5 MtCO2/a in SG, "
            "more than SG's structural unavoidable CO2 (54.9 Mt) with no domestic storage", 115.5e6, "tCO2/a (producer_credit case)", "B", "s2_layers shipping loads x technology-data methanol CO2 intensity", "S3_REPORT.md section 6", td_sha, decision_ref="64", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "fuel_carbon.csv")
    write_json(dict(script=SCRIPT, sources=dict(pe_script=pe_sha, technology_data=td_sha)), REG_DIR / "FUEL_CARBON_EVIDENCE.json")
    print("fragment written")


if __name__ == "__main__":
    main()
