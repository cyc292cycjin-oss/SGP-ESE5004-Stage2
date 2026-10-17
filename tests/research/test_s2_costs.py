"""S2-1 cost table: active layer v0.15.0 (EUR2020), WEO 2025 fuel prices (decision 33; STEPS main since S4C-0, decision 85), AEO8 SMR/geothermal rows, FT unit handling."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
REG = ROOT / "research_inputs" / "registry_v5" / "DATA_REGISTRY.csv"
pytestmark = pytest.mark.skipif(not REG.exists(), reason="registry not built")


@pytest.fixture(scope="module")
def costs():
    from phase4_static import config
    from s2_costs import build_research_costs
    cfg = config(ROOT, "integrated")
    return build_research_costs(ROOT, cfg, REG)


def annuity(n, r):
    return r / (1.0 - 1.0 / (1.0 + r) ** n)


def test_fuel_prices_are_weo_steps_not_layer(costs):
    # S4C-0 (decision 85, modifies decision 33): main = WEO 2025 STEPS 2050 for gas, oil and coal
    c, ledger = costs
    reg = pd.read_csv(REG)
    for tech in ["gas", "oil", "coal"]:
        want = float(reg.loc[reg.param_id == f"fuel_price_{tech}_STEPS_2050_high_price", "value"].iloc[0])
        assert c.at[tech, "fuel"] == pytest.approx(want, rel=1e-9)
    assert {o["technology"] for o in ledger["overrides"]} == {"gas", "oil", "coal"} and ledger["fuel_price_scenario"] == "steps"
    assert c.at["gas", "fuel"] == pytest.approx(27.069, abs=1e-3) and c.at["oil", "fuel"] == pytest.approx(35.318, abs=1e-3) and c.at["coal", "fuel"] == pytest.approx(8.861, abs=1e-3)


def test_fuel_price_scenario_switch_nze_and_bad_value():
    import copy
    from phase4_static import config
    from s2_costs import build_research_costs, fuel_price_ids
    cfg = config(ROOT, "integrated"); low = copy.deepcopy(cfg); low["research"]["fuels"]["price_scenario"] = "nze"
    c, ledger = build_research_costs(ROOT, low, REG)
    assert c.at["gas", "fuel"] == pytest.approx(13.674, abs=1e-3) and c.at["oil", "fuel"] == pytest.approx(11.618, abs=1e-3) and c.at["coal", "fuel"] == pytest.approx(5.169, abs=1e-3)
    assert set(fuel_price_ids(low).values()) == {f"fuel_price_{t}_NZE_2050_main" for t in ["gas", "oil", "coal"]}
    bad = copy.deepcopy(cfg); bad["research"]["fuels"]["price_scenario"] = "mixed"
    with pytest.raises(ValueError):
        fuel_price_ids(bad)


def test_fischer_tropsch_new_unit(costs):
    c, ledger = costs
    # v0.15.0 labels the FT investment 'EUR/kW_FT/year' (1,203.34 EUR2025); treated as EUR/kW_FT total investment -> x1e3 per MW, annualised
    inv = c.at["Fischer-Tropsch", "investment"]
    assert inv == pytest.approx(1203.3447 * 0.83319563076 * 1e3, rel=1e-6)
    assert c.at["Fischer-Tropsch", "fixed"] == pytest.approx((annuity(25, 0.07) + 6.5778 / 100) * inv, rel=1e-6)
    assert c.at["Fischer-Tropsch", "efficiency"] == pytest.approx(0.754) and c.at["Fischer-Tropsch", "lifetime"] == 25
    assert any("Fischer-Tropsch" in n for n in ledger.get("notes", []))


def test_smr_and_geothermal_rows(costs):
    c, ledger = costs
    assert c.at["nuclear SMR", "investment"] == pytest.approx(8421394.8727, rel=1e-6) and c.at["nuclear SMR", "lifetime"] == 40
    assert c.at["nuclear SMR", "fuel"] == pytest.approx(c.at["uranium", "fuel"]) and c.at["nuclear SMR", "efficiency"] == pytest.approx(0.326)
    assert c.at["geothermal", "investment"] == pytest.approx(4100e3 * 0.877229, rel=1e-4) and c.at["geothermal", "lifetime"] == 30
    assert c.at["geothermal", "FOM"] == pytest.approx(19.5 / 4100 * 100, rel=1e-6)
    assert ledger["layer"] == "technology_data_v0_15_0_2050_eur2020"
    assert c.at["onwind", "investment"] == pytest.approx(1286.4669 * 0.83319563076 * 1e3, rel=1e-6)
