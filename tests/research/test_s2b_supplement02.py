"""S2 supplement 02 (decisions 55-60): data outputs of R1-R3, solver-free checks of R4-R7, and the rebuilt networks (results_project/s2b)."""
from __future__ import annotations

import inspect
import json
import math
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
REG = ROOT / "research_inputs" / "registry_v5"
DEM = ROOT / "research_inputs" / "demand_v5"
S2B = ROOT / "results_project" / "s2b"


@pytest.fixture(scope="module")
def registry():
    return pd.read_csv(REG / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")


# ---------------------------------------------------------------- R3 (decision 57)
def test_r3_aeo8_relative_allocation(registry):
    r = registry
    assert r.loc["demand_country_allocation_mode", "value"] == "aeo8_ats_relative"
    assert abs(float(r.loc["demand_aeo8_percapita_sum_check_2022", "value"]) / 432.2 - 1) < 1e-3
    assert abs(float(r.loc["demand_aeo8_percapita_sum_check_2050", "value"]) / 746.2 - 1) < 1e-3
    growth = pd.read_csv(REG / "sources" / "GROWTH_CHAIN_2019_2050_WDI_SSP2.csv").set_index("Country Code")
    assert float(r.loc["demand_aeo8_ats_relative_factor_TL", "value"]) == pytest.approx(float(growth.loc["TLS", "gdp_rel_ASEAN"]))
    # r_c = G_c / G_ASEAN; ID per-capita 586.45 -> 901.77 kgoe, population 275.8 -> 317.2 M (C.8 / D.1)
    g_id = (901.77 * 317.2) / (586.45 * 275.8)
    assert float(r.loc["demand_aeo8_ats_growth_2022_2050_ID", "value"]) == pytest.approx(g_id, rel=1e-6)
    ch = json.loads((DEM / "DEMAND_2050_CROSSCHECKS.json").read_text())["checks"]["r3_aeo8_country_allocation"]
    assert float(r.loc["demand_aeo8_ats_relative_factor_ID", "value"]) == pytest.approx(g_id / ch["G_asean"], rel=1e-6)
    dem = pd.read_csv(DEM / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", keep_default_na=False)
    ind_vn = dem[(dem.country == "VN") & (dem.sector == "Industry")].multiplier_total.astype(float).iloc[0]
    assert ind_vn == pytest.approx(float(r.loc["demand_country_multiplier_2019_2050_VN", "value"]), rel=1e-9)
    cmp = pd.read_csv(DEM / "DEMAND_2050_ALLOCATION_COMPARISON.csv")
    assert len(cmp) == 66 and (cmp.value_2050_aeo8_mwh >= 0).all()
    for f in ["DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_GDP_SENSITIVITY.csv", "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_POP_SENSITIVITY.csv"]:
        assert (DEM / f).exists()


# ---------------------------------------------------------------- R1 (decision 55)
def test_r1_industry_routes(registry):
    r = registry
    s = pd.read_csv(DEM / "INDUSTRY_2050_SUMMARY_aeo8_ats_relative.csv").set_index("country")
    vn = s.loc["VN"]
    assert vn.crude_steel_2019_t == pytest.approx(17469e3) and vn.crude_steel_2050_t == pytest.approx(17469e3 * vn.industry_multiplier, rel=1e-9)
    assert vn.primary_dri_2050_t == pytest.approx(0.3 * vn.crude_steel_2050_t, rel=1e-9)
    # S3-0 (decision 61): PyPSA-Eur ratios reproduced from JRC-IDEES-2021 for all sub-sectors; technology-data steel/cement = sensitivity file
    ratios = pd.read_csv(REG / "INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", index_col=0)
    assert ratios.shape[1] == 27 and ratios.at["hydrogen", "DRI + Electric arc"] == pytest.approx(1.7) and ratios.at["heat", "Cement"] > 0   # H2_DRI line 839; low-T heat row
    h2_dri = 1.7 * vn.primary_dri_2050_t
    assert abs(vn.pe_hydrogen_mwh - h2_dri) < 0.05 * h2_dri   # DRI hydrogen +- the chemical rows (HVC +0.173, chlorine by-product -0.937 MWh_H2/t)
    assert s.loc["ID"].clinker_2019_t == pytest.approx(29379.1246447e3 / 0.52, rel=1e-9)         # EDGAR 2.A.1 / IPCC EF
    assert s.loc["ID"].cement_2050_t == pytest.approx(s.loc["ID"].clinker_2019_t / 0.656 * s.loc["ID"].industry_multiplier, rel=1e-6)   # technology-data cement finishing clinker-input
    assert (s.pe_coal_mwh == 0).all() and vn.pe_coal_mwh < vn.bas_coal_mwh   # 2050 ratios carry coal/coke only in Integrated steelworks (not used: primary route = H2-DRI)
    assert s.loc["SG"].biomass_overflow_agriculture_to_gas_mwh > 0 and s.loc["VN"].biomass_overflow_industry_to_gas_mwh > 0
    assert (s.pe_heat_mwh > 0).sum() >= 10 and (s.pe_ammonia_mwh >= 0).all()   # low-temperature heat row for every country with industry (TL none)
    assert r.loc["industry_sector_ratios_pypsa_eur_2050", "status"] == "REGISTERED" and r.loc["industry_carrier_mode", "value"] == "pypsa_eur_2050"
    assert r.loc["industry_ratio_source", "value"].startswith("jrc_idees_2021") and float(r.loc["industry_sector_ratios_eu27_ammonia_2019", "value"]) == pytest.approx(15712.857, rel=1e-5)
    assert float(r.loc["industry_clinker_emission_factor_ipcc", "value"]) == 0.52
    td = pd.read_csv(DEM / "INDUSTRY_2050_SUMMARY_aeo8_ats_relative_TD_SENSITIVITY.csv").set_index("country")
    assert td.loc["VN"].pe_hydrogen_mwh == pytest.approx(vn.pe_hydrogen_mwh, rel=1e-9) and td.loc["ID"].pe_gas_mwh > 0 and td.loc["ID"].pe_electricity_mwh != s.loc["ID"].pe_electricity_mwh   # S2B steel/cement method kept as sensitivity
    cmp = pd.read_csv(DEM / "INDUSTRY_2050_COMPARISON_BAS_S2B_S3.csv")
    assert len(cmp) == 99 and set(cmp.columns) >= {"bas_fixed_mwh", "s2b_technology_data_mwh", "s3_0_idees_mwh"}
    gaps = pd.read_csv(DEM / "INDUSTRY_2050_GAPS.csv")
    assert (gaps[gaps["mode"] == "aeo8_ats_relative"].country == "VN").any()


# ---------------------------------------------------------------- R2 (decision 56)
def test_r2_territorial_feedstock(registry):
    r = registry
    f = pd.read_csv(REG / "FEEDSTOCK_CARBON_TERRITORIAL_2050_aeo8_ats_relative.csv", keep_default_na=False).set_index("country")
    sg = f.loc["SG"]
    assert float(sg.process_2B_2D_2050_t) == pytest.approx((float(sg.edgar_2B_2019_t) + float(sg.edgar_2D_2019_t)) * float(sg.industry_multiplier), rel=1e-9)
    idn = f.loc["ID"]
    expect = float(idn.msw_2050_t) * float(idn.plastic_share) * (0.3747 * 0.739) * 1.0 * 0.75 * 1.0 * 44 / 12
    assert float(idn.plastics_burned_co2_2050_t) == pytest.approx(expect, rel=1e-3)
    la = f.loc["LA"]   # S3-0 (decision 63): MSW-weighted proxies, grade C, sensitivity 0 .. observed max
    assert float(la.plastics_burned_co2_2050_t) > 0 and str(la.plastic_share_is_proxy) == "True" and "proxy" in str(la["flags"])
    assert r.loc["waste_plastic_share_LA", "status"] == "REGISTERED" and float(r.loc["waste_plastic_share_LA", "sensitivity_low"]) == 0.0 and float(r.loc["waste_plastic_share_LA", "sensitivity_high"]) == pytest.approx(0.29)
    assert all(str(f.loc[c].open_burned_share_is_proxy) == "True" for c in ["KH", "TH", "VN"]) and str(f.loc["ID"].open_burned_share_is_proxy) == "False"
    assert r.loc["feedstock_carbon_mode", "value"] == "territorial" and float(r.loc["plastics_total_carbon_fraction_ipcc", "value"]) == 0.75
    assert float(f.loc["TH"].full_release_2050_t) > float(f.loc["TH"].territorial_total_2050_t)


# ---------------------------------------------------------------- R4 (decision 58)
def test_r4_representative_weights():
    import pypsa
    from s2_solve import set_representative_weights
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=56, freq="3h"))
    n.snapshot_weightings.loc[:, :] = 3.0
    led = set_representative_weights(n)
    assert led["weight_hours_per_snapshot"] == pytest.approx(8760 / 56) and led["annual_caps_scaled"] is False
    assert all(n.snapshot_weightings[c].sum() == pytest.approx(8760.0) for c in ["objective", "generators", "stores"])
    assert n.meta["representative_weights"]["decision"] == "58"


# ---------------------------------------------------------------- R7
def test_r7_gate_signatures():
    from validation_dynamics import dynamic_checks
    from v5.v5_gates import gate_a3_a5_physics, gate_b11_supply_routes
    assert "extra_known_objective" in inspect.signature(dynamic_checks).parameters
    assert {"known_terms", "ignore_checks"} <= set(inspect.signature(gate_a3_a5_physics).parameters)
    src = inspect.getsource(gate_b11_supply_routes)
    assert "auxiliary_nodes_without_loads" in src and "load_nodes" in src


# ---------------------------------------------------------------- rebuilt networks (R1, R2, R5, R6 wiring)
INT = S2B / "integrated" / "integrated_2920_3h_unsolved.nc"
DIS = S2B / "disconnected" / "disconnected_2920_3h_unsolved.nc"


@pytest.fixture(scope="module")
def nets():
    import pypsa
    if not INT.exists() or not DIS.exists():
        pytest.skip("S2B networks not built")
    return pypsa.Network(str(INT)), pypsa.Network(str(DIS)), json.loads((S2B / "integrated" / "integrated_BUILD_RECEIPT.json").read_text())


def test_s2b_networks_r5_pipelines(nets):
    ni, nd, ri = nets
    p = ri["pipelines"]
    assert p["topology"] == "electricity_network_topology" and p["candidates"] == 109 and p["cross_border_candidates"] == 19
    assert p["by_country_pair"]["LA-TH"] == 9 and "MM" not in "".join(p["by_country_pair"]) and p["domestic_by_country"]["MM"] > 0
    assert (ni.links.carrier == "H2 pipeline").sum() == 109 == (ni.links.carrier == "CO2 pipeline").sum()
    assert not ni.links.index.str.contains("via HVDC").any()
    a, b = "ID_Kalimantan4 8", "MY_Sarawak4 1"
    x0, y0, x1, y1 = ni.buses.at[a, "x"], ni.buses.at[a, "y"], ni.buses.at[b, "x"], ni.buses.at[b, "y"]
    p0, p1 = math.radians(y0), math.radians(y1); h = math.sin((p1 - p0) / 2) ** 2 + math.cos(p0) * math.cos(p1) * math.sin(math.radians(x1 - x0) / 2) ** 2
    L = 2 * 6371.0088 * math.asin(math.sqrt(h)) * 1.25
    assert ni.links.at[f"CO2 pipeline {a} -> {b}", "length"] == pytest.approx(L, rel=1e-6)
    assert ((nd.links.carrier == "H2 pipeline") & (nd.links.border_class == "cross_border")).sum() == 0


def test_s2b_networks_r1_r2_r6(nets):
    ni, nd, ri = nets
    assert ri["demand_s2"]["parameters"]["industry_carrier_mode"] == "pypsa_eur_2050"
    assert (ni.loads.carrier == "industry hydrogen").sum() > 0 and (ni.loads.carrier == "industry electricity").sum() > 0
    assert (ni.generators.carrier == "plastic waste").sum() > 0 and (ni.links.carrier == "waste incineration").sum() > 0
    feed = ni.links[ni.links.carrier.str.endswith(" feedstock")]
    assert (feed.bus2 == "").all()   # territorial mode: no carbon ports on the feedstock links
    dac = ni.links[ni.links.carrier == "DAC"].iloc[0]
    assert dac.bus3.endswith(" industry heat") and dac.efficiency3 == pytest.approx(-1.4 / 0.55, rel=1e-6) and dac.efficiency == pytest.approx(1 / 0.55, rel=1e-6)
    ded = {d["country"]: d for d in ri["demand_s2"]["deductions"]}
    assert ded["VN"]["deducted_industry_mwh"] > 0 and ded["VN"]["added_explicit"]["industry_hydrogen_mwh"] > 0
    ov = ri["demand_s2"]["parameters"]
    assert ov["industry_table"].endswith("INDUSTRY_2050_SUMMARY_aeo8_ats_relative.csv")
