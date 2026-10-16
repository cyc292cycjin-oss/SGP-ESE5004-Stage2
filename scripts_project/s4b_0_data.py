"""S4B-0 data: decision 70 switch table (model vs PyPSA-Eur v2025.07.0 sector block) and the registry fragment for decisions 70-73.

    python scripts_project/s4b_0_data.py

Writes research_inputs/sector_v5/SECTOR_SWITCHES_VS_PYPSA_EUR.csv (one row per PyPSA-Eur sector key, lines 478-820 of
registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml) and research_inputs/registry_v5/fragments/s4b_0.csv.
Original model values cite the PyPSA-Earth config (config.default.yaml / configs/config.asean.yaml of this repository, which the
research layer composes) or the research decision that set them; "aligned" rows need no reason, every "deviation" row carries a
confirmed decision or an ASEAN-specific reason, and rows without either are flagged USER_DECISION.
"""
from __future__ import annotations

from d1_common import REG_DIR, ROOT, SRC_DIR, Registry, sha256, write_csv

SCRIPT = "scripts_project/s4b_0_data.py"
INSTRUCTION_SHA = "52f1b758e00cfdeb1760c8cd04dbb10d4bfe8bb6bdf8beab3e1da499604dbc51"   # S4B_CLAUDE_CODE_INSTRUCTION.md v1 (user decisions 70-81)
PE_CFG = SRC_DIR / "pypsa_eur_v2025.07.0_config.default.yaml"
PE_PSN = SRC_DIR / "pypsa_eur_v2025.07.0_prepare_sector_network.py"
PE_IMPORT = SRC_DIR / "pypsa_eur_data" / "pypsa_eur_5a87cedd_prepare_sector_network.py"
EARTH = ROOT / "config.default.yaml"; ASEAN_CFG = ROOT / "configs" / "config.asean.yaml"
OUT_DIR = ROOT / "research_inputs" / "sector_v5"

# (PyPSA-Eur key, line(s), PyPSA-Eur value, model config path / component, original model value, new value, components, origin of the original value, status, reason)
A, D, N, U = "aligned", "deviation_confirmed", "not_applicable", "USER_DECISION"
ROWS = [
    ("transport", "479", "true", "research.s2.demand (land transport loads, D1 section 4)", "on", "on", "land transport EV / oil / BEV charger", "S2 demand layer (decision 10, D1)", A, ""),
    ("heating", "480", "true", "research_demand.heat_without_accepted_service", "embedded", "embedded", "none (no space / water heat buses)", "S1 instruction: add_heat / add_residential / add_services not called (sector_adapter.NOT_CALLED)", D,
     "confirmed S1 decision; tropical ASEAN has no space-heating demand class in the accepted demand tables, heat services embedded in electricity (research_demand)"),
    ("biomass", "481", "true", "research.s2.biomass", "on", "on", "national biomass pools + conversions", "S2-3 (decisions 31, 32, 36, 54)", A, ""),
    ("industry", "482", "true", "research.s2.industry", "on", "on", "industry loads (S3-0 routes)", "decisions 55, 61", A, ""),
    ("shipping", "483", "true", "research.s3.shipping", "on", "on", "shipping oil / methanol", "S3-4 (decision 10)", A, ""),
    ("aviation", "484", "true", "research.s2.demand.international_bunkers", "on", "on", "aviation kerosene loads", "decision 10", A, ""),
    ("agriculture", "485", "true", "research.s2.demand", "on", "on", "agriculture machinery / heat loads", "S2 demand (share_agriculture_machinery_* = PyPSA-Eur)", A, ""),
    ("fossil_fuels", "486", "true", "research.s3.gas / imports", "on", "on", "domestic gas production, LNG, oil / coal supply", "S3-1, S3-2", A, ""),
    ("district_heating (and sub-keys)", "487-549", "potential 0.6 ...", "-", "none", "none", "none", "S1 (add_heat not called)", N, "no district-heat buses (tropical climate; S1 decision)"),
    ("heat_pump_sources / cluster_heat_buses / heat_demand_cutout", "550-559", "...", "-", "none", "none", "none", "S1", N, "heat sector not modelled (S1)"),
    ("bev_dsm_* / transport_heating_* / ICE / EV degree factors", "560-567", "...", "-", "none", "none", "none", "S2", N, "BEV DSM off, no climate-dependent transport demand"),
    ("bev_dsm", "568", "true", "research.s2.demand.bev_dsm", "false", "false", "no EV battery DSM store", "S2 (DATA_PENDING: no ASEAN fleet data, number of cars)", D, "confirmed S2 data gap (DATA_PENDING)"),
    ("bev_dsm_availability / bev_energy / bev_charge_* / bev_avail_*", "569-574", "...", "-", "-", "-", "-", "S2", N, "only used with bev_dsm"),
    ("v2g", "575", "true", "-", "not built", "not built", "-", "S2 (needs bev_dsm)", D, "depends on bev_dsm (DATA_PENDING)"),
    ("land_transport_fuel_cell / electric / ice_share (2050)", "576-599", "0 / 1 / 0", "research.s2.demand.land_transport_shares", "pypsa_eur_v2025.07.0", "same", "land transport loads", "D1 section 4 registry share_land_transport_*_2050", A, ""),
    ("transport_electric / fuel_cell / ice_efficiency", "600-602", "53.19 / 30.003 / 16.0712", "registry share_transport_*_efficiency", "same", "same", "land transport loads", "D1 registry", A, ""),
    ("agriculture_machinery_* (shares, efficiencies)", "603-606", "0.5 / 0.5 / 0.7 / 0.3", "registry share_agriculture_machinery_*", "same", "same", "agriculture loads", "D1 registry", A, ""),
    ("MWh_MeOH_per_MWh_H2 / per_tCO2 / per_MWh_e", "607-609", "0.8787 / 4.0321 / 3.6907", "research.s3.ammonia_methanol", "same", "same", "methanolisation", "S3-3 (decision 44)", A, ""),
    ("shipping_hydrogen_liquefaction / shipping shares (2050) / efficiencies", "610-636", "false / H2 0, methanol 1, oil 0 / 0.46, 0.40", "research.s3.shipping", "same", "same", "shipping loads", "S3-4 (registry share_shipping_*_2050)", A, ""),
    ("aviation_demand_factor / HVC_demand_factor", "637-638", "1 / 1", "registry share_aviation_demand_factor / share_HVC_demand_factor", "1 / 1", "1 / 1", "-", "D1 registry", A, ""),
    ("time_dep_hp_cop ... biomass_boiler / overdimension_heat_generators", "639-667", "...", "research S2-5 industrial heat bus", "industrial low-T heat only", "same", "industry heat pump / electric / gas / biomass boiler", "S2-5 (heat sector not modelled, S1)", N, "building heat not modelled; the industrial heat bus uses the same technology rows"),
    ("chp (enable, fuel solid biomass + gas)", "668-673", "true", "-", "not built (biomass EOP power-only + CC)", "same", "biomass EOP / EOP CC", "S2-3", D, "PyPSA-Eur CHPs feed urban central heat buses, which do not exist here (no district heating, S1 decision); power-only biomass EOP kept"),
    ("solar_thermal / solar_cf_correction", "674-675", "true / 0.788", "-", "none", "none", "-", "S1", N, "heat sector not modelled"),
    ("methanation", "676", "true", "research.sector.methanation", "not built (PyPSA-Earth config.default.yaml:1000 is true, but the S1 research recipe build_research_assets.build_fragment did not build it)", "true",
     "Sabatier per node: H2 + captured CO2 -> node gas (decision 64: gas producer credit)", "S1 recipe omission (no decision)", A, "aligned in S4B-0"),
    ("coal_cc", "677", "false", "-", "not built", "not built", "-", "S1 recipe", A, ""),
    ("dac", "678", "true", "research.s2.co2.dac", "true", "true", "DAC per node", "decision 11", A, ""),
    ("co2_vent", "679", "false", "research.s2.co2.vent", "true (S2 implementation; no confirmed decision; vented 0 in every smoke)", "false", "co2 vent links removed", "S2 implementation choice", A, "aligned in S4B-0; true kept as sensitivity"),
    ("heat_vent / marginal_cost_heat_vent", "680-684", "...", "-", "-", "-", "-", "S1", N, "heat sector not modelled"),
    ("allam_cycle_gas", "685", "false", "-", "not built", "not built", "-", "-", A, ""),
    ("hydrogen_fuel_cell", "686", "true", "research.sector.hydrogen_fuel_cell", "true (upstream add_hydrogen)", "true", "H2 Fuel Cell", "S1 adapter", A, ""),
    ("hydrogen_turbine", "687", "true", "research.hydrogen.h2_turbine", "true (PyPSA-Earth config.default.yaml:746)", "true", "H2 turbine (OCGT proxy)", "S1 (decision 42)", A, ""),
    ("SMR", "688", "true", "research.sector.SMR", "true (S1 recipe)", "true", "SMR", "S1", A, ""),
    ("SMR_cc", "689", "true", "research.sector.SMR_cc", "true (S1 recipe)", "true", "SMR CC", "S1", A, ""),
    ("regional_oil_demand", "690", "true", "research.s3.imports.oil_pool", "regional (node oil buses + one ASEAN oil pool)", "same", "oil pool links, node meters with national atmospheres", "decision 18", A, "node-resolved demand with one supply pool = PyPSA-Eur regional demand + EU oil bus"),
    ("regional_coal_demand", "691", "false", "-", "per-node coal supply at one price (unlimited)", "same", "coal external supply", "S2 / decision 18 (coal per node unchanged)", D, "decision 18 keeps coal per node; with unlimited supply at one price the per-node pools are economically equivalent to one bus"),
    ("regional_co2_sequestration_potential", "692-702", "enable true, years 25, offshore only", "research.s2.co2 (national caps)", "national caps = D1 potential / 50 a", "same", "co2 sequestered stores", "decisions 20, 28-30", D, "confirmed decisions (national storage assessments, 50 years)"),
    ("co2_sequestration_potential (2050)", "703-710", "250 Mt/a (Europe)", "registry co2_injection_cap_*", "national caps", "same", "-", "decisions 28-30", D, "confirmed decisions"),
    ("co2_sequestration_cost", "711", "30", "research.s2.co2.sequestration_cost_eur_per_t", "30", "30", "co2 sequestered stores", "S2 (PyPSA-Eur value)", A, ""),
    ("co2_sequestration_lifetime", "712", "50", "research.s2.co2.storage_years", "50", "50", "-", "decisions 28-30", A, ""),
    ("co2_spatial", "713", "true", "-", "per-node co2 stored buses", "same", "-", "S2", A, ""),
    ("co2_network", "714", "true", "research.cross_border.co2 + R5 pipelines", "true (PyPSA-Earth config.asean.yaml:255 false overridden by the research layer)", "true", "CO2 pipelines", "decisions 35, 59", A, ""),
    ("co2_network_cost_factor", "715", "1", "-", "1", "1", "-", "S2", A, ""),
    ("cc_fraction", "716", "0.9", "sector.cc_fraction", "0.9 (PyPSA-Earth config.default.yaml:1003)", "0.9", "all CC links", "S1", A, ""),
    ("hydrogen_underground_storage (+ locations)", "717-721", "true", "research.hydrogen.underground_storage", "false", "false", "-", "S1 (DATA_PENDING: no ASEAN salt-cavern data)", D, "confirmed S1 data gap"),
    ("methanol.regional_methanol_demand", "723", "false", "research.s2.industry.ammonia_methanol_mode", "one ASEAN methanol bus", "same", "ASEAN methanol", "decision 44", A, "false = one bus, as here"),
    ("methanol.methanol_reforming / _cc / methanol_to_kerosene", "724-726", "false", "-", "not built", "not built", "-", "S3-3", A, ""),
    ("methanol.methanol_to_power (ccgt / ccgt_cc / ocgt / allam)", "727-731", "false / false / true / false", "research.s3.ammonia_methanol.methanol_to_power_ocgt", "ocgt only", "same", "OCGT methanol", "S3-3 (decision 44)", A, ""),
    ("methanol.biomass_to_methanol", "732", "true", "research.s3.ammonia_methanol.biomass_to_methanol", "true", "true", "biomass-to-methanol", "S3-3", A, ""),
    ("methanol.biomass_to_methanol_cc", "733", "false", "-", "not built", "not built", "-", "S3-3", A, ""),
    ("ammonia", "734", "true", "research.s2.industry.ammonia_methanol_mode", "regional_buses (Haber-Bosch, cracker, store)", "same", "ASEAN ammonia", "S3-3 (decision 44)", A, ""),
    ("min_part_load_fischer_tropsch", "735", "0.5", "research.sector.min_part_load_fischer_tropsch", "0 (S1 recipe p_min_pu 0; PyPSA-Earth config.default.yaml:1006 0.9 not applied)", "0.5", "Fischer-Tropsch p_min_pu", "S1 recipe (no decision)", A, "aligned in S4B-0"),
    ("min_part_load_methanolisation", "736", "0.3", "research.s3.ammonia_methanol.min_part_load_methanolisation", "0.3", "0.3", "methanolisation", "S3-3", A, ""),
    ("min_part_load_methanation", "737", "0.3", "research.sector.min_part_load_methanation", "- (no Sabatier)", "0.3", "Sabatier p_min_pu", "S4B-0", A, "aligned in S4B-0"),
    ("use_*_waste_heat", "738-743", "0.25 / 1", "-", "none", "none", "-", "S1", N, "waste heat feeds urban central heat buses, which do not exist (no district heating)"),
    ("electricity_transmission_grid", "744", "true", "electric base", "true", "true", "AC lines, DC links", "frozen electric base (S1)", A, ""),
    ("electricity_distribution_grid", "745", "true", "electric base", "true", "true", "electricity distribution grid links", "frozen electric base", A, ""),
    ("electricity_grid_connection", "746", "true", "-", "not applied (PyPSA-Earth config.default.yaml:952 enable_electricity_connection_cost false)", "not applied", "onwind / solar capital cost", "PyPSA-Earth default", U,
     "the decision-50 cost layer technology-data v0.15.0 has no 'electricity grid connection' row (removed in v0.15.0, D1 report section 2); applying it needs a cost row from another layer (v0.13.2) -> user decision"),
    ("transmission_efficiency.DC / electricity distribution grid", "747-755, 762-763", "DC 0.98 static, 0.977 per 1000 km; distribution 0.97", "electric base", "1.0 / 1.0 (frozen electric base)", "same", "DC links, distribution grid links", "frozen electric base (S1)", D,
     "the electric base identity is frozen (S1, ELECTRIC_BASE_SHA); changing link efficiencies changes the base -> listed for the user"),
    ("transmission_efficiency.H2 pipeline / gas pipeline", "756-761", "compression 0.018 / 0.01 MWh_el per MWh per 1000 km (lossless otherwise)", "R5 / S3-1 pipelines", "no compression electricity", "same", "H2 / gas pipelines", "R5 (decision 59), S3-1 (no decision on losses)", U,
     "PyPSA-Eur splits every bidirectional pipeline into two one-way links with a compression port (lossy_bidirectional_links, line 5727) and ties their capacities in the solve; structural change to 242 links -> user decision (impact 0.2-2.3 % of the transported energy as electricity)"),
    ("H2_network", "764", "true", "research.hydrogen.network", "greenfield_along_grid", "same", "H2 pipelines", "decision 59", A, ""),
    ("gas_network", "765", "true", "research.s3.gas", "true", "true", "gas pipelines", "S3-1", A, ""),
    ("H2_retrofit / H2_retrofit_capacity_per_CH4", "766-767", "false / 0.6", "research.hydrogen.gas_network_repurposing", "false", "false", "-", "S1", A, ""),
    ("gas_network_connectivity_upgrade", "768", "1", "s3_layers.add_gas_network", "1", "1", "gas pipeline new <-> links", "S3-1", A, ""),
    ("gas_distribution_grid / cost factor", "769-770", "true / 1.0", "-", "none", "none", "-", "S1 (heat not modelled)", N, "the PyPSA-Eur cost adder applies to building gas boilers, which are not modelled"),
    ("biomass_spatial", "771", "true", "research.s2.biomass", "national pools per country x category, conversion at every node", "same", "biomass Stores", "decision 36, S2-3", D, "confirmed decision (national potentials, no cross-border biomass)"),
    ("biomass_transport", "772", "false", "research.s2.biomass.cross_border", "false", "false", "-", "decision 36", A, ""),
    ("biogas_upgrading", "773", "true", "-", "true", "true", "biogas upgrading", "S2-3", A, ""),
    ("biogas_upgrading_cc", "774", "false", "-", "not built", "not built", "-", "S2-3", A, ""),
    ("conventional_generation", "775-776", "OCGT: gas", "S1 recipe", "OCGT + CCGT on gas (PyPSA-Earth config.default.yaml:1018-1024)", "same", "OCGT, CCGT", "S1", A, "CCGT additionally (PyPSA-Earth default)"),
    ("biomass_to_liquid", "777", "true", "research.sector.biomass_to_liquid", "true (S2 biomass layer)", "true", "BtL", "S2-3", A, "capital cost convention differs (see USER_DECISION row btl_capital_cost)"),
    ("biomass_to_liquid_cc", "778", "false", "-", "not built", "not built", "-", "S2-3", A, ""),
    ("electrobiofuels", "779", "true", "research.sector.electrobiofuels", "not built", "true", "electrobiofuels per node", "S2 omission (no decision)", A, "aligned in S4B-0"),
    ("biosng / biosng_cc / bioH2", "780-782", "false", "-", "not built", "not built", "-", "-", A, ""),
    ("municipal_solid_waste", "783", "false", "-", "not built as a resource (waste incineration links are the S2 territorial plastics release)", "same", "-", "S2 R2 (decision 56)", A, ""),
    ("limit_max_growth", "784-797", "enable false", "-", "not applied", "not applied", "-", "-", A, ""),
    ("enhanced_geothermal", "798-804", "enable false", "-", "not built", "not built", "-", "-", A, ""),
    ("solid_biomass_import", "805-809", "enable false", "-", "none", "none", "-", "decision 36", A, ""),
    ("imports", "810-819", "enable false", "research.s3.imports", "extra-ASEAN imports of oil, ammonia, methanol, FT fuel, liquid H2, LNG", "same", "import generators", "S3-2 (decisions 17, 18, 64)", D, "confirmed decisions (ASEAN imports are part of the study design)"),
    ("btl_capital_cost (formula, add_biomass line 4227-4228)", "4227-4228 (code)", "capital_cost = BtL capital_cost x BtL efficiency (per MW biomass input)", "s2_layers.add_biomass_layer", "BtL fixed (not x efficiency): 252,723 EUR/MW_biomass/a", "unchanged", "BtL", "S2-3 implementation", U,
     "found while aligning electrobiofuels: PyPSA-Eur multiplies by the efficiency (output reading, 113,726 EUR/MW_biomass/a); technology-data v0.15.0 gives the unit EUR/kW_th (input reading = model, 252,723) -> user decision"),
]


def main():
    cfg_sha, psn_sha = sha256(PE_CFG), sha256(PE_PSN)
    cols = ["pypsa_eur_key", "pypsa_eur_lines", "pypsa_eur_value", "model_config_or_component", "model_original", "model_new", "components", "origin_of_original", "status", "reason"]
    table = [dict(zip(cols, r)) for r in ROWS]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(table, OUT_DIR / "SECTOR_SWITCHES_VS_PYPSA_EUR.csv", cols)
    reg = Registry(SCRIPT)
    src = "PyPSA-Eur v2025.07.0 config/config.default.yaml (registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml)"
    reg.add("sector_switch_methanation", "Sabatier per node (H2 + captured CO2 -> node gas bus), PyPSA-Eur default; carbon per decision 64 (gas producer credit, no synthesis port)", "true", "flag", "B", src, "line 676; prepare_sector_network.py 2094-2111", cfg_sha, decision_ref="70")
    reg.add("sector_min_part_load_methanation", "Sabatier minimum part load", 0.3, "p.u.", "B", src, "line 737", cfg_sha, decision_ref="70")
    reg.add("sector_switch_electrobiofuels", "Electrobiofuels per node (solid biomass + H2 -> oil, FT based); origin_neutral: non-fossil pool, no credit", "true", "flag", "B", src, "line 779; prepare_sector_network.py 4263-4304", cfg_sha, decision_ref="70")
    reg.add("sector_min_part_load_fischer_tropsch", "Fischer-Tropsch minimum part load (former model 0)", 0.5, "p.u.", "B", src, "line 735", cfg_sha, decision_ref="70")
    reg.add("sector_switch_co2_vent", "Captured CO2 venting (former model true; no confirmed decision; vented 0 in every smoke); true kept as sensitivity", "false", "flag", "B", src, "line 679", cfg_sha, decision_ref="70")
    reg.add("sector_switch_table", "Model vs PyPSA-Eur sector keys, original and new values, reasons for deviations (research_inputs/sector_v5/SECTOR_SWITCHES_VS_PYPSA_EUR.csv)", len(table), "rows", "B", src, "lines 478-820", sha256(OUT_DIR / "SECTOR_SWITCHES_VS_PYPSA_EUR.csv"), decision_ref="70", status="REFERENCE_ONLY")
    reg.add("sector_deviation_electricity_grid_connection", "PyPSA-Eur electricity_grid_connection true (line 746) not applied: technology-data v0.15.0 (decision 50) has no 'electricity grid connection' row; PyPSA-Earth default false (config.default.yaml:952) -> user decision",
            None, "flag", "C", src, "line 746", cfg_sha, decision_ref="70", status="REFERENCE_ONLY")
    reg.add("sector_deviation_pipeline_compression", "PyPSA-Eur transmission_efficiency compression 0.018 (H2) / 0.01 (gas) MWh_el per MWh per 1000 km (lines 756-761) not applied (lossy bidirectional links needed) -> user decision",
            None, "flag", "C", src, "lines 756-761; prepare_sector_network.py 5727", psn_sha, decision_ref="70", status="REFERENCE_ONLY")
    reg.add("sector_deviation_btl_capital_cost", "BtL capital cost: PyPSA-Eur capital_cost x efficiency (113,726 EUR/MW_biomass/a) vs model fixed (252,723); unchanged -> user decision", None, "flag", "C",
            "PyPSA-Eur v2025.07.0 scripts/prepare_sector_network.py", "lines 4227-4228", psn_sha, decision_ref="70", status="REFERENCE_ONLY")
    reg.add("acceptance_tolerance_basis", "Decision 71 option 1: A1/A2 primal / dual budgets tied to Gurobi FeasibilityTol / OptimalityTol (1e-6) x 10 with row-activity relative terms (net-zero rows: country gross CO2 flow; "
            "biomass pools: capacity); A3, B1, B3 likewise; gap and complementarity <= 10 x BarConvTol (scripts_project/s4b_acceptance.py); S3B R4.4 budgets reported alongside", "solver_tolerances", "flag", "B",
            "S4B instruction S4B-0 item 2; Gurobi parameter documentation (FeasibilityTol, OptimalityTol default 1e-6)", "configs/research/baseline.yaml research.solver.interior", INSTRUCTION_SHA, decision_ref="71")
    reg.add("lng_terminal_expansion_mode_s4b", "Decision 72: LNG terminals may expand up to the decision-17 cap (2.5 x existing; proposed-only sites up to the proposed capacity) at the expansion capital cost; existing_only is now a sensitivity",
            "cap_factor_cost", "flag", "C", "S4B instruction S4B-0 item 3", "configs/research/baseline.yaml research.s3.gas.lng_expansion", sha256(ROOT / "research_inputs/lng_terminals_v5/LNG_IMPORT_TERMINALS_GEM_2025.csv"), decision_ref="72")
    reg.add("lng_terminal_expansion_capex_main", "LNG regasification terminal expansion cost = PyPSA-Eur import-branch terminal_capital_cost shipping-lch4 (code constant, same source as the liquid-H2 terminal); references: "
            "Ulvestad & Overland 2012 converted 8,020 EUR/MW/a (lng_regas_capex_ref_ulvestad_overland_2012), ERIA 2016 storage-based (lng_regas_capex_ref_eria_2016)", 7018.0, "EUR2020/MW/a", "C",
            "PyPSA-Eur import branch 5a87cedd scripts/prepare_sector_network.py", "line 4561", sha256(PE_IMPORT), sensitivity_low=3509.0, sensitivity_high=10527.0, decision_ref="72")
    reg.add("gap_diagnostic_gas_slack", "Decision 73: gap_diagnostic adds a penalised gas source on every node gas bus (reported per country), penalty as the other slacks; main runs unchanged; products labelled GAP_DIAGNOSTIC",
            10000.0, "EUR/MWh", "B", "S4B instruction S4B-0 item 4 (method parameter of decision 73, equal to the decision-49/53 penalties)", "configs/research/baseline.yaml research.s2.gap_diagnostic.penalty_eur_per_mwh_gas", INSTRUCTION_SHA, decision_ref="73")
    reg.add("industry_other_bucket_asean_own_2019", "Other-bucket switch value asean_own_2019: UNSD 2019 own carrier composition of the country's other / construction / mining sub-sectors x industry multiplier, no conversion "
            "(tables *_OTHER_ASEAN_OWN_2019.csv); implemented only, not run in the formal trial", "asean_own_2019", "flag", "C", "S4B instruction S4B-0 item 5 (S3B section 8 item 6)",
            "configs/research/baseline.yaml research.s3.industry.other_bucket", INSTRUCTION_SHA, decision_ref="S3B-8.6", status="SENSITIVITY")
    reg.add("s3b_section8_accepted_items", "User decisions on S3B section 8 recorded in S4B-0: SG pipeline re-export to MY accepted as an optimisation result (no direction limit; regasification cost still DATA_PENDING); "
            "VN biomass overflow to methane kept (synthetic methane may now serve it); R1 bridge multipliers accepted as in S3B", None, "flag", "B", "S4B instruction S4B-0 item 5", "S3B report section 8 items 3, 5, 7", INSTRUCTION_SHA,
            decision_ref="S3B-8", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4b_0.csv")
    print(dict(table_rows=len(table), status_counts={s: sum(1 for r in table if r["status"] == s) for s in {r["status"] for r in table}}, registry_rows=len(reg.rows)))


if __name__ == "__main__":
    main()
