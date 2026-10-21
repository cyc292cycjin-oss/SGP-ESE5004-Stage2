"""M08b B1 / M08-5 (decisions 126, 129, 134): AEO8 ATS activity anchors and the physical output rule (no build, no solve)."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from m08b_demand import BASE_SECTORS, SECTORS, aeo8_country, c3_ats, gdp_growth, RES_ELEC_ATS_MTOE   # noqa: E402
from s2_layers import demand_anchor_settings, demand_table_key, physical_output_settings   # noqa: E402

DEM = ROOT / "research_inputs" / "demand_v5"
REG = ROOT / "research_inputs" / "registry_v5" / "DATA_REGISTRY.csv"
ASEAN = ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "TL", "VN"]
TOL = 1e-6


def rel(a, b):
    return abs(a - b) / max(1.0, abs(b))


@pytest.fixture(scope="module")
def data():
    an = pd.read_csv(DEM / "DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
    t = pd.read_csv(DEM / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False)
    t["v"] = pd.to_numeric(t.value_2050_mwh, errors="coerce").fillna(0.0); t["b"] = pd.to_numeric(t.base_2019_mwh, errors="coerce").fillna(0.0)
    ratio = pd.read_csv(DEM / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", keep_default_na=False)
    ratio["b"] = pd.to_numeric(ratio.base_2019_mwh, errors="coerce").fillna(0.0); ratio["v"] = pd.to_numeric(ratio.value_2050_mwh, errors="coerce").fillna(0.0)
    out = pd.read_csv(DEM / "INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country")
    reg = pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id")
    return an, t, ratio, out, reg


def test_country_totals_from_aeo8(data):
    an = data[0]; a8 = aeo8_country()
    for c in ASEAN:
        assert rel(an.at[c, "ats_elec_2050_mwh"], a8[c]["elec_pc_kwh"] * a8[c]["pop_2050_million"] * 1e3) < 1e-9
        assert rel(an.at[c, "ats_tfec_2050_mwh"], a8[c]["tfec_pc_kgoe"] * a8[c]["pop_2050_million"] * 1e3 * 11.63) < 1e-9
    assert an.at["TL", "population_2050_million"] == pytest.approx(1.8892495, abs=1e-9)   # UN WPP 2024 median, 1,889,249.5 persons
    assert an.at["TL", "ats_elec_pc_2050_kwh"] == pytest.approx(np.mean([an.at[p, "ats_elec_pc_2050_kwh"] for p in ("KH", "LA", "MM")]))
    assert an.at["VN", "ats_elec_2050_mwh"] / 1e6 == pytest.approx(506.538, abs=1e-3)   # 4,734 kWh x 107.0 M (Table C.8 x D.1)


def test_activity_equals_anchor(data):
    """11 countries: base load, transport and industry (incl. non-energy use) of the ats_anchor table equal the anchors (<= 1e-6), and the anchors equal an
    independent recomputation from the AEO8 sources and the 2019 bases of the ratio table."""
    an, t, ratio, _, _ = data; c3 = c3_ats()
    g_el = {s: c3[s][1] / c3[s][0] for s in SECTORS}; g_el["Residential"] = RES_ELEC_ATS_MTOE[1] / RES_ELEC_ATS_MTOE[0]
    g_t = {s: c3[s][1] / c3[s][0] for s in SECTORS}
    for c in ASEAN:
        m = t.country == c
        bl = float(t[m & (t.carrier == "electricity") & t.sector.isin(BASE_SECTORS)].v.sum())
        tr = float(t[m & (t.sector == "Transport")].v.sum())
        ind = float(t[m & t.sector.isin(["Industry", "NonEnergyUse"])].v.sum())
        assert rel(bl, an.at[c, "base_load_anchor_mwh"]) <= TOL
        assert rel(tr, an.at[c, "transport_anchor_mwh"]) <= TOL
        assert rel(ind, an.at[c, "industry_anchor_mwh"]) <= TOL
        r = ratio[ratio.country == c]
        el19 = {s: float(r[(r.carrier == "electricity") & (r.sector == s)].b.sum()) for s in SECTORS}
        w = {s: el19[s] * g_el[s] for s in SECTORS}
        assert rel(an.at[c, "base_load_anchor_mwh"], an.at[c, "ats_elec_2050_mwh"] * sum(w[s] for s in BASE_SECTORS) / sum(w.values())) <= TOL
        t19 = {s: float(r[r.sector == s].b.sum()) for s in SECTORS}; t19["Industry"] += float(r[r.sector == "NonEnergyUse"].b.sum())
        wt = {s: t19[s] * g_t[s] for s in SECTORS}
        assert rel(an.at[c, "transport_anchor_mwh"], an.at[c, "ats_tfec_2050_mwh"] * wt["Transport"] / sum(wt.values())) <= TOL
    # the anchor table is a row-for-row copy of the ratio table; rows that are not anchored keep their ratio-table values
    assert list(t.country + t.sector + t.carrier + t.account) == list(ratio.country + ratio.sector + ratio.carrier + ratio.account)
    keep = ~(((t.carrier == "electricity") & t.sector.isin(BASE_SECTORS)) | t.sector.isin(["Transport", "Industry", "NonEnergyUse"]))
    assert keep.sum() > 0 and (t.loc[keep, "value_2050_mwh"].values == ratio.loc[keep, "value_2050_mwh"].values).all()


def test_base_loads_nonnegative_and_total(data):
    an, t = data[0], data[1]
    assert (an.base_load_anchor_mwh >= 0).all() and an.base_load_nonnegative.all()
    assert (t[t.sector.isin(BASE_SECTORS) & (t.carrier == "electricity")].v >= 0).all()
    total = an.base_load_anchor_mwh.sum() / 1e6
    assert total == pytest.approx(966.9, abs=0.1)   # S4R supplement 01: 966 TWh (industry 2022 from the BAS panel 185.6; ATS panel 186 here)
    assert (an.transport_fuel_multiplier > 0).all() and (an.industry_multiplier > 0).all()


def test_physical_output_rule(data):
    out = data[3]; g = gdp_growth()
    v = out.loc["VN"]
    assert v.cement_2050_mt == pytest.approx(107.0, abs=1e-9) and v.cement_binding == "per-capita"
    assert v.steel_2050_mt == pytest.approx(40.64, abs=0.01) and v.steel_binding == "growth"   # S4R 40.7 with the WSIF 22.0 Mt base; worldsteel viewer 21.974 Mt
    for c in ASEAN:
        r = out.loc[c]
        for prod, sat in (("cement", 1.0), ("steel", 0.6)):
            by = int(r[f"{prod}_base_year"])
            growth = r[f"{prod}_base_mt"] * max(g[c], 1.0) ** ((2050 - by) / 28 * 0.5)
            plan = float(r[f"{prod}_plan_cap_mt"]) if str(r[f"{prod}_plan_cap_mt"]) not in ("", "nan") else np.inf
            assert r[f"{prod}_2050_mt"] == pytest.approx(min(growth, sat * r.population_2050_million, plan), rel=1e-9)
            assert r[f"{prod}_2050_mt"] <= sat * r.population_2050_million + 1e-9            # every country within the per-capita cap
            assert r[f"{prod}_2050_mt"] <= r[f"{prod}_2050_without_plan_mt"] + 1e-9          # a plan value never raises output
    assert out.loc[["SG", "TL"], "cement_base_mt"].eq(0).all() and out.loc[["BN", "KH", "LA", "TL"], "steel_base_mt"].eq(0).all()
    assert out.at["VN", "cement_base_mt"] == pytest.approx(106.952) and out.at["ID", "steel_base_mt"] == pytest.approx(18.642175)


def test_industry_tables_use_the_rule(data):
    an, out = data[0], data[3]
    for sfx in ("", "_OTHER_USEFUL_HEAT_BANDS", "_TD_SENSITIVITY"):
        s = pd.read_csv(DEM / f"INDUSTRY_2050_SUMMARY_aeo8_ats_anchor{sfx}.csv").set_index("country")
        if "cement_2050_t" in s:
            assert np.allclose(s.cement_2050_t, out.cement_2050_mt.reindex(s.index) * 1e6, rtol=1e-9)
            assert np.allclose(s.crude_steel_2050_t, out.steel_2050_mt.reindex(s.index) * 1e6, rtol=1e-9)
            assert np.allclose(s.industry_multiplier, an.industry_multiplier.reindex(s.index), rtol=1e-9)


def test_switch_validation():
    from phase4_static import config
    cfg = config(ROOT, "integrated")
    assert demand_table_key(cfg) == "aeo8_ats_anchor" and demand_anchor_settings(cfg)["base_load_anchor"] == "ats_buildings_agri"
    assert physical_output_settings(cfg, ROOT)["rule"] == "sqrt_gdp_capped"
    bad = []
    c = copy.deepcopy(cfg); c["research"]["demand"]["base_load_anchor"] = "table"; bad.append(lambda c=c: demand_anchor_settings(c))
    c = copy.deepcopy(cfg); c["research"]["demand"]["country_allocation"] = "gdp"; bad.append(lambda c=c: demand_anchor_settings(c))
    c = copy.deepcopy(cfg); c["research"]["demand"]["growth_method"] = "ratio"; bad.append(lambda c=c: physical_output_settings(c, ROOT))   # rule needs ats_anchor
    c = copy.deepcopy(cfg); c["research"]["s2"]["industry"]["physical_output_elasticity"] = 0.3; bad.append(lambda c=c: physical_output_settings(c, ROOT))   # tables made with 0.5
    for f in bad:
        with pytest.raises(ValueError):
            f()
    c = copy.deepcopy(cfg); c["research"]["demand"].update(growth_method="ratio", base_load_anchor="table", transport_anchor="table")
    c["research"]["s2"]["industry"]["physical_output_rule"] = "industry_multiplier"
    assert demand_table_key(c) == "aeo8_ats_relative" and physical_output_settings(c, ROOT)["rule"] == "industry_multiplier"


def test_registry_rows(data):
    reg = data[4]
    for pid in ["demand_anchor_family_main", "demand_base_load_rule", "demand_transport_anchor_rule", "demand_industry_electricity_not_anchored", "demand_anchor_family_control",
                "demand_anchor_tl_rule", "industry_output_rule_2050", "industry_output_base_year", "industry_output_elasticity", "industry_percap_saturation_cement",
                "industry_percap_saturation_steel", "industry_cement_2050_VN", "industry_steel_2050_VN", "industry_output_plan_sensitivity_VN"]:
        assert pid in reg.index and reg.at[pid, "status"] in ("REGISTERED", "SOURCE_ZERO"), pid
    assert reg.at["industry_output_rule_2050", "value"] == "sqrt_gdp_capped" and reg.at["demand_anchor_family_main", "value"] == "aeo8_ats"
    assert float(reg.at["industry_cement_2050_VN", "value"]) == pytest.approx(107.0) and float(reg.at["industry_steel_2050_VN", "value"]) / 1e6 == pytest.approx(40.64, abs=0.01)
    for pid in ["demand_country_allocation_mode", "demand_growth_method", "s4j1_base_load_sectors"]:
        assert reg.at[pid, "status"] == "REFERENCE_ONLY" and "[M08b B1] 历史" in reg.at[pid, "description"]
    for c in ASEAN:
        for g in ("minerals", "metals", "chemicals"):
            assert f"process_emissions_{g}_2050_ats_anchor_{c}" in reg.index
