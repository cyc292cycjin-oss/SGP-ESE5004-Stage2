"""V5 X20 (decisions 241, 244, 246, 251): registry rows of the v5 input revisions, assembled into DATA_REGISTRY.csv by scripts_project/d1_registry.py.

    PYTHONHASHSEED=0 python scripts_project/v5_x20_registry.py && python scripts_project/d1_registry.py

  fragments/v5_x20.csv              new rows: switch rules, the v5 input tables (file rows with SHA256), values (alpha, potentials, fractions, NEU gas, stock).
  fragments/v5_x20_corrections.csv  description corrections of existing rows (values unchanged; X20_SPEC.md 1.1 (d), 1.4, 1.5, 1.6, 1.11, 1.12, 1.14, 1.17),
                                    written against the registry assembled with the corrections before this one (idempotent).
v4 rows whose value a v5 switch changes keep their value (a v5-off build must stay the 26c2e47d build); the v5 value is a new v5_* row.
Nothing is solved.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import d1_registry as DR   # noqa: E402
from d1_common import REG_DIR, Registry   # noqa: E402
from v4_common import ROOT, sha256   # noqa: E402

SCRIPT = "scripts_project/v5_x20_registry.py"
STEP = "research/06_scope_redesign/p1_v5_x20_20261111"
COLUMNS = ["param_id", "description", "value", "unit", "country", "node", "tier", "source", "source_locator", "source_sha256", "derivation_script",
           "sensitivity_low", "sensitivity_high", "decision_ref", "status"]
RV = ROOT / "research_inputs/renewable_v5"; FV = ROOT / "research_inputs/fleet_v5"; CV = ROOT / "research_inputs/corridors"
SPEC = ROOT / STEP / "X20_SPEC.md"; ADD = ROOT / STEP / "X20_SPEC_ADDENDUM_246.md"
PE_CFG = ROOT / "research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml"
PE_PSN = ROOT / "research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_prepare_sector_network.py"
NGCP_SHA = "eb39b15e4f60341d9aabd3f2d2bf597706052e3bee874afcf39130167c675262"
COUNTRIES = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]


def rel(p: Path) -> str:
    return str(Path(p).relative_to(ROOT))


def file_row(r: Registry, pid: str, p: Path, desc: str, tier: str, dec: str) -> None:
    r.add(pid, desc, int(p.stat().st_size), "bytes", tier, f"V5 X20 ({STEP})", f"file: {rel(p)}", sha256(p), decision_ref=dec, status="REFERENCE_ONLY")


def rule_row(r: Registry, pid: str, desc: str, value: str, src: str, loc: str, sha: str, dec: str, tier: str = "B", status: str = "REGISTERED") -> None:
    r.add(pid, desc, value, "rule", tier, src, loc, sha, decision_ref=dec, status=status)


def new_rows() -> Registry:
    import v5_common as V5
    r = Registry(SCRIPT); spec = sha256(SPEC); add = sha256(ADD)
    rule_row(r, "v5_switch_set", "research.demand.v5 (configs/research/baseline.yaml): enabled false = every rule at its 26c2e47d (v4 W14) behaviour; enabled true = the v5 main set "
             "(scripts_project/v5_common.py V5_MAIN); value = SHA256 of the v5 main switch set", V5.switch_sha(V5.V5_MAIN), "X20_SPEC.md section 0.1; decisions 241, 244, 246",
             rel(HERE / "v5_common.py"), sha256(HERE / "v5_common.py"), "241,244,246")
    # ---- 1-1 onshore wind
    file_row(r, "v5_onwind_gwa_cell_factor", RV / "WIND_GWA_CELL_FACTOR_V5.nc", "GWA v4 ws100 land mean / ERA5 2013 time-mean wnd100m per cutout cell (1 below 50 % coverage; clipped [0.5, 3]; "
             "4,048 cells used, 1 clipped); profiles of calibrated_gwa_v5 (scripts_project/v5_wind_gwa.py)", "B", "241,246")
    file_row(r, "v5_onwind_gwa_farm_point_factor", RV / "WIND_GWA_FARM_POINT_FACTOR_V5.csv", "GWA v4 ws100 at the 156 calibration farm points / ERA5 cell mean; calibration only (decision 246 Q1 (b))", "B", "246")
    rule_row(r, "v5_onwind_calibration_switch", "research.demand.v5.onwind_calibration: gwa_cell_ember (v5 main: ERA5 x GWA cell factor x alpha calibrated on Ember at the GWA-corrected farm "
             "points, Q1 (b); profile variant calibrated_gwa_v5) | ember_country (v4 calibrated_modern)", "gwa_cell_ember", "X20_SPEC.md 1.1; addendum section 1 (Q1)", rel(ADD), add, "241,246")
    a = pd.read_csv(RV / "WIND_CALIBRATION_ALPHA_V5.csv").set_index("country"); ha = sha256(RV / "WIND_CALIBRATION_ALPHA_V5.csv")
    for c in COUNTRIES:
        x = a.loc[c]; cal = bool(x.calibrated_individually)
        r.add(f"v5_onwind_alpha_{c}", f"{c} onshore-wind speed scaling alpha of the v5 main set (on the GWA-corrected speed; farm-point calibration on Ember 2019-2025, NREL ATB 2020 4 MW "
              "reference turbine; " + ("calibrated on the country's farms" if cal else "capacity-weighted alpha of PH / TH / VN, range = their min / max") + "); the v4 row onwind_alpha_"
              f"{c} keeps the calibrated_modern value", float(x.alpha_main), "factor", ("B" if cal else "C"), "Ember yearly electricity data (CC BY 4.0); GEM GIPT 2026-09 wind farms; GWA v4",
              "research_inputs/renewable_v5/WIND_CALIBRATION_ALPHA_V5.csv", ha, country=c, sensitivity_low=(None if cal else float(x.alpha_range_low)),
              sensitivity_high=(None if cal else float(x.alpha_range_high)), decision_ref="241,246,251", status="REGISTERED")
    file_row(r, "v5_onwind_effective_multiplier_check", RV / "WIND_EFFECTIVE_MULTIPLIER_V5.csv", "decision 251: the bound [0.8, 1.6] applies to the potential-weighted country median of the "
             "effective multiplier cell factor x alpha on the candidate cells (all 11 medians 0.831-1.312, passed; rule correction after the point-factor alphas PH 0.699 / VN 0.789 "
             "were seen; scripts_project/v5_wind_effective_multiplier.py)", "B", "251")
    for N in (1, 3):
        file_row(r, f"renewable_profile_file_calibrated_gwa_v5_c{N}_3h", RV / f"profiles_calibrated_gwa_v5_c{N}_3h.nc", f"S4A-format profiles, variant calibrated_gwa_v5, {N} class(es): "
                 "onshore wind ERA5 x GWA cell factor x alpha V5 + DEA 2050 turbine; offshore and solar = pypsa_eur (equal to calibrated_modern)", "B", "241,246,251")
        file_row(r, f"renewable_profile_classes_calibrated_gwa_v5_c{N}", RV / f"S4A_PROFILE_CLASSES_calibrated_gwa_v5_c{N}.csv", f"class table of calibrated_gwa_v5, {N} class(es)", "B", "241")
    # ---- 1-2 / Q12
    rule_row(r, "v5_existing_wind_profile_rule", "research.demand.v5.existing_wind_profile: best_class (v5 main: existing onshore / offshore wind copies the highest class column of its node, "
             "falling back class by class) | class0 (v4: the worst class after the class split, X03 section 2)", "best_class", "X20_SPEC.md 1.2; X03 REPORT section 2", rel(SPEC), spec, "241", tier="C")
    q = json.loads((RV / "EXISTING_SOLAR_PROFILE_CHOICE.json").read_text())
    rule_row(r, "v5_existing_solar_profile_rule", f"research.demand.v5.existing_solar_profile (Q12, rule fixed before computing, addendum section 3): node average vs best class, the one "
             f"closer to the Ember country solar CF (MW-weighted mean absolute error over the 8 usable countries) for all 11 countries: E node average {q['E']['node_average']:.5f}, best class "
             f"{q['E']['best_class']:.5f} -> {q['choice']} (class 0, reported only: {q['E']['class0']:.5f})", q["choice"], "Ember yearly data; v5 2920x3h pre-build", "research_inputs/renewable_v5/"
             "EXISTING_SOLAR_PROFILE_CHOICE.csv", sha256(RV / "EXISTING_SOLAR_PROFILE_CHOICE.csv"), "246", tier="C")
    # ---- 1-3 / 1-4
    r.add("v5_offwind_asean_premium", "research.demand.v5.offwind_asean_premium_pct: ASEAN capital-cost premium on extendable offshore wind (0 main; sensitivity 10 / 20 / 30 %; X03 section 3.4, "
          "World Bank Viet Nam offshore wind roadmap, secondary)", 0.0, "%", "C", "X03 SOURCES A5-1, A5-2", "X20_SPEC.md 1.3", spec, sensitivity_low=10.0, sensitivity_high=30.0, decision_ref="241", status="SENSITIVITY")
    for c in ("MY", "ID", "VN"):
        r.add(f"v5_solar_cap_scale_{c}", f"research.demand.v5.solar_cap_scale_{c}: factor on the {c} ground-mounted solar caps (1.0 main; 0.5 / 2 for X21)", 1.0, "factor", "C", "X03 section 4.5",
              "X20_SPEC.md 1.4", spec, country=c, sensitivity_low=0.5, sensitivity_high=2.0, decision_ref="241", status="SENSITIVITY")
    v = pd.read_csv(RV / "SOLAR_MY_LANDUSE_VARIANTS_V5.csv").set_index("variant"); hv = sha256(RV / "SOLAR_MY_LANDUSE_VARIANTS_V5.csv")
    r.add("v5_solar_openforest_MY", "research.demand.v5.solar_landuse_my = open_forest: LC100 121-126 counted as eligible after the protected-area exclusion, MY cap 86.4 -> 198 GW (X03 4.5 [E]); "
          "raw LC100 area cross-check without the exclusion 2.3957", float(v.at["open_forest", "factor"]), "factor", "C", "X03 REPORT section 4.5; lc100_country_class_area.csv",
          "research_inputs/renewable_v5/SOLAR_MY_LANDUSE_VARIANTS_V5.csv", hv, country="MY", sensitivity_low=float(v.at["open_forest", "factor"]),
          sensitivity_high=float(v.at["open_forest", "crosscheck_factor_raw_area"]), decision_ref="241", status="SENSITIVITY")
    r.add("v5_solar_oilpalm_MY", f"research.demand.v5.solar_landuse_my = oil_palm: FAOSTAT 2019-2023 mean oil palm harvested area {float(v.at['oil_palm', 'added_area_km2']):,.1f} km2 x 5.1 MW/km2 added to the "
          "MY cap, spread pro rata", float(v.at["oil_palm", "factor"]), "factor", "C", "FAOSTAT QCL item 254 (research_inputs/registry_v5/sources/FAOSTAT_QCL_ASEAN11_2019_2024.csv)",
          "research_inputs/renewable_v5/SOLAR_MY_LANDUSE_VARIANTS_V5.csv", hv, country="MY", sensitivity_low=1.0, sensitivity_high=float(v.at["oil_palm", "factor"]), decision_ref="241", status="SENSITIVITY")
    # ---- 1-5
    rule_row(r, "v5_hydro_inflow_denominator_rule", "research.demand.v5.hydro_inflow_denominator: operating_only (v5 main: per-MW inflow = national target / capacity operating in 2025; "
             "construction units get the same per-MW inflow, Q14) | all_stock (v4)", "operating_only", "X20_SPEC.md 1.5; Q14", rel(SPEC), spec, "241")
    pac = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/config.default.yaml")
    r.add("v5_hydro_inflow_multiplier_source", "research.demand.v5.hydro_inflow_multiplier: 1.1 main (author chain pypsa-asean config.default.yaml:445 'multiplier: 1.1'; introduced by "
          "PyPSA-Earth commit 273eba53 2022-06-30 'Add normalization_multiplier' without a stated reason; the config table documents default 1.0) | 1.0", 1.1, "factor", "C",
          "pypsa-asean config.default.yaml:445; PyPSA-Earth git history", f"{STEP}/logs/46_hydro_multiplier_source.log", sha256(pac) if pac.exists() else sha256(SPEC),
          sensitivity_low=1.0, sensitivity_high=1.1, decision_ref="241", status="REGISTERED")
    rule_row(r, "v5_hydro_spill_bookkeeping_rule", "hydro spill report: bookkeeping part = inflow of the unbuilt new-build reservoir capacity (forced into spill by research_new_hydro_inflow), true "
             "spill = reported - bookkeeping (v5_layers.hydro_spill_tables; regression on W14: F1 526.956 / 519.865 / 7.091 TWh)", "report", "X03 section 5.4", rel(HERE / "v5_layers.py"),
             sha256(HERE / "v5_layers.py"), "241", status="REFERENCE_ONLY")
    # ---- 1-6
    g = pd.read_csv(ROOT / "research_inputs/potentials_v5/GEOTHERMAL_ID_POTENTIAL_V5.csv").set_index("case"); hg = sha256(ROOT / "research_inputs/potentials_v5/GEOTHERMAL_ID_POTENTIAL_V5.csv")
    r.add("potential_geothermal_ID_reserves_2017", "ID geothermal reserves 2017 = possible 12,046 + probable 2,493 + proven 2,967 MW (MEMR via ThinkGeoEnergy 2017-09-24; the article total reads 17,501; "
          "units misprinted as GW); the value is grade B, its use as the 2050 cap (minus the network's ID stock, built at build time) grade C, range proven+probable ... resource potential",
          float(g.at["reserves_2017", "potential_mw"]), "MW", "C", "ThinkGeoEnergy 2017-09-24 (X03 SOURCES C3-5)", "research_inputs/potentials_v5/GEOTHERMAL_ID_POTENTIAL_V5.csv", hg,
          country="ID", sensitivity_low=float(g.at["proven_probable", "potential_mw"]), sensitivity_high=float(g.at["resource_potential", "potential_mw"]), decision_ref="241,246", status="REGISTERED")
    r.add("potential_geothermal_ID_proven_probable_2017", "ID geothermal proven + probable reserves 2017 (2,967 + 2,493 MW); research.demand.v5.geothermal_cap_id = proven_probable (minus stock, Q16)",
          float(g.at["proven_probable", "potential_mw"]), "MW", "B", "ThinkGeoEnergy 2017-09-24 (X03 SOURCES C3-5)", "research_inputs/potentials_v5/GEOTHERMAL_ID_POTENTIAL_V5.csv", hg, country="ID",
          decision_ref="241,246", status="SENSITIVITY")
    # ---- 1-7
    rule_row(r, "v5_biomass_residue_fix_rule", "research.demand.v5.biomass_residue_fix: corrected (v5 main: d1_biomass E1 cotton counted three times -> seed cotton only; E2 R-3 group prefixes "
             "Spices / Cereals, other / Sunflowers added; MM 85.63 -> 84.21 TWh, ASEAN T06 +11.26 TWh) | v4; table-level key", "corrected", "X20_SPEC_ADDENDUM_246.md section 4.3", rel(ADD), add, "241,246")
    B = ROOT / "research_inputs/biomass_v5"
    file_row(r, "v5_biomass_potential_2050_v5fix_base", B / "BIOMASS_POTENTIAL_2050_V5FIX.csv", "d1_biomass.py --v5-residue-fix: the v3 base potential with E1 / E2 fixed", "C", "241,246")
    file_row(r, "v5_biomass_potential_2050_t06_v5fix", B / "BIOMASS_POTENTIAL_2050_V4_T06_V5FIX.csv", "T06 on the corrected base (v4_biomass_potential.py --v5-residue-fix); the v5 main potential", "C", "241,246")
    file_row(r, "v5_biomass_crosscheck_irena", B / "BIOMASS_CROSSCHECK_IRENA_V5.csv", "IRENA 2022 collectable 2050 residues against the current T06 tables (MM ratio 9.13: scope - IRENA 2022 MM "
             "covers wood residues only)", "C", "241")
    # ---- 2-1 / 2-2 / 2-3
    t = pd.read_csv(CV / "PH_DC_STOCK_V5.csv", dtype={"component": str})
    file_row(r, "v5_ph_dc_stock_table", CV / "PH_DC_STOCK_V5.csv", "PH inter-island DC stock override (NGCP TDP 2025-2050): frozen 18,193.28 -> 1,330 MW", "B", "244,246")
    for x in t.itertuples():
        r.add(f"v5_ph_dc_stock_{x.component}", f"PH DC link {x.component}: {x.basis} ({x.action})", float(x.corrected_mw), "MW", str(x.grade), "NGCP Transmission Development Plan 2025-2050",
              f"PDF {x.source_page}", NGCP_SHA, country="PH", decision_ref="244,246", status="REGISTERED")
    file_row(r, "v5_ac_dedup_table", CV / "AC_DEDUP_V5.csv", "domestic AC corridors with OSM duplicate rows: MY lines 90 / 93 / 95 / 96 corrected, 94 not (reconstruction check failed)", "B", "244,246")
    file_row(r, "v5_osm_way_tags", CV / "OSM_WAY_TAGS_V5.csv", "OSM API way tags (cables, circuits) of the 314 duplicated ways (X20 B download, ODbL)", "B", "244")
    gf = pd.read_csv(ROOT / "research_inputs/gas_v5/GAS_CAP_FRACTIONS_V5.csv").set_index("country"); hf = sha256(ROOT / "research_inputs/gas_v5/GAS_CAP_FRACTIONS_V5.csv")
    rule_row(r, "v5_gas_cap_rule_switch", "research.demand.v5.gas_cap_rule: field_status (v5 main, rule B) | reserve_average (rule A) | marketed (v4); the v4 cap table is unchanged, the build "
             "multiplies each country's cap by the fraction", "field_status", "X10 REPORT section 2", "research_inputs/gas_v5/GAS_CAP_FRACTIONS_V5.csv", hf, "244")
    for c in ("BN", "ID", "MM", "MY", "PH", "TH", "TL", "VN"):
        fb, fa = float(gf.at[c, "rule_b_field_status"]), float(gf.at[c, "rule_a_reserve_average"])
        r.add(f"v5_gas_cap_fraction_{c}", f"{c} gas production cap fraction, rule B field status (rule A reserve average {fa:.6f}); {gf.at[c, 'note'] or 'EI Statistical Review 2025 / BP 2021 reserves (X10)'}",
              fb, "fraction", "C", "X10 SOURCES (EI Statistical Review 2025, BP 2021, World Bank 2023 MM, Malampaya, Bayu-Undan)", "research_inputs/gas_v5/GAS_CAP_FRACTIONS_V5.csv", hf, country=c,
              sensitivity_low=(None if fb == 0 else min(fa, fb)), sensitivity_high=(None if fb == 0 else max(fa, fb)), decision_ref="244", status=("SOURCE_ZERO" if fb == 0 else "REGISTERED"))
    # ---- 2-4
    neu = pd.read_csv(ROOT / STEP / "evidence/NEU_GAS_PRODUCT_RULE_V5.csv").set_index("country"); hn = sha256(ROOT / STEP / "evidence/NEU_GAS_PRODUCT_RULE_V5.csv")
    rule_row(r, "v5_neu_gas_product_rule", "research.demand.v5.neu_gas_growth: product (v5 main: a = min(NEU gas 2019, ammonia 2019 x 10.8 MWh/t) grows with the ammonia output, the residual "
             "with the NEU multiplier, methanol part 0 (no sourced feedstock intensity), then DFX F2.4) | industry_multiplier (v4); table-level key", "product", "X20_SPEC_ADDENDUM_246.md section 4.2",
             rel(ADD), add, "244,246")
    for c in neu.index:
        x = neu.loc[c]; v4, v5 = float(x.neu_gas_2050_v4_mwh), float(x.neu_gas_2050_v5_mwh)
        r.add(f"v5_neu_gas_2050_{c}", f"{c} non-energy-use natural gas 2050 after the ammonia deduction, v5 product rule (v4 {v4:,.0f} MWh)", v5, "MWh/a", "C", "v5 table chain (out_ras_v5)",
              f"{STEP}/evidence/NEU_GAS_PRODUCT_RULE_V5.csv", hn, country=c, sensitivity_low=min(v4, v5), sensitivity_high=max(v4, v5), decision_ref="244,246", status="REGISTERED")
    # ---- 2-5 / 2-6
    rule_row(r, "v5_lifetime_boundary_switch", "research.demand.v5.lifetime_boundary: inclusive (v5 main: start + lifetime >= 2050 in service) | strict (v4: > 2050); the frozen electric base is "
             "unchanged (decision 246 Q2 (b)); the S1 boundary units (8, 2,503.1 MW) enter through the GEM additions only (7 units, 1,833.1 MW; North Bangkok 1 mothballed)", "inclusive",
             "X20_SPEC.md 1.12; addendum section 2", f"{STEP}/evidence/Q2_NO_DOUBLE_COUNT.json", sha256(ROOT / STEP / "evidence/Q2_NO_DOUBLE_COUNT.json"), "244,246")
    r.add("v5_geothermal_existing_lifetime", "existing geothermal lifetime of the v5 main set (research.demand.v5.geothermal_existing_lifetime; X10 section 10: Tiwi-MakBan 47 a, Kamojang 43 a); "
          "the v4 row geothermal_existing_lifetime keeps 30 a (S1-3)", 40.0, "years", "C", "X10 REPORT section 10", "X20_SPEC.md 1.12", spec, sensitivity_low=30.0, sensitivity_high=50.0,
          decision_ref="244", status="REGISTERED")
    a5 = pd.read_csv(FV / "FLEET_ADDITIONS_2050_V5.csv"); ha5 = sha256(FV / "FLEET_ADDITIONS_2050_V5.csv")
    for c, d in a5.groupby("country"):
        r.add(f"fleet_additions_2050_v5_{c}", f"{c}: GEM units in service 2050 added under the v5 rule (>= 2050, geothermal 40 a): " + "; ".join(f"{k} {v:,.0f} MW" for k, v in d.groupby('model_class').capacity_mw.sum().items()),
              float(d.capacity_mw.sum()), "MW", "B", "GEM GIPT 2026-09, nearest-node mapping", "research_inputs/fleet_v5/FLEET_ADDITIONS_2050_V5.csv", ha5, country=c, decision_ref="244,246", status="REGISTERED")
    file_row(r, "v5_gem_coord_corrections", FV / "GEM_COORD_CORRECTIONS_V5.csv", "checked coordinates of the approximate GEM points (5 units of X20_SPEC 1.13 + Truong Son 1, which enters "
             "through 2-5); Truong Son 1 and 2 move LA2 1 -> LA2 3", "B", "244")
    # ---- 3-1 .. 3-4
    cs = pd.read_csv(ROOT / "research_inputs/co2_v5/CO2_STORAGE_CASES_V5.csv").set_index("country"); hc = sha256(ROOT / "research_inputs/co2_v5/CO2_STORAGE_CASES_V5.csv")
    for col, case, txt in (("iea_anchor_200_mt", "iea_anchor_200", "(ii-a) ASEAN 200 Mt/a, ID 90, rest by P50 shares"), ("project_ramp_377_mt", "project_ramp_377", "(ii-b) announced capacity x 1.10^20")):
        for c in COUNTRIES:
            r.add(f"v5_co2_storage_case_{case}_{c}", f"{c} annual CO2 injection cap of research.s2.co2.storage_potential_case = {case}: {txt}; read directly (not divided by storage_years)",
                  float(cs.at[c, col]), "Mt CO2/a", "C", "IEA 2021 / project list (X10 SOURCES)", "research_inputs/co2_v5/CO2_STORAGE_CASES_V5.csv", hc, country=c, decision_ref="244", status="SENSITIVITY")
    rule_row(r, "v5_co2_extra_asean_capacity", "research.co2.extra_asean_capacity_mt: null (main, uncapped) | number | {country: Mt/a} as e_nom_max of the country extra-ASEAN store; 0 removes the "
             "store and its links; values for X21 (Q13)", "null", "X20_SPEC.md 1.14 item 4", rel(SPEC), spec, "244", status="REFERENCE_ONLY")
    r.add("v5_dac_investment_scale", "research.cost_scaling.DAC: factor on the DAC capital cost (annualised investment + FOM, as every cost_scaling key); 1.0 main, 1.5 / 2 for X21 (X10 section 4)",
          1.0, "factor", "C", "X10 REPORT section 4", "configs/research/baseline.yaml research.cost_scaling.DAC", spec, sensitivity_low=1.0, sensitivity_high=2.0, decision_ref="244", status="SENSITIVITY")
    r.add("v5_ev_smart_share", "research.s2.demand.ev_smart_share: share of the EV fleet on smart charging (1.0 main = unchanged; 0.5 sensitivity: the rest as a grid-side uncontrolled load on the "
          "charger's bus, X10 section 6(d))", 1.0, "share", "C", "X10 REPORT section 6(d)", "X20_SPEC.md 1.16", spec, sensitivity_low=0.5, sensitivity_high=1.0, decision_ref="244", status="SENSITIVITY")
    r.add("v5_distribution_grid_efficiency", "electricity distribution grid efficiency of the v5 main set (forward and reversed, research.demand.v5.distribution_grid = lv_pypsa_eur; PyPSA-Eur "
          "v2025.07.0 config transmission_efficiency 'electricity distribution grid' efficiency_static)", 0.97, "efficiency", "B", "PyPSA-Eur v2025.07.0 config.default.yaml L762-763",
          rel(PE_CFG), sha256(PE_CFG), decision_ref="244,246", status="REGISTERED")
    rule_row(r, "v5_distribution_grid_lv_attachment", "v5 low-voltage attachment (PyPSA-Eur insert_electricity_distribution_grid): loads with 'electric' in the carrier, BEV chargers, industrial "
             "heat pumps, industrial electric boilers and electric cooking on LV (Q3 (b)); electrolysis, DAC on HV; loads not scaled by 0.97 (Q4 (a)); uncontrolled EV with the charger (Q5 (a))",
             "lv_pypsa_eur", "PyPSA-Eur v2025.07.0 prepare_sector_network.py L1479-1590", rel(PE_PSN), sha256(PE_PSN), "244,246")
    rule_row(r, "v5_bunker_attribution_rule", "post-solve report BUNKER_CARBON_ATTRIBUTION: methanol synthesis carbon by producer -> destination (annual proportional mixing over the methanol "
             "trade, INFERENCE) -> use, by the producer's co2 stored inflow shares; W14 F1 130.958 Mt, 120.13 Mt to bunker shipping", "report", "X10 08_x16_bunker.py + BUNKER_CARBON_MEMO",
             rel(HERE / "v5_bunker_attribution.py"), sha256(HERE / "v5_bunker_attribution.py"), "244", status="REFERENCE_ONLY")
    return r


NOTES = {
    "onwind_gwa_crosscheck_s4b3": "[V5 X20, X20_SPEC 1.1 (d)] the GWA 3.3 country constants (s4b_3_wind_calibration.py:38) have no located source and are not used; GWA v4 rasters replace them in v5 (v5_onwind_gwa_cell_factor)",
    "renewable_capacity_per_sqkm_solar": "[V5 X20, X20_SPEC 1.4] 5.1 MW/km2 is the average density over the whole eligible land, already including the use of only a small part of it (PyPSA-Earth 4.6 = 45.6 x 10 %); 5.1 / 4.6 = 1.1087 is only the ratio of two model densities, no source gives that factor (X03 4.1); value unchanged",
    "hydro_inflow_normalization_main": "[V5 X20, X20_SPEC 1.5] v5 main: the denominator is the capacity operating in 2025; construction units get the same per-MW inflow (v5_hydro_inflow_denominator_rule)",
    "candidate_cap_geothermal_ID": "[V5 X20, X20_SPEC 1.6] v5: computed at build time = research.demand.v5.geothermal_cap_id potential (reserves 2017 17,506 MW main) - the network's ID stock (v4 value kept for v5 off)",
    "demand_neu_2050_ID": "[V5 X20, X20_SPEC 1.11] the v4 main tables (out_ras) grow ID NEU with the v4 NEU multiplier 3.2034, not the v3.1 2.61861 of this row; under v5 (out_ras_v5) ID NEU natural gas is 0 (v5_neu_gas_2050_ID)",
    "fleet_lifetime_rule_s1": "[V5 X20, X20_SPEC 1.12] v5 main: start year + lifetime >= 2050 in service (research.demand.v5.lifetime_boundary = inclusive; FLEET_ADDITIONS_2050_V5.csv)",
    "s4j2_link_losses": "[V5 X20, X20_SPEC 1.17] the distribution grid efficiency 0.97 is used in v5 (v5_distribution_grid_efficiency); v4 unchanged",
    "co2_storage_unified_table": "[V5 X20, X20_SPEC 1.14] the /50 is PyPSA-Eur co2_sequestration_lifetime 50 (asset lifetime, config L712), not years_of_storage 25 (L702); /50 is more conservative than /25; PyPSA-Eur also has an EU 2050 total cap of 250 Mt/a (L703-710, reference); decisions 28-30; '50' has no external literature source in the registry",
}


def corrections(base: pd.DataFrame) -> pd.DataFrame:
    R = base.set_index("param_id"); rows = []
    ids = dict(NOTES)
    for c in COUNTRIES:
        ids[f"co2_injection_cap_unified_{c}"] = NOTES["co2_storage_unified_table"]
        ids[f"co2_injection_cap_{c}"] = NOTES["co2_storage_unified_table"]
    for pid, note in ids.items():
        if pid not in R.index:
            raise SystemExit(f"registry row {pid} missing")
        x = R.loc[pid].to_dict()
        if note in x["description"]:
            desc = x["description"]
        else:
            desc = f"{x['description']} | {note}"
        dec = x["decision_ref"] if "244" in str(x["decision_ref"]) else (str(x["decision_ref"]) + ", 244").strip(", ")
        y = dict(x, param_id=pid, description=desc, decision_ref=dec)
        rows.append({c: y[c] for c in COLUMNS})
    return pd.DataFrame(rows, columns=COLUMNS)


def main():
    r = new_rows()
    out = REG_DIR / "fragments" / "v5_x20.csv"
    r.write(out)
    base, _ = DR.assemble(DR.CORRECTIONS[:DR.CORRECTIONS.index("v5_x20_corrections")])
    corr = corrections(base)
    corr.sort_values("param_id").to_csv(REG_DIR / "fragments" / "v5_x20_corrections.csv", index=False, lineterminator="\n")
    print(out, len(r.rows), "rows; corrections", len(corr))


if __name__ == "__main__":
    main()
