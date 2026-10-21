"""S3B R1 (decision 66): ratio growth method (main) and level method (sensitivity) for the 2050 demand."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
DEM = ROOT / "research_inputs" / "demand_v5"
REG = ROOT / "research_inputs" / "registry_v5"


def test_growth_method_switch_and_tables():
    from phase4_static import config
    from s2_layers import demand_table_key
    cfg = config(ROOT, "integrated")
    D = cfg["research"]["demand"]
    assert D["growth_method"] == "ats_anchor" and demand_table_key(cfg) == "aeo8_ats_anchor"   # M08b B1 (decision 134): new main; ratio / level stay selectable
    c2 = copy.deepcopy(cfg); c2["research"]["demand"]["growth_method"] = "ratio"
    assert demand_table_key(c2) == "aeo8_ats_relative"
    c2["research"]["demand"]["growth_method"] = "level"
    assert demand_table_key(c2) == "aeo8_ats_relative_level"
    c2["research"]["demand"]["growth_method"] = "x"
    with pytest.raises(ValueError):
        demand_table_key(c2)
    for path in [cfg["research"]["s2"]["demand"]["tables_by_allocation"]["aeo8_ats_relative_level"], cfg["research"]["s2"]["industry"]["pypsa_eur_tables"]["aeo8_ats_relative_level"], cfg["research"]["s2"]["industry"]["territorial_tables"]["aeo8_ats_relative_level"]]:
        assert (ROOT / path).exists()
    for f in ["INDUSTRY_2050_SUMMARY_aeo8_ats_relative_level.csv", "INDUSTRY_2050_SUMMARY_aeo8_ats_relative_level_TD_SENSITIVITY.csv"]:
        assert (DEM / f).exists()
    assert (REG / "FEEDSTOCK_CARBON_TERRITORIAL_2050_aeo8_ats_relative_level.csv").exists()


def test_bridge_basis_gap_and_shipping_chain():
    r1 = json.loads((DEM / "DEMAND_2050_R1_GROWTH_METHOD.json").read_text())["r1"]
    b = r1["bridge"]
    assert b["tfec_2019_mtoe_derived"] == pytest.approx(156.2 / 0.384)
    assert b["bridge_main"]["Industry"] == pytest.approx(185.6 / 156.2) and b["bridge_main"]["Transport"] == pytest.approx(145.2 / (0.36 * 156.2 / 0.384))
    lo, hi = b["transport_bridge_range"]
    assert lo < b["bridge_main"]["Transport"] < hi
    assert all(b["bridge_main"][s] == 1.0 for s in ["Residential", "Commercial", "AgricultureOthers"])
    assert 1.0 < b["wdi_gdp_growth_2019_2022_asean10"] < 1.1
    gap = {r["sector"]: r for r in r1["basis_gap"]}
    assert 1.45 < gap["Transport"]["basis_gap_main"] < 1.47   # instruction: transport about 1.45
    for s, r in gap.items():
        assert r["basis_gap_main"] == pytest.approx(r["level_over_ratio"], rel=1e-9)   # level / ratio = AEO8 2022 / (UNSD 2019 x bridge)
    sc = r1["shipping_chain"]
    tot = lambda k: (sc[k]["domestic_mwh"] + sc[k]["international_mwh"]) / 1e6
    assert tot("s2_level_gdp_allocation") == pytest.approx(670.18, abs=0.01) and tot("r3_level_aeo8_allocation") == pytest.approx(651.19, abs=0.01)
    assert tot("s3b_ratio_aeo8_allocation") == pytest.approx(621.99, abs=0.01)
    assert sc["s2_level_gdp_allocation"]["international_mwh"] == sc["s3b_ratio_aeo8_allocation"]["international_mwh"]   # bunkers constant 2019


def test_level_file_equals_level_calibration_and_registry():
    lvl = pd.read_csv(DEM / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_LEVEL_SENSITIVITY.csv", keep_default_na=False)
    main = pd.read_csv(DEM / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", keep_default_na=False)
    assert len(lvl) == len(main) and (main.growth_method[main.sector == "Transport"].str.startswith("ratio")).all()
    r = pd.read_csv(REG / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    assert r.loc["demand_growth_method", "value"] == "ratio" and r.loc["demand_bridge_2019_2022_Transport", "tier"] == "C"
    assert r.loc["demand_base_year", "value"] == "2019"
    ind = lambda d, c: float(d[(d.country == c) & (d.sector == "Industry")].multiplier_total.astype(float).iloc[0])
    for c in ["ID", "VN"]:
        main_v = float(r.loc[f"process_emissions_minerals_2050_{c}", "value"]) if f"process_emissions_minerals_2050_{c}" in r.index else None
        if main_v:
            assert float(r.loc[f"process_emissions_minerals_2050_level_{c}", "value"]) == pytest.approx(main_v * ind(lvl, c) / ind(main, c), rel=1e-9)
