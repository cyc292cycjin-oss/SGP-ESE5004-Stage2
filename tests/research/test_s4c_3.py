"""S4C-3 (decision 88, modifying decision 10): international bunkers - asean_pool (main) | bunkering_country | excluded."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4c_layers import BUNKER_CO2_BUS, BUNKER_HOOK, bunker_mode, install_bunker_net_zero, validate_bunker_account  # noqa: E402

BUILD = ROOT / "results_project/s4c/build_s4c3"
CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())


def test_config_main_and_registry_key_position():
    R = CFG["research"]
    assert R["bunkers"]["attribution"] == "asean_pool"
    assert R["cost_layer"]["registry"] == "research_inputs/registry_v5/DATA_REGISTRY.csv" and "registry" not in R["corridors"]


def test_mode_switch_rules():
    from s4c_layers import demand_cfg
    c = copy.deepcopy(CFG)
    assert bunker_mode(c) == "asean_pool" and demand_cfg(c) is c
    c["research"]["bunkers"]["attribution"] = "excluded"; bunker_mode(c)
    assert c["research"]["s2"]["demand"]["international_bunkers"] is True   # the config itself is never mutated (gate B12 hash)
    assert demand_cfg(c)["research"]["s2"]["demand"]["international_bunkers"] is False   # the demand layer sees the S2 switch off
    c = copy.deepcopy(CFG); c["research"]["s2"]["demand"]["international_bunkers"] = False
    with pytest.raises(ValueError, match="contradicts"):
        bunker_mode(c)
    c = copy.deepcopy(CFG); c["research"]["s3"]["fuel_carbon_mode"] = "producer_credit"
    with pytest.raises(ValueError, match="origin_neutral"):
        bunker_mode(c)
    c = copy.deepcopy(CFG); c["research"]["bunkers"]["attribution"] = "bunkering"
    with pytest.raises(ValueError, match="Unknown"):
        bunker_mode(c)


def _toy(with_removal=False):
    import pypsa
    n = pypsa.Network(); n.set_snapshots(range(3))
    fb = "ASEAN aviation international oil final"
    for b, car in [("ASEAN oil", "oil"), ("ASEAN oil non-fossil", "oil non-fossil"), (fb, "oil final energy"), (BUNKER_CO2_BUS, "co2 bunkers"), ("X", "co2 stored")]:
        n.add("Bus", b, carrier=car)
    n.add("Generator", "fossil", bus="ASEAN oil", p_nom=1e3, marginal_cost=10.0)
    n.add("Generator", "non-fossil", bus="ASEAN oil non-fossil", p_nom=1e3, marginal_cost=100.0)
    n.add("Link", "ASEAN aviation international oil meter", bus0="ASEAN oil", bus1=fb, bus2=BUNKER_CO2_BUS, efficiency=1.0, efficiency2=0.2571, p_nom=1e3)
    n.add("Link", "ASEAN aviation international oil meter non-fossil", bus0="ASEAN oil non-fossil", bus1=fb, efficiency=1.0, p_nom=1e3)
    n.add("Load", "bunker", bus=fb, p_set=5.0)
    n.add("Store", BUNKER_CO2_BUS, bus=BUNKER_CO2_BUS, carrier="co2 bunkers", e_nom_extendable=True, e_min_pu=-1.0, e_initial=0.0, e_cyclic=False)
    if with_removal:   # a country's removal routed into the account must be refused
        n.add("Generator", "dac power", bus="X", p_nom=1e3)
        n.add("Link", "foreign DAC", bus0="X", bus1=BUNKER_CO2_BUS, efficiency=-1.0, p_nom=1e3)
    return n


def test_account_refuses_removals():
    assert validate_bunker_account(_toy())["ports"][0]["coefficient_t_per_mwh"] == pytest.approx(0.2571)
    with pytest.raises(ValueError, match="removal port"):
        validate_bunker_account(_toy(with_removal=True))


def test_net_zero_hook_forces_non_fossil_bunkers():
    n = _toy(); n.optimize(solver_name="highs")
    assert n.generators_t.p["fossil"].sum() == pytest.approx(15.0)   # without the hook the cheap fossil kerosene is used
    n = _toy(); n.optimize(solver_name="highs", extra_functionality=lambda n, sns: install_bunker_net_zero(n))
    assert n.generators_t.p["fossil"].sum() == pytest.approx(0.0, abs=1e-6) and n.generators_t.p["non-fossil"].sum() == pytest.approx(15.0)
    assert float(n.stores_t.e[BUNKER_CO2_BUS].iloc[-1]) <= 1e-6


def _net(tag, sc="integrated"):
    import pypsa
    return pypsa.Network(str(BUILD / tag / f"{sc}_2920_3h_unsolved.nc"))


def _annual(n):
    w = n.snapshot_weightings.generators
    return n.get_switchable_as_dense("Load", "p_set").mul(w, axis=0).sum()


present = all((BUILD / t / f"{s}_2920_3h_unsolved.nc").exists() for t, s in [("integrated", "integrated"), ("disconnected", "disconnected"), ("bunkering_country", "integrated"), ("excluded", "integrated")])


@pytest.mark.skipif(not present, reason="S4C-3 builds not present")
def test_builds_three_modes():
    nb = _net("bunkering_country"); ab = _annual(nb); L = nb.loads
    av = float(ab[L.index[L.account == "InternationalAviationBunker"]].sum()); sh = float(ab[L.index[L.account == "InternationalShippingBunker"]].sum())
    assert av == pytest.approx(239.550e6, rel=1e-4) and sh == pytest.approx(485.585e6, rel=1e-4)
    assert BUNKER_CO2_BUS not in nb.stores.index and BUNKER_HOOK not in nb.meta["required_constraint_hooks"]
    for tag, sc in [("integrated", "integrated"), ("disconnected", "disconnected")]:
        n = _net(tag, sc); a = _annual(n); L = n.loads
        bl = L[L.account.isin(["InternationalAviationBunker", "InternationalShippingBunker"])]
        assert set(bl.country) == {"ASEAN"} and len(bl) == 2   # not attributed to any country, aviation and shipping separate
        assert float(a["ASEAN aviation international oil demand"]) == pytest.approx(av, rel=1e-9)
        assert float(a["ASEAN shipping international methanol"]) == pytest.approx(sh, rel=1e-9)
        assert not any(b.endswith("aviation international oil final") and not b.startswith("ASEAN") for b in n.buses.index)
        acc = validate_bunker_account(n)
        assert [p["link"] for p in acc["ports"]] == ["ASEAN aviation international oil meter"] and BUNKER_HOOK in n.meta["required_constraint_hooks"]
        assert n.links.at["ASEAN aviation international oil meter", "bus0"] == "ASEAN oil" and n.links.at["ASEAN aviation international oil meter non-fossil", "bus0"] == "ASEAN oil non-fossil"
        assert n.links.at["ASEAN shipping international methanol", "bus2"] in ("", None) or pd.isna(n.links.at["ASEAN shipping international methanol", "bus2"])
        # B8: S2 sector totals unchanged by pooling
        assert abs(float(a.sum()) - float(ab.sum())) < 1e-3 * float(ab.sum()) * 1e-6
        assert set(n.meta["demand_owners"]) == set(n.loads.index)
    ne = _net("excluded"); L = ne.loads
    assert not L.account.isin(["InternationalAviationBunker", "InternationalShippingBunker"]).any()
    d = ne.meta["research_bunkers"]["deferred"]
    assert len(d) == 22 and sum(x["annual_mwh"] for x in d) == pytest.approx(239.550e6 + 558.423e6, rel=1e-4)
