"""D1 data registry tests (no network build, no solve)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
REG = ROOT / "research_inputs" / "registry_v5"
DEM = ROOT / "research_inputs" / "demand_v5"
BIO = ROOT / "research_inputs" / "biomass_v5"
COST = ROOT / "research_inputs" / "cost_layers_v5"
LNG = ROOT / "research_inputs" / "lng_terminals_v5"
MWH_PER_MTOE = 11.63e6
AEO8_BAS_2050_MTOE = {"Industry": 561.0, "Transport": 374.9, "Residential": 68.2, "Commercial": 75.9, "AgricultureOthers": 27.8}
ASEAN10 = ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "VN"]


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="module")
def registry():
    return pd.read_csv(REG / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False)


def test_registry_schema_and_tiers(registry):
    from d1_common import COLUMNS
    assert list(registry.columns) == COLUMNS
    assert registry.param_id.is_unique
    assert set(registry.tier) <= {"A", "B", "C"}
    from d1_common import STATUSES
    assert set(registry.status) <= STATUSES
    zbd = registry[registry.status == "ZERO_BY_DECISION"]
    assert len(zbd) == 11 and (pd.to_numeric(zbd.value) == 0).all()
    pend = registry[registry.status == "DATA_PENDING"]
    assert (pend.value == "DATA_PENDING").all()
    c = registry[(registry.tier == "C") & (registry.status == "REGISTERED")]
    numeric = pd.to_numeric(c.value, errors="coerce").notna()
    assert ((c[numeric].sensitivity_low != "") & (c[numeric].sensitivity_high != "")).all()
    assert (registry[registry.status != "DATA_PENDING"].source_sha256 != "").all()


def test_author_aeo8_rule_replicates_author_output():
    import d1_cost_layers as cl
    fx = 0.8772286325726557
    layer = cl.author_rule(fx).set_index("technology_data_name")
    # values quoted in the D1 instruction (EUR/MW in the author's costs_2050_sec.csv)
    assert layer.loc["solar-utility", "investment_eur2020_per_kw"] * 1000 == pytest.approx(850911.77, rel=1e-6)
    assert layer.loc["onwind", "investment_eur2020_per_kw"] * 1000 == pytest.approx(991619.25, rel=1e-6)
    assert layer.loc["solar-utility", "decline_label_matched"] == False  # "Solar" != "Solar PV": no decline for solar
    assert layer.loc["onwind", "decline_label_matched"] == True
    assert layer.loc["solar-utility", "investment_eur2020_per_kw"] == pytest.approx(970 * fx)
    assert layer.loc["onwind", "investment_eur2020_per_kw"] == pytest.approx(1570 * fx * (1 - 0.28))
    if cl.AUTHOR_OUTPUT.exists():
        ver = pd.read_csv(COST / "LAYER_B_VERIFICATION_VS_AUTHOR_OUTPUT.csv")
        assert ver.rel_diff.abs().max() < 1e-9


def test_smr_cost_rows(registry):
    r = registry.set_index("param_id")
    inv = float(r.loc["smr_investment", "value"])
    assert inv == pytest.approx(9600 * 0.8772286325726557, rel=1e-9)
    assert r.loc["smr_investment", "tier"] == "C"
    assert float(r.loc["smr_investment", "sensitivity_low"]) == pytest.approx(inv * 0.7)
    assert float(r.loc["smr_investment", "sensitivity_high"]) == pytest.approx(inv * 1.3)
    assert float(r.loc["smr_FOM", "value"]) == pytest.approx(110.0 / 9600 * 100)
    assert float(r.loc["geothermal_existing_FOM", "value"]) == 2.0
    assert float(r.loc["geothermal_existing_lifetime", "value"]) == 30.0


def test_co2_storage_values_and_caps(registry):
    r = registry.set_index("param_id")
    for c, main in {"MY": 127 + 1.773, "ID": 49 + 2.275, "BN": 18 + 0.5793, "TH": 15 + 1.024, "PH": 22.3, "VN": 11.8, "KH": 0.085, "TL": 0.25, "LA": 0, "MM": 0, "SG": 0}.items():
        assert float(r.loc[f"co2_storage_potential_{c}", "value"]) == pytest.approx(main, abs=1e-9)
        assert float(r.loc[f"co2_injection_cap_{c}", "value"]) == pytest.approx(main * 1e9 / 50, rel=1e-12)
    assert float(r.loc["co2_storage_potential_MY", "sensitivity_low"]) == 80.0
    assert float(r.loc["co2_storage_potential_ID", "sensitivity_high"]) == pytest.approx(77.275)


def test_fuel_price_conversion(registry):
    r = registry.set_index("param_id")
    fx = (105.377 / 125.587) * 0.8772286325726557
    gas = 4.9 / 0.29307107 / 0.90 * fx
    assert float(r.loc["fuel_price_gas_NZE_2050_main", "value"]) == pytest.approx(gas, rel=1e-9)
    coal = 49 / (25.1208 / 3.6) * fx
    assert float(r.loc["fuel_price_coal_NZE_2050_main", "value"]) == pytest.approx(coal, rel=1e-9)
    assert r.loc["fuel_price_basis", "value"] == "NCV"
    assert r.loc["fuel_price_gas_STEPS_2050_high_price", "status"] == "SENSITIVITY"


def test_lng_caps(registry):
    r = registry.set_index("param_id")
    mwh_per_mtpa = 1e6 * 48.0 / 3.6
    assert float(r.loc["lng_existing_capacity_SG", "value"]) == pytest.approx(11.0)
    for c in ["ID", "MY", "PH", "SG", "TH", "VN"]:
        ex = float(r.loc[f"lng_existing_capacity_{c}", "value"])
        assert float(r.loc[f"lng_import_cap_{c}", "value"]) == pytest.approx(2.5 * ex * mwh_per_mtpa, rel=1e-9)  # CSV keeps 12 significant digits
    assert r.loc["lng_import_cap_LA", "status"] == "SOURCE_ZERO"
    units = load(LNG / "LNG_IMPORT_TERMINALS_GEM_2025.csv")
    assert all(u["node"].split(" ")[0][:2] == u["country"] for u in units if u["country"] not in ("TL",))


def test_fossil_production_caps(registry):
    r = registry.set_index("param_id")
    assert float(r.loc["fossil_production_cap_coal_ID", "value"]) == pytest.approx(616167.277e3 * 25.8 / 3.6, rel=1e-9)
    assert float(r.loc["fossil_production_cap_gas_SG", "value"]) == 0.0
    assert r.loc["fossil_production_cap_gas_SG", "status"] == "SOURCE_ZERO"
    assert float(r.loc["fossil_production_cap_gas_MY", "value"]) == pytest.approx(3398100.728 * 0.9 / 0.0036, rel=1e-9)


def test_demand_2050_calibration():
    rows = load(DEM / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv")
    for s, mtoe in AEO8_BAS_2050_MTOE.items():
        tot = sum(float(r["value_2050_mwh"]) for r in rows if r["sector"] == s and r["country"] in ASEAN10 and r["value_2050_mwh"] != "")
        assert tot == pytest.approx(mtoe * MWH_PER_MTOE, rel=1e-9)
    vals = [float(r["value_2050_mwh"]) for r in rows if r["value_2050_mwh"] != ""]
    assert min(vals) >= 0.0
    pend = [r for r in rows if r["status"] == "DATA_PENDING"]
    assert pend == []  # S2-0.4: the four marine bunkers are 0 (UNSD Energy Balance 2019 shows no flow)
    zero = [r for r in rows if r["sector"] == "InternationalBunkers" and r["account"] == "InternationalShippingBunker" and r["country"] in ("BN", "KH", "LA", "TL")]
    assert len(zero) == 4 and all(r["status"] == "SOURCE_ZERO" and float(r["value_2050_mwh"]) == 0.0 for r in zero)
    elec = [r for r in rows if r["carrier"] == "electricity" and r["sector"] in AEO8_BAS_2050_MTOE]
    assert all(r["in_existing_electricity_load"] == "true" and r["existing_electricity_load_2050_mwh"] != "" for r in elec)
    ne = [r for r in rows if r["sector"] == "NonEnergyUse"]
    assert ne and all("industry multiplier" in r["growth_method"] for r in ne)
    checks = json.loads((DEM / "DEMAND_2050_CROSSCHECKS.json").read_text())
    ratio = checks["checks"]["electricity_vs_existing_astar_2050"]["table_total_asean11_mwh"] / checks["checks"]["electricity_vs_existing_astar_2050"]["astar_total_asean11_mwh"]
    assert 0.8 < ratio < 1.2


def test_biomass_replication_and_potentials():
    rep = load(BIO / "REPLICATION_R3_VS_R1A.csv")
    assert len(rep) == 5
    assert max(abs(float(r["err_H_pct"])) for r in rep) < 2.0
    assert max(abs(float(r["err_P_pct"])) for r in rep) < 2.0
    fao = load(BIO / "REPLICATION_FAOSTAT2010_VS_R1A.csv")
    assert max(abs(float(r["err_H_pct"])) for r in fao) < 10.0
    assert max(abs(float(r["err_P_pct"])) for r in fao) < 25.0
    pot = load(BIO / "BIOMASS_POTENTIAL_2050.csv")
    assert {r["country"] for r in pot} == set(ASEAN10 + ["TL"])
    for r in pot:
        if r["status"] == "DATA_PENDING":
            continue
        lo, m, hi = float(r["potential_low_mwh"]), float(r["potential_main_mwh"]), float(r["potential_high_mwh"])
        assert 0 <= lo <= m * (1 + 1e-9) and m <= hi * (1 + 1e-9), r["category"]
        if r["cost_eur2020_per_mwh"] != "":
            assert float(r["cost_low_eur2020_per_mwh"]) == pytest.approx(0.5 * float(r["cost_eur2020_per_mwh"]))
            assert float(r["cost_high_eur2020_per_mwh"]) == pytest.approx(1.5 * float(r["cost_eur2020_per_mwh"]))
    assert all(r["country"] != "SG" or r["category"] in ("msw_organic_biogas", "wood_processing_residues", "logging_residues", "other_crop_residues", "coconut_residues", "rice_residues", "sugarcane_residues", "maize_residues", "cassava_residues") for r in pot)
    # S2-0.2: MSW organic fraction is a biogas feedstock (IPCC DOC method), no direct-combustion row left
    assert not any(r["category"] == "msw_organic" for r in pot)
    msw = [r for r in pot if r["category"] == "msw_organic_biogas" and r["status"] != "DATA_PENDING"]
    assert msw and all(r["feedstock_group"] == "biogas" and 0.5 < float(r["lhv_gj_per_t"]) < 3.5 for r in msw)
    assert [r["country"] for r in pot if r["category"] == "msw_organic_biogas" and r["status"] == "DATA_PENDING"] == ["LA"]
    # S2-0.5: logging residues are zero by decision with a high-biomass sensitivity; wood processing residues derived for the FAO-gap countries
    logs = [r for r in pot if r["category"] == "logging_residues"]
    assert len(logs) == 11 and all(r["status"] == "ZERO_BY_DECISION" and float(r["potential_main_mwh"]) == 0.0 for r in logs)
    assert sum(float(r["potential_high_mwh"]) for r in logs) > 0
    wood = {r["country"]: r for r in pot if r["category"] == "wood_processing_residues"}
    assert all(wood[c]["status"] == "REGISTERED" for c in ["BN", "KH", "LA", "MM", "PH", "SG", "TL", "ID", "MY", "TH", "VN"])
    assert "FAO/APFC 2001" in wood["KH"]["potential_method"] and wood["KH"]["potential_tier"] == "B" and wood["SG"]["potential_tier"] == "C"


def test_demand_shares(registry):
    r = registry.set_index("param_id")
    assert float(r.loc["share_land_transport_electric_share_2050", "value"]) == 1.0
    assert float(r.loc["share_shipping_methanol_share_2050", "value"]) == 1.0
    assert float(r.loc["share_DRI_fraction_2050", "value"]) == 1.0
    assert r.loc["share_reduce_space_heat_exogenously_factor_2050", "status"] == "REFERENCE_ONLY"
    assert r.loc["share_source_version", "value"] == "v2025.07.0"


def test_cost_layer_config_switch():
    import yaml
    import d1_cost_layers as cl
    cfg = yaml.safe_load((ROOT / "configs" / "research" / "baseline.yaml").read_text())
    cl_cfg = cfg["research"]["cost_layer"]
    assert cl_cfg["active"] == "technology_data_v0_15_0_2050_eur2020"  # S2-0.1, decision 50
    assert set(cl_cfg["layers"]) == {"technology_data_v0_15_0_2050_eur2020", "technology_data_v0_13_2_2050", "aeo8_author_rule_2050"}
    name, layer = cl.load_cost_layer(cfg)
    assert name == "technology_data_v0_15_0_2050_eur2020" and layer["manifest"]["aeo8_overrides"] is False
    assert layer["manifest"]["technology_data"]["tag"] == "v0.15.0" and layer["manifest"]["technology_data"]["eur_year"] == 2025
    cfg["research"]["cost_layer"]["active"] = "technology_data_v0_13_2_2050"
    name, layer = cl.load_cost_layer(cfg)
    assert name == "technology_data_v0_13_2_2050" and layer["manifest"]["aeo8_overrides"] is False
    cfg["research"]["cost_layer"]["active"] = "aeo8_author_rule_2050"
    name, layer = cl.load_cost_layer(cfg)
    assert name == "aeo8_author_rule_2050" and "nuclear SMR" in set(layer["overrides"].technology_data_name)


def test_s2_0_cost_layer_v015_rebase(registry):
    import pandas as pd
    r = registry.set_index("param_id")
    d2025 = float(r.loc["deflator_ea20_gdp_2025", "value"])
    assert d2025 == pytest.approx(120.01983244779059, rel=1e-9)
    factor = 100.0 / d2025
    assert float(r.loc["conv_eur2025_to_eur2020", "value"]) == pytest.approx(factor, rel=1e-9)
    assert float(r.loc["cost_C_onwind_investment", "value"]) == pytest.approx(1286.4669 * factor, rel=1e-6)
    assert float(r.loc["cost_C_electrolysis_investment", "value"]) == pytest.approx(1257.3346 * factor, rel=1e-6)
    assert r.loc["technology_data_v0_15_0_tag_commit", "value"] == "07e43575c7996a988c60964d00772376ab9bd10c"
    long = pd.read_csv(COST / "technology_data_v0.15.0_EUR2020" / "costs_2050_EUR2020.csv")
    mon = long[long.monetary]
    import numpy as np
    assert (mon.currency_year == 2020).all()
    assert np.allclose(mon[mon.source_currency_year == 2025].conversion_factor, factor) and (mon.source_currency_year == 2025).sum() == 374
    assert (mon[mon.source_currency_year == 2020].conversion_factor == 1.0).all()  # 'commodity' row already EUR2020
    assert (mon[mon.source_currency_year == 2019].conversion_factor > 1.0).all()  # 'pelletizing cost' row inflated 2019 -> 2020
    assert (long[~long.monetary].conversion_factor == 1.0).all()
    wide = pd.read_csv(COST / "technology_data_v0.15.0_EUR2020" / "costs_2050_EUR2020_prepared.csv", index_col=0)
    inv = float(wide.at["direct air capture", "investment"]); fom = float(wide.at["direct air capture", "FOM"]); life = float(wide.at["direct air capture", "lifetime"])
    assert float(wide.at["direct air capture", "fixed"]) == pytest.approx(inv * (0.07 / (1 - 1.07 ** -life) + fom / 100), rel=1e-9)
    assert "SMR" in wide.index and float(wide.at["nuclear", "marginal_cost"]) > float(wide.at["nuclear", "VOM"])


def test_s2_0_process_emissions(registry):
    r = registry.set_index("param_id")
    # EDGAR 2025 2019 kt: ID 2.A.1 29.38 + 2.A.2 0.34 + 2.A.3-4 0.40 Mt (extraction md section 1)
    assert float(r.loc["process_emissions_minerals_2019_ID", "value"]) == pytest.approx(30.12e6, rel=0.01)
    assert float(r.loc["process_emissions_chemicals_2019_SG", "value"]) == pytest.approx(10.36e6, rel=0.01)
    assert r.loc["process_emissions_chemicals_2050_SG", "status"] == "REFERENCE_ONLY"  # covered by feedstock carbon (method question)
    assert r.loc["process_emissions_metals_2050_VN", "status"] == "REGISTERED"
    mult = float(r.loc["demand_gdp_multiplier_2019_2050_VN", "value"]) * float(r.loc["demand_sector_calibration_k_Industry", "value"])
    assert float(r.loc["process_emissions_minerals_2050_VN", "value"]) == pytest.approx(float(r.loc["process_emissions_minerals_2019_VN", "value"]) * mult, rel=1e-9)
    assert not any(registry.param_id.str.startswith("process_emissions_") & (registry.status == "DATA_PENDING"))
    assert float(r.loc["fugitive_factor_oilgas_MY", "value"]) > 0 and r.loc["fugitive_factor_oilgas_MY", "unit"] == "tCO2/MWh_production"
    assert r.loc["demand_bunker_marine_zero_LA", "status"] == "SOURCE_ZERO" and float(r.loc["demand_bunker_marine_zero_LA", "value"]) == 0.0
    assert "demand_bunker_pending_LA_InternationalShippingBunker" not in r.index
    bound = load(REG / "FEEDSTOCK_CARBON_BOUNDARY_2019.csv")
    sg = next(b for b in bound if b["country"] == "SG")
    assert float(sg["edgar_2B_chemicals_tco2"]) == pytest.approx(10.36e6, rel=0.01) and float(sg["feedstock_carbon_potential_tco2"]) > float(sg["edgar_2B_chemicals_tco2"])
