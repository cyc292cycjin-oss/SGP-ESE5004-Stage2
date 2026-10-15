"""S2 structure tests on the built (unsolved) scenario networks and receipts; skipped when the builds are absent."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
OUT = ROOT / "results_project" / "s2b"   # S2 supplement 02 rebuild (R1-R7)
INT = OUT / "integrated" / "integrated_2920_3h_unsolved.nc"
DIS = OUT / "disconnected" / "disconnected_2920_3h_unsolved.nc"
pytestmark = pytest.mark.skipif(not INT.exists() or not DIS.exists(), reason="S2 networks not built")


@pytest.fixture(scope="module")
def nets():
    import pypsa
    return pypsa.Network(str(INT)), pypsa.Network(str(DIS))


@pytest.fixture(scope="module")
def receipts():
    return (json.loads((OUT / "integrated" / "integrated_BUILD_RECEIPT.json").read_text()),
            json.loads((OUT / "disconnected" / "disconnected_BUILD_RECEIPT.json").read_text()))


def test_s2_status_and_switches(nets, receipts):
    ni, nd = nets; ri, rd = receipts
    assert ni.meta["skeleton_status"] == "S2_SECTOR_COUPLED_SMOKE" and ni.meta["solver_allowed"] is False
    assert ri["status"] == rd["status"] == "S2_SCENARIO_BUILT_STATIC_PASS"
    assert ri["cross_border"]["co2"]["switch"] is True and rd["cross_border"]["co2"]["switch"] is False
    assert (ni.links.carrier == "CO2 pipeline").sum() - (nd.links.carrier == "CO2 pipeline").sum() == rd["cross_border"]["co2"]["removed_count"]
    assert "border_class" in nd.links and not ((nd.links.border_class == "cross_border") & (nd.links.carrier == "CO2 pipeline")).any()
    assert ri["transmission_limit"]["mode"] == "lvopt" and "lv_limit" not in ni.global_constraints.index


def test_s2_co2_two_layer_storage(nets, receipts):
    ni, _ = nets; ri, _ = receipts
    seq = ni.stores[ni.stores.carrier == "co2 sequestered"]
    assert sorted(seq.country) == ["BN", "ID", "KH", "MY", "PH", "TH", "TL", "VN"]  # decision 30: LA, MM, SG have no store
    caps = ni.meta["research_co2_storage"]["caps_t_per_year"]
    for name, z in seq.iterrows():
        assert z.e_nom_max == pytest.approx(caps[z.country]) and ni.meta["store_power_rules"][name] == "charge_only"
    assert caps["MY"] == pytest.approx(128.773e9 / 50, rel=1e-6) and caps["SG"] == 0.0
    buffers = ni.stores[ni.stores.carrier == "co2 stored"]
    assert len(buffers) == 97 and buffers.e_cyclic.all()
    for carrier in ["CCGT CC", "DAC", "process emissions CC", "biomass EOP CC", "biogas upgrading", "BtL", "co2 vent", "CO2 sequestration"]:
        assert (ni.links.carrier == carrier).any(), carrier
    dac = ni.links[ni.links.carrier == "DAC"].iloc[0]
    assert dac.bus0.endswith(" ") is False and ni.buses.at[dac.bus0, "carrier"] in ("AC", "DC") and dac.bus1.endswith(" co2 stored") and dac.efficiency2 < 0 and dac.bus3.endswith(" industry heat")  # R6
    assert "research_co2_storage_cap" in ni.meta["required_constraint_hooks"]


def test_s2_biomass_pools(nets, receipts):
    ni, _ = nets; ri, _ = receipts
    pools = ni.stores[ni.stores.research_role == "FINITE_RESOURCE"]
    assert len(pools) == ri["static_validation"]["s2"]["biomass_stores"] and not pools.e_nom_extendable.any()
    assert all(ni.meta["store_power_rules"][s] == "discharge_only" for s in pools.index)
    assert not any("logging" in s for s in pools.index)
    assert set(ni.buses[ni.buses.carrier == "solid biomass"].country) == set("BN KH ID LA MY MM PH SG TH TL VN".split())
    assert not (ni.links.carrier == "solid biomass transport").any()  # decision 36: no cross-border biomass


def test_s2_demand_ownership_and_deductions(nets, receipts):
    ni, _ = nets; ri, _ = receipts
    assert set(ni.meta["demand_owners"]) == set(ni.loads.index)
    kinds = ni.loads.demand_owner_kind.value_counts().to_dict()
    assert kinds["REGISTRY"] == 96 and kinds["S2_DEMAND_TABLE"] == len(ni.loads) - 96
    ded = {d["country"]: d for d in ri["demand_s2"]["deductions"]}
    assert ded["SG"]["deducted_mwh"] > 0 and ded["SG"]["astar_after_mwh"] == pytest.approx(ded["SG"]["astar_before_mwh"] - ded["SG"]["deducted_mwh"], rel=1e-9)
    assert all(d["account"] in ("DomesticShippingFuel", "InternationalShippingBunker") for d in ri["demand_s2"]["deferred"])
    assert (ni.loads.carrier == "land transport EV").sum() == 96 and (ni.links.carrier == "BEV charger").sum() == 96
    assert (ni.links.carrier == "industry heat pump").sum() == 97   # R1: the industry heat demand itself is 0 in pypsa_eur_2050 mode (ratio heat rows pending); DAC heat (R6) uses the bus
    rail = ni.links[(ni.links.carrier == "oil final-energy accounting") & ni.links.index.str.contains(" rail ")]
    assert len(rail) > 0 and (rail.efficiency2 > 0).all()  # U2: rail oil emits


def test_s2_existing_geothermal_and_smr(nets, receipts):
    ni, _ = nets; ri, _ = receipts
    geo = ni.generators[ni.generators.carrier == "geothermal existing"]
    assert geo.p_nom.sum() == pytest.approx(186.0) and (geo.capital_cost == 0).all() and geo.p_max_pu.tolist() == pytest.approx([0.7194] * len(geo), rel=1e-3)
    assert ri["geothermal"]["in_service_mw"] == 186.0 and len(ri["geothermal"]["pending_units"]) == 9
    smr = ni.generators[ni.generators.carrier == "nuclear SMR"]
    assert (smr.capital_cost > 0).all() and (smr.p_nom_max == float("inf")).all() and "SG2 0 nuclear SMR" in smr.index
    assert ri["cost_layer"]["layer"] == "technology_data_v0_15_0_2050_eur2020"
    assert {o["technology"] for o in ri["cost_layer"]["overrides"]} == {"gas", "oil", "coal"}
