"""M08a A1 / M08-1 (decision 131): technology-data v0.15.0 rebased with the EEA HICP rate of change (no network build, no solve)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from d1_common import (HICP_DOWNLOAD_FILE, HICP_EEA_ROW, HICP_TD_FILE, HICP_US_ROW, eurostat_download_rates,   # noqa: E402
                       hicp_factor, hicp_rates)
from s2_costs import layer_files, load_active_layer   # noqa: E402

COST = ROOT / "research_inputs" / "cost_layers_v5"
MAIN = COST / "technology_data_v0.15.0_EUR2020"
EA20 = COST / "technology_data_v0.15.0_EUR2020_ea20gdp"
CFG = yaml.safe_load((ROOT / "configs" / "research" / "baseline.yaml").read_text())


def test_td_inflation_rule_mirrored():
    eea = hicp_rates(HICP_TD_FILE, HICP_EEA_ROW)
    assert [round(eea[y] * 100, 6) for y in range(2021, 2026)] == [2.9, 9.2, 6.4, 2.6, 2.5]
    up = hicp_factor(eea, 2020, 2025)   # technology-data get_factor(rates, 2020, 2025): its inflation EUR2020 -> EUR2025
    assert up == pytest.approx(1.25733, abs=5e-6)
    assert hicp_factor(eea, 2025, 2020) * up == pytest.approx(1.0, rel=1e-12)
    assert hicp_factor(eea, 2019, 2020) == pytest.approx(1.007, rel=1e-12)
    us = hicp_rates(HICP_TD_FILE, HICP_US_ROW)
    assert 2025 not in us   # filled with the series mean, as technology-data does
    mean = sum(us.values()) / len(us)
    assert hicp_factor(us, 2025, 2020) == pytest.approx(1 / np.prod([1 + us[y] for y in range(2021, 2025)] + [1 + mean]), rel=1e-12)


def test_download_cross_check_identical_rates():
    eea = hicp_rates(HICP_TD_FILE, HICP_EEA_ROW)
    dl = eurostat_download_rates(HICP_DOWNLOAD_FILE, "Sheet 6", HICP_EEA_ROW)
    assert all(dl[y] == pytest.approx(eea[y], abs=1e-12) for y in range(2021, 2026))


def test_rebase_factor_times_td_inflation_is_one():
    """Instruction A1: rebase factor x technology-data inflation factor = 1 (+-0.1 %): by the rule and on the data."""
    m = json.loads((MAIN / "LAYER_MANIFEST.json").read_text())
    assert m["rebase"]["index"] == "eea_hicp_rate" and m["rebase_index"] == "eea_hicp_rate"
    assert m["rebase"]["factor_2025_to_2020"] * m["rebase"]["eea_inflation_factor_2020_2025"] == pytest.approx(1.0, rel=1e-3)
    assert m["rebase"]["cross_check"]["identical_2021_2025"] is True
    # observed: rows whose source did not change between v0.13.2 (EUR2020) and v0.15.0 (EUR2025) come back to their v0.13.2 value
    cmp = pd.read_csv(MAIN / "COMPARISON_v0.13.2_vs_v0.15.0_EUR2020.csv").set_index(["technology", "parameter"])
    for k in [("electrolysis", "investment"), ("solar-utility", "investment"), ("nuclear", "investment"), ("battery storage", "investment"),
              ("coal", "investment"), ("offwind", "investment"), ("direct air capture", "investment")]:
        r = cmp.loc[k]
        assert r.v0_15_0_eur2020 / r.v0_13_2_eur2020 == pytest.approx(1.0, rel=1e-3), k
        # and the inverse view: published EUR2025 value / v0.13.2 EUR2020 value = technology-data inflation factor
        assert (r.v0_15_0_as_published / r.v0_13_2_eur2020) * m["rebase"]["factor_2025_to_2020"] == pytest.approx(1.0, rel=1e-3), k


def test_non_monetary_rows_unchanged_and_monetary_rows_rebased():
    long = pd.read_csv(MAIN / "costs_2050_EUR2020.csv")
    old = pd.read_csv(EA20 / "costs_2050_EUR2020.csv")
    non = long[~long.monetary]
    assert len(non) > 0 and (non.conversion_factor == 1.0).all() and np.array_equal(non.value.to_numpy(), non.value_v0_15_0.to_numpy())
    assert np.array_equal(non.value.to_numpy(), old[~old.monetary].value.to_numpy())
    mon = long[long.monetary]
    f = 1 / 1.029 / 1.092 / 1.064 / 1.026 / 1.025
    eur25 = mon[(mon.source_currency_year == 2025) & ~mon.unit.str.contains("USD")]
    assert np.allclose(eur25.conversion_factor, f, rtol=1e-12) and len(eur25) == 369
    assert np.allclose(mon[mon.source_currency_year == 2019].conversion_factor, 1.007)
    assert (mon[mon.source_currency_year == 2020].conversion_factor == 1.0).all()
    usd = mon[mon.unit.str.contains("USD")]
    assert len(usd) == 5 and not np.allclose(usd.conversion_factor, f)
    assert np.allclose(mon.value, mon.value_v0_15_0 * mon.conversion_factor, rtol=1e-11)


def test_comparison_variant_is_former_rebase():
    m = json.loads((EA20 / "LAYER_MANIFEST.json").read_text())
    assert m["rebase"]["index"] == "ea20_gdp_deflator"
    old = pd.read_csv(EA20 / "costs_2050_EUR2020.csv")
    mon = old[old.monetary & (old.source_currency_year == 2025)]
    assert np.allclose(mon.conversion_factor, 100.0 / 120.01983244779059, rtol=1e-12)   # USD rows included (former behaviour)


def test_config_key_default_and_resolver():
    spec = CFG["research"]["cost_layer"]["layers"]["technology_data_v0_15_0_2050_eur2020"]
    assert spec["rebase_index"] == "eea_hicp_rate"
    assert set(spec["rebase_variants"]) == {"eea_hicp_rate", "ea20_gdp_deflator"}
    assert layer_files(spec)["prepared_file"].endswith("technology_data_v0.15.0_EUR2020/costs_2050_EUR2020_prepared.csv")
    alt = dict(spec, rebase_index="ea20_gdp_deflator")
    assert "_ea20gdp/" in layer_files(alt)["prepared_file"]
    with pytest.raises(ValueError):
        layer_files(dict(spec, rebase_index="hicp_ea"))
    name, s, man, wide = load_active_layer(ROOT, CFG)
    assert man["rebase"]["index"] == "eea_hicp_rate" and "electrolysis" in wide.index
    cfg = copy.deepcopy(CFG)
    cfg["research"]["cost_layer"]["layers"]["technology_data_v0_15_0_2050_eur2020"]["rebase_index"] = "ea20_gdp_deflator"
    _, _, man2, wide2 = load_active_layer(ROOT, cfg)
    assert man2["rebase"]["index"] == "ea20_gdp_deflator"
    assert float(wide2.at["electrolysis", "investment"]) / float(wide.at["electrolysis", "investment"]) == pytest.approx(1.2573346 / 1.2001983, rel=1e-6)
    bad = copy.deepcopy(CFG)   # a variant entry pointing at the other variant's manifest is refused
    lay = bad["research"]["cost_layer"]["layers"]["technology_data_v0_15_0_2050_eur2020"]
    lay["rebase_variants"]["eea_hicp_rate"] = dict(lay["rebase_variants"]["ea20_gdp_deflator"])
    with pytest.raises(ValueError):
        load_active_layer(ROOT, bad)
