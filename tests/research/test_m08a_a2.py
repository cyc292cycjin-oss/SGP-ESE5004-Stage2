"""M08a A2 / M08-2 (decision 131): nuclear from one source (SMR = technology-data nuclear x AEO8 D.15 ratios) and the
AEO8 price-year factor (no network build, no solve)."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
REG = ROOT / "research_inputs" / "registry_v5" / "DATA_REGISTRY.csv"
pytestmark = pytest.mark.skipif(not REG.exists(), reason="registry not built")


@pytest.fixture(scope="module")
def cfg():
    from phase4_static import config
    return config(ROOT, "integrated")


def build(cfg):
    from s2_costs import build_research_costs
    return build_research_costs(ROOT, cfg, REG)


def test_smr_equals_nuclear_times_aeo8_ratios(cfg):
    assert cfg["research"]["cost_layer"]["smr_cost_source"] == "td_nuclear_x_aeo8_ratio"
    c, ledger = build(cfg)
    nuc, smr = c.loc["nuclear"], c.loc["nuclear SMR"]
    assert smr.investment == pytest.approx(nuc.investment * 1.0667, rel=1e-4)            # instruction A2
    assert smr.investment == pytest.approx(nuc.investment * 9600 / 9000, rel=1e-12)
    assert smr.FOM == pytest.approx(nuc.FOM * 1.37, rel=1e-3) and smr.FOM == pytest.approx(nuc.FOM * (110.0 / 9600) / (75.3 / 9000), rel=1e-12)
    assert smr.VOM == pytest.approx(nuc.VOM * 0.43, rel=4e-3) and smr.VOM == pytest.approx(nuc.VOM * 2.2 / 5.1, rel=1e-12)
    assert (smr.lifetime, smr.efficiency, smr["discount rate"]) == (nuc.lifetime, nuc.efficiency, nuc["discount rate"])
    assert smr.fuel == pytest.approx(c.at["uranium", "fuel"])
    r = smr["discount rate"]
    assert smr.fixed == pytest.approx((r / (1 - (1 + r) ** -smr.lifetime) + smr.FOM / 100) * smr.investment, rel=1e-12)
    assert ledger["smr_rule"]["source"] == "td_nuclear_x_aeo8_ratio"
    # ratios are dimensionless (same table): the SMR / nuclear investment ratio does not depend on the rebase index
    alt = copy.deepcopy(cfg)
    alt["research"]["cost_layer"]["layers"]["technology_data_v0_15_0_2050_eur2020"]["rebase_index"] = "ea20_gdp_deflator"
    c2, _ = build(alt)
    assert c2.at["nuclear SMR", "investment"] / c2.at["nuclear", "investment"] == pytest.approx(9600 / 9000, rel=1e-12)


def test_former_smr_source_and_price_year_factor(cfg):
    old = copy.deepcopy(cfg)
    old["research"]["cost_layer"]["smr_cost_source"] = "aeo8_author_rule_2050"
    c, _ = build(old)
    assert c.at["nuclear SMR", "investment"] == pytest.approx(8421394.8727, rel=1e-6)   # AEO8 9,600 kUSD/MW x ECB 2020 FX (former main)
    assert cfg["research"]["cost_layer"]["aeo8_price_year_factor"] == 1.0
    base, _ = build(cfg)
    s = copy.deepcopy(cfg); s["research"]["cost_layer"]["aeo8_price_year_factor"] = 0.86
    c86, led = build(s)
    assert c86.at["geothermal", "investment"] == pytest.approx(base.at["geothermal", "investment"] * 0.86, rel=1e-12)
    assert c86.at["geothermal", "FOM"] == base.at["geothermal", "FOM"] and c86.at["geothermal", "VOM"] == base.at["geothermal", "VOM"]
    assert c86.at["nuclear SMR", "investment"] == base.at["nuclear SMR", "investment"]   # main SMR rule is currency-neutral
    assert c86.at["geothermal", "aeo8_price_year_factor"] == 0.86 and led["aeo8_price_year_factor"] == 0.86
    # existing-geothermal FOM constant keeps the unscaled basis (s2_layers.add_existing_geothermal divides the factor out)
    assert c86.at["geothermal", "FOM"] / 100 * c86.at["geothermal", "investment"] / 0.86 == pytest.approx(base.at["geothermal", "FOM"] / 100 * base.at["geothermal", "investment"], rel=1e-12)
    old86 = copy.deepcopy(old); old86["research"]["cost_layer"]["aeo8_price_year_factor"] = 0.86
    co, _ = build(old86)
    assert co.at["nuclear SMR", "investment"] == pytest.approx(8421394.8727 * 0.86, rel=1e-6)
    bad = copy.deepcopy(cfg); bad["research"]["cost_layer"]["smr_cost_source"] = "inl_atb"
    with pytest.raises(ValueError):
        build(bad)


def test_registry_rows():
    r = pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id")
    assert r.loc["nuclear_cost_rule", "value"] == "td_nuclear_x_aeo8_ratio" and r.loc["nuclear_cost_rule", "status"] == "REGISTERED"
    assert float(r.loc["smr_ratio_aeo8_investment", "value"]) == pytest.approx(9600 / 9000, rel=1e-10)   # registry values carry 12 significant digits
    assert r.loc["aeo8_cost_price_year", "status"] == "DATA_PENDING"
    assert float(r.loc["aeo8_price_year_factor_main", "sensitivity_low"]) == 0.86
    for pid in ("smr_investment", "smr_FOM", "smr_VOM"):
        assert r.loc[pid, "status"] == "REFERENCE_ONLY" and "历史：已被 nuclear_cost_rule 替代" in r.loc[pid, "description"]
