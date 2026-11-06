"""V4 W08 checklist section 10: registry fragment research_inputs/registry_v5/fragments/v4_w08.csv (every new v4 input with its SHA256 and source;
the fugitive factors of the marketed gas caps used by the build), assembled into DATA_REGISTRY.csv by scripts_project/d1_registry.py.

    PYTHONHASHSEED=0 python scripts_project/v4_registry.py && python scripts_project/d1_registry.py

File rows carry the repository path in source_locator ('file: <path>') and the file's SHA256 in source_sha256 (tests/research/test_v4_registry.py
checks them). Deterministic (no time stamps).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from d1_common import REG_DIR, Registry   # noqa: E402
from v4_common import ASEAN, BIOMASS_DIR, DEMAND_DIR, ROOT, SDMX_DIR, SRC, V4_DIR, sha256   # noqa: E402

SCRIPT = "scripts_project/v4_registry.py"
FFE = "FfE dataset 59 'Normalized Industrial Electrical Load Profiles (Germany)', München: FfE München 2021; licence CC BY 4.0, (c) FfE, eXtremOS Project"
NREL = "NREL 'Manufacturing Thermal Energy Use in 2014' (McMillan 2019), DOI 10.7799/1570008; DOE/NREL/ALLIANCE data licence (credit DOE/NREL/ALLIANCE; keep the notice with copies of the data)"
FILES = [
    ("v4_sdmx_2019_capsule", SRC / "SDMX_2019_CAPSULE.json", "B", "UNSD SDMX 2019 capsule (2,752 records) from the eleven W12 responses (v4_base_sdmx.py = I1 i1_sdmx rules)", "210"),
    ("v4_sdmx_2019_blend_memo", SRC / "SDMX_2019_BLEND_MEMO.csv", "A", "UNSD SDMX 'Of which' biofuel memo quantities (blend rule)", "210"),
    ("v4_sdmx_dictionary_extension", SRC / "SDMX_DICTIONARY_EXTENSION.json", "B", "six SDMX commodity names added to the fuel groups (no frozen factor; SDMX CONVERSION_FACTOR)", "210"),
    ("v4_sdmx_responses_registry_w12", SDMX_DIR / "SDMX_RESPONSES_REGISTRY_W12.csv", "A", "W12 retrieval rows of the eleven responses (url, UTC, bytes, SHA256)", "210"),
    ("v4_ncv_exceptions", DEMAND_DIR / "NCV_EXCEPTIONS.csv", "B", "NCV exceptions of the SDMX base: ID hard coal 20.29, ID coke oven coke 28.20 GJ/t", "207, 210"),
    ("v4_d1_base_2019_sdmx", V4_DIR / "D1_BASE2019_SDMX.csv", "B", "v4 seed: D1 base rows of the SDMX base (S5p)", "210"),
    ("v4_d1_base_2019_v31_rebuild", V4_DIR / "D1_BASE2019_V31_REBUILD.csv", "B", "v3.1 base at full precision (reference of the seed edits)", "210"),
    ("v4_household_gasoline_2019", V4_DIR / "HOUSEHOLD_GASOLINE_2019.csv", "A", "UNSD SDMX 2019 households motor gasoline (ID 197.03 TWh)", "210"),
    ("v4_industry_cells_2019", V4_DIR / "SDMX_INDUSTRY_CELLS_2019.csv", "B", "SDMX industry records by sub-row (cache source)", "210"),
    ("v4_residue_records_2019", V4_DIR / "RESIDUE_RECORDS_2019.csv", "B", "self-produced (a) / purchased (c) residue records", "210"),
    ("v4_residue_classes", V4_DIR / "RESIDUE_CLASSES.csv", "C", "residue classification rules (I2; n.e.s. rice husk reading INFERENCE)", "210, 211"),
    ("v4_national_balance_biomass_coverage", V4_DIR / "NATIONAL_BALANCE_BIOMASS_COVERAGE.csv", "C", "national balance coverage of self-produced residues (ID excluded, others as UNSD: MISSING T02)", "210"),
    ("v4_fuelwood_outside_balance", V4_DIR / "FUELWOOD_OUTSIDE_BALANCE.csv", "B", "ID fuelwood 2010-2017 mean 29,510 thousand m3 (outside the anchor)", "206, 210"),
    ("v4_industry_cache", V4_DIR / "industry_cache_v4.json", "B", "v4 industry sub-sector cache (main switch set)", "210, 211"),
    ("v4_anchor_v3_sector_factors", DEMAND_DIR / "DEMAND_ANCHOR_V3_SECTOR_FACTORS.csv", "B", "v3 RAS sector factors (IId)", "210, 211"),
    ("v4_anchor_v3_frozen", DEMAND_DIR / "DEMAND_ANCHOR_V3_FROZEN.csv", "B", "frozen v3 country x sector anchors (IIb)", "211"),
    ("v4_captive_coal_2019", V4_DIR / "CAPTIVE_COAL_2019.csv", "C", "captive coal option (b): ID central, MM low, PH paper / refinery (tonnes x NCV)", "204, 208"),
    ("v4_cement_usgs_2019", V4_DIR / "CEMENT_USGS_2019.csv", "B", "USGS 2019 cement tonnes (grinding electricity), BN EDGAR 2.A.1 = 0", "210"),
    ("v4_pulp_paper_faostat", V4_DIR / "PULP_PAPER_FAOSTAT_V4.csv", "B", "FAOSTAT pulp / paper leaf items 2019 and 2050 (session growth rule)", "206, 208"),
    ("v4_hvc_plants", V4_DIR / "HVC_PLANTS_V4.csv", "C", "HVC tonnes 2019 / 2050 / new plants (utilisation 0.85)", "208, 210"),
    ("v4_methanol_plants", V4_DIR / "METHANOL_PLANTS_V4.csv", "C", "methanol plants (Labuan, Kaltim, Brunei Methanol, Sarawak Petchem)", "210"),
    ("v4_product_derived_inputs", V4_DIR / "PRODUCT_DERIVED_INPUTS_V4.csv", "C", "glass, alumina, copper, lime, MY methanol energy (session derivations)", "208"),
    ("v4_my_ammonia_fuel_duplicate", V4_DIR / "MY_AMMONIA_FUEL_DUPLICATE.csv", "C", "MY ammonia fuel duplicate (mid)", "208"),
    ("v4_vn_hybrid_electricity_rows", V4_DIR / "VN_HYBRID_ELECTRICITY_ROWS.csv", "C", "VN iron / steel and chemicals electricity back-cast 2019", "208"),
    ("v4_node_shares_sessions", V4_DIR / "NODE_SHARES_SESSIONS_V4.csv", "C", "W07 session node shares (share_v4)", "208"),
    ("v4_biomass_potential_2050", BIOMASS_DIR / "BIOMASS_POTENTIAL_2050_V4.csv", "C", "solid-biomass potential after F3 (bagasse R2) and F4 (in-mill self-use)", "209, 210"),
    ("v4_biomass_potential_adjustment", BIOMASS_DIR / "BIOMASS_POTENTIAL_ADJ_V4.csv", "C", "F3 / F4 adjustment by country and category", "209, 210"),
    ("v4_w12_bagasse_supply_overestimate", BIOMASS_DIR / "W12_BAGASSE_SUPPLY_OVERESTIMATE.csv", "B", "W12 bagasse supply over-estimate (R2)", "209"),
    ("v4_w12_unsd_bagasse_2019", BIOMASS_DIR / "W12_UNSD_BAGASSE_2019.csv", "A", "UNSD 2019 bagasse production / consumption (W12)", "209"),
    ("v4_w12_unsd_gas_2019", ROOT / "research_inputs/gas_v5/W12_UNSD_GAS_2019.csv", "A", "UNSD 2019 natural gas gross / marketed production (W12, UNdata export)", "209"),
    ("v4_gas_production_caps_2050", ROOT / "research_inputs/gas_v5/GAS_PRODUCTION_CAPS_2050_V4.csv", "B", "domestic gas caps on marketed production", "209"),
    ("v4_industry_profiles_8760", V4_DIR / "INDUSTRY_PROFILES_8760.parquet", "B", f"G5 hourly shapes (MAIN and sensitivities). Electricity: {FFE}. Heat: {NREL}", "G5, 209"),
    ("v4_industry_profile_index", V4_DIR / "INDUSTRY_PROFILE_INDEX.csv", "B", "G5 curve index (variant x key x etype x zone)", "G5"),
    ("v4_industry_profile_mapping", V4_DIR / "INDUSTRY_PROFILE_MAPPING.csv", "B", "G5 sub-sector -> shape mapping and reasons", "G5"),
]


def main():
    reg = Registry(SCRIPT)
    T = pd.read_csv(SDMX_DIR / "SDMX_RESPONSES_REGISTRY_W12.csv").set_index("path")
    import v4_base_sdmx as B
    R = B.responses().set_index("country")
    for cc in ASEAN:
        p = SDMX_DIR / f"{cc}_2019_all.xml"; r = T.loc[f"sdmx/{p.name}"]
        reg.add(f"v4_sdmx_2019_response_{cc}", f"UNSD SDMX DF_UNDATA_ENERGY 2019 response {cc} (all commodities / transactions); Prepared {R.at[cc, 'prepared']}; retrieved {r.retrieved_utc}",
                int(p.stat().st_size), "bytes", "A", r.url, f"file: {p.relative_to(ROOT)}", sha256(p), country=cc, decision_ref="210", status="REFERENCE_ONLY")
    for pid, p, tier, desc, dec in FILES:
        reg.add(pid, desc, int(p.stat().st_size), "bytes", tier, "V4 W08 (W07 / I1 / I2 / W12 / G5 deliverables; see the table's source column)", f"file: {p.relative_to(ROOT)}",
                sha256(p), decision_ref=dec, status="REFERENCE_ONLY")
    e = pd.read_csv(DEMAND_DIR / "NCV_EXCEPTIONS.csv", dtype=str)
    for r in e.itertuples():
        reg.add(f"v4_ncv_{r.country}_{r.commodity.lower().replace(' ', '_').replace('-', '_')}", f"{r.country} {r.commodity} NCV of the SDMX base ({r.basis})", float(r.gj_per_unit), "GJ/t", "B",
                "decisions 207 / 210", f"file: {(DEMAND_DIR / 'NCV_EXCEPTIONS.csv').relative_to(ROOT)}", sha256(DEMAND_DIR / "NCV_EXCEPTIONS.csv"), country=r.country, decision_ref=r.decision)
    reg.add("v4_id_fuelwood_mean_2010_2017_km3", "ID industrial fuelwood outside the national balance: UNSD 2010-2017 mean (decision 206; 210 item 4 b)", 29510.0, "thousand m3", "B",
            "UNSD fuelwood n.e.s. industry 2010-2017 (S2 section 3; G0 step 8)", f"file: {(V4_DIR / 'FUELWOOD_OUTSIDE_BALANCE.csv').relative_to(ROOT)}", sha256(V4_DIR / "FUELWOOD_OUTSIDE_BALANCE.csv"),
            country="ID", decision_ref="206, 210")
    from v4_biomass_potential import PKS_IN_MILL_SHARE
    reg.add("v4_pks_in_mill_share", "share of palm kernel shells burned in the mills (removed from the potential): W08 constant, since V4 D1 the fallback of the per-country table PALM_MILL_SELF_USE.csv (registry v4_palm_mill_*; T03)", PKS_IN_MILL_SHARE, "share", "C",
            "I2 central assumption (grade D)", "scripts_project/v4_biomass_potential.py PKS_IN_MILL_SHARE", sha256(HERE / "v4_biomass_potential.py"), sensitivity_low=0.0, sensitivity_high=1.0, decision_ref="209, 210")
    reg.add("v4_biomass_overflow_cap_share", "overflow cap = share x solid-biomass potential (W12 F7; 1 % margin of the pool)", 0.99, "share", "C", "decision 209 F7",
            "configs/research/baseline.yaml research.demand.v4.bio_cap_share", sha256(ROOT / "configs/research/baseline.yaml"), sensitivity_low=0.98, sensitivity_high=1.0, decision_ref="209")
    g = pd.read_csv(ROOT / "research_inputs/gas_v5/GAS_PRODUCTION_CAPS_2050_V4.csv"); f = pd.read_csv(ROOT / "research_inputs/gas_v5/FUGITIVE_FACTORS_V4.csv").set_index("country")
    gsha = sha256(ROOT / "research_inputs/gas_v5/W12_UNSD_GAS_2019.csv"); fsha = sha256(ROOT / "research_inputs/gas_v5/FUGITIVE_FACTORS_V4.csv")
    for r in g.itertuples():
        reg.add(f"v4_gas_production_cap_2050_{r.country}", f"{r.country} annual domestic gas cap = UNSD 2019 marketed production x 0.90 / 0.0036 (W12 F1)", float(r.cap_mwh_per_year), "MWh/a", "B",
                "UNSD energy statistics 2019 (UNdata export, W12 table)", "file: research_inputs/gas_v5/W12_UNSD_GAS_2019.csv marketed_tj", gsha, country=r.country, decision_ref="209",
                status="REGISTERED" if r.cap_mwh_per_year > 0 else "SOURCE_ZERO")
        if r.country in f.index and pd.notna(f.at[r.country, "factor_t_per_mwh"]):
            reg.add(r.fugitive_factor_id, f"{r.country} fugitive CO2 per MWh of domestic oil + marketed gas production = EDGAR 2019 1.B.2 {f.at[r.country, 'edgar_1B2_t']:,.0f} t / "
                    f"(oil {f.at[r.country, 'oil_cap_mwh']:,.0f} + gas {f.at[r.country, 'gas_cap_marketed_mwh']:,.0f} MWh)", float(f.at[r.country, "factor_t_per_mwh"]), "tCO2/MWh_production", "B",
                    "EDGAR 2025 1.B.2 / UNSD 2019 production (oil cap + marketed gas cap)", "file: research_inputs/gas_v5/FUGITIVE_FACTORS_V4.csv", fsha, country=r.country, decision_ref="209")
    out = REG_DIR / "fragments" / "v4_w08.csv"
    reg.write(out)
    print(out, len(reg.rows))


if __name__ == "__main__":
    main()
