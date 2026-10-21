"""M08b B2 / M08-6 (decision 133): useful-heat bands of the other-industry bucket and the biomass overflow as useful heat (no build, no solve)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pypsa
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s2_layers import HEAT_BAND_TECH, add_industrial_heat, biomass_overflow   # noqa: E402

DEM = ROOT / "research_inputs" / "demand_v5"
REG = ROOT / "research_inputs" / "registry_v5" / "DATA_REGISTRY.csv"
COSTS = ROOT / "research_inputs" / "cost_layers_v5" / "technology_data_v0.15.0_EUR2020" / "costs_2050_EUR2020_prepared.csv"
MODES = ["aeo8_ats_anchor", "aeo8_ats_relative", "gdp", "population", "aeo8_ats_relative_level"]
FUELS = ["coal", "oil", "gas", "biomass"]


@pytest.fixture(scope="module")
def bands():
    return pd.read_csv(DEM / "INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.csv").set_index("carrier")


def test_band_shares(bands):
    s = bands[["share_low", "share_medium", "share_high", "share_mechanical"]]
    assert list(bands.index) == FUELS and ((s.sum(axis=1) - 1.0).abs() < 1e-9).all() and (s >= 0).all().all()
    assert bands.at["biomass", "share_high"] == 0 and bands.at["oil", "share_mechanical"] > 0.3   # JRC OIS: no biomass in thermal processing; diesel motors
    assert bands.at["coal", "share_high"] > 0.7 and bands.at["coal", "share_mechanical"] == 0


@pytest.mark.parametrize("mode", MODES)
def test_useful_heat_equals_energy_times_efficiency(mode, bands):
    """sum of the three bands = original other-bucket fuel energy (heat uses) x efficiency, recomputed from the other-bucket 2019 table x multiplier."""
    s = pd.read_csv(DEM / f"INDUSTRY_2050_SUMMARY_{mode}_OTHER_USEFUL_HEAT_BANDS.csv").set_index("country")
    ob = pd.read_csv(DEM / "INDUSTRY_2050_OTHER_BUCKET.csv"); ob = ob[ob["mode"] == mode].set_index("country")
    for c in s.index:
        r = s.loc[c]
        total = r.other_heat_low_mwh + r.other_heat_medium_mwh + r.other_heat_high_mwh
        assert total == pytest.approx(r.other_heat_fuel_2050_mwh * r.useful_heat_efficiency, rel=1e-9, abs=1e-6)
        heat_fuel = sum(ob.at[c, f"other_2019_{car}_mwh"] * ob.at[c, "industry_multiplier"] * (1 - bands.at[car, "share_mechanical"]) for car in FUELS)
        assert r.other_heat_fuel_2050_mwh == pytest.approx(heat_fuel, rel=1e-9, abs=1e-6)
        for band in ("medium", "high"):
            want = sum(ob.at[c, f"other_2019_{car}_mwh"] * ob.at[c, "industry_multiplier"] * bands.at[car, f"share_{band}"] for car in FUELS) * 0.90
            assert r[f"pe_heat_{band}_mwh"] == pytest.approx(want, rel=1e-9, abs=1e-6)
        assert r.useful_heat_efficiency == 0.90 and r.biomass_overflow_industry_to_gas_mwh == 0 and r.biomass_overflow_agriculture_to_gas_mwh == 0


def test_fixed_biomass_within_pool():
    """biomass_overflow keeps the fixed solid-biomass demand <= the national pool (cap = potential in useful_heat mode); the overflow becomes useful heat x 0.90."""
    for ind, ag, pot in [(233e6, 19e6, 125.8e6), (0.0, 0.2e6, 0.03e6), (22e6, 19e6, 125.8e6), (5.0, 0.0, 0.0), (10.0, 10.0, 20.0)]:
        ov_i, ov_a, cap, _ = biomass_overflow(ind, ag, pot)
        assert cap == pot and ind + ag - ov_i - ov_a <= pot + 1e-6 and ov_i <= ind and ov_a <= ag and ov_i >= 0 and ov_a >= 0
        assert (ov_i + ov_a) == pytest.approx(max(0.0, ind + ag - pot))
    ov_i, ov_a, cap, b = biomass_overflow(10.0, 0.0, 10.0, cap_share=0.98)   # historical methane mode (decision 115): 2 % below the potential where binding
    assert b and cap == pytest.approx(9.8) and ov_i == pytest.approx(0.2)
    for mode in MODES:   # the industry tables of every allocation: fixed demand after the overflow within the pool
        s = pd.read_csv(DEM / f"INDUSTRY_2050_SUMMARY_{mode}_OTHER_USEFUL_HEAT_BANDS.csv").set_index("country")
        for c in s.index:
            r = s.loc[c]
            ov_i, ov_a, _, _ = biomass_overflow(r.pe_biomass_before_overflow_mwh, r.agriculture_biomass_2050_mwh, r.solid_biomass_potential_main_mwh)
            assert r.pe_biomass_before_overflow_mwh + r.agriculture_biomass_2050_mwh - ov_i - ov_a <= r.solid_biomass_potential_main_mwh + 1e-6
            assert ov_i == pytest.approx(r.biomass_overflow_industry_mwh, rel=1e-9, abs=1e-6) and ov_a == pytest.approx(r.biomass_overflow_agriculture_mwh, rel=1e-9, abs=1e-6)


def test_band_technology_map():
    costs = pd.read_csv(COSTS, index_col=0)
    for band, techs in HEAT_BAND_TECH.items():
        for tech, carrier, fuel in techs:
            assert tech in costs.index, tech                       # decision 133: only technology-data v0.15.0 rows
            assert fuel in ("electricity", "gas", "biomass")       # no hydrogen row in technology-data v0.15.0
    assert all(f != "electricity" for _, _, f in HEAT_BAND_TECH["high"])   # no electric heating above 400 C (no covering row)
    assert [b for b, ts in HEAT_BAND_TECH.items() if any("heat pump" in t for t, _, _ in ts)] == ["low"]
    assert not any("hydrogen" in t.lower() or "h2" in t.lower() for ts in HEAT_BAND_TECH.values() for t, _, _ in ts)


def test_high_band_links_on_a_network():
    """add_industrial_heat(bands=True) on a two-node network: no link from an electricity bus (or H2) into a high-band bus; low band unchanged."""
    costs = pd.read_csv(COSTS, index_col=0)
    n = pypsa.Network(); n.set_snapshots([0])
    for node in ["N1", "N2"]:
        n.add("Bus", node, carrier="AC"); n.buses.loc[node, "country"] = "VN"
    n1 = pypsa.Network(); n1.set_snapshots([0])
    for node in ["N1", "N2"]:
        n1.add("Bus", node, carrier="AC"); n1.buses.loc[node, "country"] = "VN"
    led = add_industrial_heat(n, costs, ["N1", "N2"], 0.9, bands=True)
    add_industrial_heat(n1, costs, ["N1", "N2"], 0.9, bands=False)
    lk = n.links
    high = lk[lk.bus1.str.endswith("industry heat high")]
    assert len(high) == 6 and not high.bus0.isin(["N1", "N2"]).any() and not high.bus0.str.contains("H2").any()
    assert set(high.carrier) == {"industry direct firing gas", "industry direct firing biomass", "industry direct firing biomass CC"}
    med = lk[lk.bus1.str.endswith("industry heat medium")]
    assert len(med) == 8 and "industry heat pump" not in set(med.carrier)
    low = lk[lk.bus1.str.endswith(" industry heat")]
    assert list(low.index) and set(low.index) == set(n1.links.index) and "heat_band" not in n1.links
    assert led["supply_links"] == 2 * (5 + 4 + 3) and "no hydrogen heating" in led["excluded"]


def test_registry_and_config():
    reg = pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id")
    for pid in ["biomass_overflow_rule", "industry_route_mode_proposed", "industry_heat_band_technology_map", "industry_other_bucket_heat_band_shares"]:
        assert pid in reg.index and reg.at[pid, "status"] == "REGISTERED", pid
    for c in ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "TL", "VN"]:
        assert reg.at[f"industry_biomass_overflow_to_gas_{c}", "status"] == "REFERENCE_ONLY"
    assert reg.at["s4m_decision_115_biomass_cap_share", "status"] == "REFERENCE_ONLY" and reg.at["industry_other_bucket_mode", "status"] == "REFERENCE_ONLY"
    from phase4_static import config
    I = config(ROOT, "integrated")["research"]["s2"]["industry"]
    assert I["biomass_overflow_mode"] == "useful_heat" and "biomass_overflow_cap_share" not in I and "biomass_overflow_to_methane" not in I
    assert I["biomass_overflow_useful_heat_efficiency"] == 0.90 and I["heat_bands"]
