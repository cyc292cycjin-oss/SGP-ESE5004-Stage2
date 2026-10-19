"""S4L-1 (decision 113 (1)): near-zero quantity inventory and cleanup (model structure only, no solve)."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4l_layers import (DEFAULT_CAPACITY_MW, DEFAULT_ENERGY_MWH, apply_dust_cleanup, attachments, dust_inventory, dust_mode,  # noqa: E402
                        identical_link_groups, thresholds)

CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
B = ROOT / "results_project/s4l/s4l1/builds/integrated/integrated_2920_3h_unsolved.nc"
K = ROOT / "results_project/s4k/s4k3/builds/integrated/integrated_2920_3h_unsolved.nc"


def toy(biomass_demand_mw: float = 300.0):   # 300 MW x 12 h = 3,600 MWh fixed biomass demand vs pools 100 + 5,000: slack 1,500 -> the tiny pool is deletable
    import pypsa
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=4, freq="3h")); n.snapshot_weightings.loc[:, :] = 3.0
    buses = (("b0", "AC", "XX"), ("b1", "AC", "XX"), ("solid biomass XX", "solid biomass", "XX"), ("b0 coal", "coal", "XX"), ("b1 coal", "coal", "XX"),
             ("b0 oil", "oil", "XX"), ("ASEAN methanol", "methanol", "ASEAN"), ("b0 H2", "H2", "XX"), ("b0 oil non-fossil", "oil non-fossil", "XX"))
    for b, car, c in buses:
        n.add("Bus", b, carrier=car, v_nom=380.0, x=100.0, y=10.0)
    n.buses["country"] = [c for _, _, c in buses]
    n.add("Store", "XX biomass tiny", bus="solid biomass XX", carrier="solid biomass", e_nom=100.0, e_initial=100.0, marginal_cost=5.0)
    n.add("Store", "XX biomass big", bus="solid biomass XX", carrier="solid biomass", e_nom=5000.0, e_initial=5000.0, marginal_cost=5.0)
    n.stores["research_role"] = "FINITE_RESOURCE"; n.stores["country"] = "XX"; n.stores["s2_category"] = "x"
    n.add("Store", "co2 sequestered extra-ASEAN XX", bus="b0", carrier="co2 sequestered extra-ASEAN", e_nom_extendable=True, e_nom_max=np.inf, capital_cost=50.0)
    n.stores.loc["co2 sequestered extra-ASEAN XX", "research_role"] = ""
    n.add("Generator", "b0 geothermal", bus="b0", carrier="geothermal", p_nom_extendable=True, p_nom_max=0.0, capital_cost=1.0)
    n.add("Generator", "b0 solar", bus="b0", carrier="solar", p_nom_extendable=True, p_nom_max=1000.0, capital_cost=1.0, p_max_pu=pd.Series([0.0, 0.5, 0.8, 0.1], index=n.snapshots))   # 4,200 MWh over the 4 toy snapshots: above the energy threshold
    n.add("Generator", "b0 solar small", bus="b0", carrier="solar", p_nom_extendable=True, p_nom_max=100.0, capital_cost=1.0, p_max_pu=pd.Series([0.0, 0.5, 0.8, 0.1], index=n.snapshots))   # 420 MWh: below
    n.add("Generator", "b1 offwind-dc", bus="b1", carrier="offwind-dc", p_nom_extendable=True, p_nom_max=0.5, capital_cost=1.0, p_max_pu=pd.Series([0.3, 0.5, 0.8, 0.1], index=n.snapshots))
    n.add("Generator", "b1 onwind zero", bus="b1", carrier="onwind", p_nom_extendable=True, p_nom_max=10.0, capital_cost=1.0, p_max_pu=pd.Series([0.0] * 4, index=n.snapshots))
    n.add("Generator", "b0 coal supply", bus="b0 coal", carrier="coal", p_nom_extendable=True, p_nom_max=np.inf, marginal_cost=8.0)
    n.add("Generator", "b0 plastic", bus="b0", carrier="plastic waste", p_nom=0.5)
    n.add("Generator", "b0 gas", bus="b0", carrier="OCGT", p_nom_extendable=True, p_nom_max=np.inf, capital_cost=1.0, marginal_cost=30.0)
    n.generators["country"] = "XX"
    n.add("StorageUnit", "b0 hydro", bus="b0", carrier="hydro", p_nom_extendable=True, p_nom_max=0.0, efficiency_store=1.0, p_min_pu=-1.0, capital_cost=1.0)
    n.add("StorageUnit", "b1 PHS", bus="b1", carrier="PHS", p_nom_extendable=True, p_nom_max=50.0, efficiency_store=0.75, p_min_pu=-1.0, capital_cost=1.0)
    n.storage_units["country"] = "XX"
    n.add("Load", "b0 load", bus="b0", carrier="electricity", p_set=100.0)
    n.add("Load", "b1 zero load", bus="b1", carrier="shipping methanol", p_set=0.0)
    n.add("Bus", "b0 biomass final", carrier="biomass final energy"); n.buses.loc["b0 biomass final", "country"] = "XX"
    n.add("Link", "b0 biomass meter", bus0="solid biomass XX", bus1="b0 biomass final", carrier="biomass meter", p_nom_extendable=True, p_nom_max=np.inf, efficiency=1.0)
    n.add("Load", "b0 biomass load", bus="b0 biomass final", carrier="biomass final energy", p_set=biomass_demand_mw)   # x 12 h = fixed demand
    n.loads["country"] = "XX"; n.loads["sector"] = "Transport"
    for name in ("b0 b2m", "b1 b2m", "b0 b2m other cost"):
        n.add("Link", name, bus0="solid biomass XX", bus1="ASEAN methanol", carrier="biomass-to-methanol", p_nom_extendable=True, p_nom_max=np.inf, capital_cost=(10.0 if "other" not in name else 11.0), efficiency=0.65)
    n.add("Link", "b0 FT", bus0="b0 H2", bus1="b0 oil non-fossil", carrier="Fischer-Tropsch", p_nom_extendable=True, p_nom_max=np.inf, capital_cost=100.0, efficiency=0.7)
    n.add("Link", "b1 coal boiler", bus0="b1 coal", bus1="b1", carrier="coal boiler", p_nom_extendable=True, p_nom_max=np.inf, capital_cost=100.0, efficiency=0.4)
    n.add("Link", "b0 oil meter", bus0="b0", bus1="b1", bus2="b0 oil", carrier="meter", p_nom_extendable=True, p_nom_max=np.inf, efficiency=1.0, efficiency2=0.0)
    n.add("Line", "l0", bus0="b0", bus1="b1", s_nom=1000.0, x=0.1, r=0.01)
    n.links["country"] = "XX"; n.links["border_class"] = "domestic"; n.links["twin_of"] = ""
    n.meta["store_power_rules"] = {"XX biomass tiny": "discharge_only", "XX biomass big": "discharge_only"}
    n.meta["research_biomass"] = dict(stores={"XX biomass tiny": 100.0, "XX biomass big": 5000.0})
    n.meta["demand_owners"] = {"b0 load": "o1", "b1 zero load": "o2"}; n.meta["demand_identity"] = {"b0 load": {}, "b1 zero load": {}}
    n.meta["research_new_hydro_inflow_tie"] = ["b0 hydro"]
    return n


def cfg_on():
    c = copy.deepcopy(CFG); c["research"]["numerics"]["dust_cleanup"] = "on"; return c


def test_switch_and_thresholds():
    assert dust_mode(CFG) == "off" and thresholds(CFG) == dict(energy_mwh=DEFAULT_ENERGY_MWH, capacity_mw=DEFAULT_CAPACITY_MW)
    c = copy.deepcopy(CFG); del c["research"]["numerics"]
    assert dust_mode(c) == "off" and thresholds(c)["energy_mwh"] == 1000.0
    c = cfg_on(); assert dust_mode(c) == "on"
    c["research"]["numerics"]["dust_cleanup"] = "maybe"
    with pytest.raises(ValueError):
        dust_mode(c)
    c = cfg_on(); c["research"]["numerics"]["dust_energy_mwh"] = 0
    with pytest.raises(ValueError):
        thresholds(c)


def test_inventory_classes():
    n = toy(); T = dust_inventory(n, thresholds(CFG)).set_index("name")
    cls = T.dust_class.to_dict(); act = T.action.to_dict()
    assert cls["XX biomass tiny"] == "biomass_pool_below_energy" and "XX biomass big" not in cls
    assert cls["b0 geothermal"] == "zero_upper_candidate" and cls["b1 offwind-dc"] == "renewable_potential_below_capacity" and cls["b1 onwind zero"] == "all_zero_profile_generator"
    assert "b0 solar" not in cls and "b0 gas" not in cls and cls["b0 solar small"] == "renewable_potential_below_energy"
    assert cls["b0 hydro"] == "zero_upper_candidate" and "b1 PHS" not in cls
    assert cls["b1 zero load"] == "all_zero_load" and "b0 load" not in cls
    assert cls["b0 coal"] == "single_attachment_fuel_bus" and cls["b0 coal supply"] == "single_attachment_fuel_bus_component"
    assert cls["b1 coal"] == "single_attachment_fuel_bus" and cls["b1 coal boiler"] == "single_attachment_fuel_bus_component"   # input port on a dead-end bus
    assert cls["b0 oil"] == "single_attachment_fuel_bus_kept" and act["b0 oil"] == "keep" and "b0 oil meter" not in cls   # zero-efficiency port: kept
    assert cls["b0 b2m"] == "identical_parallel_link" and act["b0 b2m"] == "merge_keep" and act["b1 b2m"] == "merge" and "b0 b2m other cost" not in cls
    assert cls["b0 FT"] == "kept_zero_capacity_extendable_link" and act["b0 FT"] == "keep"
    assert cls["co2 sequestered extra-ASEAN XX"] == "kept_extra_asean_co2_store" and cls["b0 plastic"] == "kept_fixed_generator_below_capacity"
    assert identical_link_groups(n) == [("b0 b2m", ["b1 b2m"])]
    assert attachments(n)["b0 coal"] == [("Generator", "b0 coal supply", "bus")]


def test_apply_on_and_off():
    n = toy(); before = {c.name: len(c.df) for c in n.iterate_components()}
    led = apply_dust_cleanup(n, CFG)
    assert led["mode"] == "off" and {c.name: len(c.df) for c in n.iterate_components()} == before and n.meta["research_dust_cleanup"]["inventory"]["rows"] == len(led["table"])
    n = toy(); led = apply_dust_cleanup(n, cfg_on())
    assert led["mode"] == "on"
    assert "XX biomass tiny" not in n.stores.index and "XX biomass big" in n.stores.index and "co2 sequestered extra-ASEAN XX" in n.stores.index
    assert set(n.generators.index) == {"b0 solar", "b0 plastic", "b0 gas"}
    assert set(n.storage_units.index) == {"b1 PHS"} and set(n.loads.index) == {"b0 load", "b0 biomass load"}
    assert "b0 coal" not in n.buses.index and "b1 coal" not in n.buses.index and "b0 oil" in n.buses.index and "b0 oil meter" in n.links.index
    assert set(n.links.index) == {"b0 b2m", "b0 b2m other cost", "b0 FT", "b0 oil meter", "b0 biomass meter"} and np.isinf(n.links.at["b0 b2m", "p_nom_max"])
    assert n.meta["store_power_rules"] == {"XX biomass big": "discharge_only"} and n.meta["research_biomass"]["stores"] == {"XX biomass big": 5000.0}
    assert n.meta["demand_owners"] == {"b0 load": "o1"} and n.meta["research_new_hydro_inflow_tie"] == []
    assert sorted(map(tuple, led["removed_required_structure"])) == [("Generator", "geothermal", "b0"), ("Generator", "onwind", "b1"), ("Generator", "solar", "b0"), ("StorageUnit", "hydro", "b0")]
    assert led["removed"]["count"] == 11 and led["merged"] ==[dict(kept="b0 b2m", members=["b1 b2m"], p_nom_max=np.inf, carrier="biomass-to-methanol")]
    assert "b1 onwind zero" not in n.generators_t.p_max_pu.columns and "b1 zero load" not in n.loads_t.p_set.columns
    assert n.meta["research_dust_cleanup"]["components_after"]["Bus"] == 8
    assert led["pool_balance_after"] == [dict(bus="solid biomass XX", country="XX", pools=1, pool_total_mwh=5000.0, fixed_demand_mwh=3600.0, slack_mwh=1400.0, binding=False)]
    # finite p_nom_max groups: the kept link gets N x p_nom_max
    n = toy(); n.links.loc[["b0 b2m", "b1 b2m"], "p_nom_max"] = 20.0
    apply_dust_cleanup(n, cfg_on()); assert n.links.at["b0 b2m", "p_nom_max"] == 40.0


def test_pool_fixed_demand_guard():
    """S4L-2 finding (BN / SG): pools that the fixed biomass demand needs are kept even below the energy threshold."""
    from s4l_layers import pool_balance, pool_fixed_demand
    n = toy(biomass_demand_mw=425.0)   # 5,100 MWh demand = pools 100 + 5,000 exactly (binding, as BN / SG / VN in the real network)
    assert pool_fixed_demand(n, "solid biomass XX") == 5100.0 and pool_balance(n)[0]["binding"] is True
    T = dust_inventory(n, thresholds(CFG)).set_index("name")
    assert T.at["XX biomass tiny", "dust_class"] == "kept_pool_fixed_demand_binding" and T.at["XX biomass tiny", "action"] == "keep"
    led = apply_dust_cleanup(n, cfg_on())
    assert "XX biomass tiny" in n.stores.index and led["pool_balance_after"][0]["slack_mwh"] == 0.0 and led["removed"]["count"] == 10
    n = toy(biomass_demand_mw=420.0)   # 5,040 MWh: slack 60 < 100 -> still kept
    assert dust_inventory(n, thresholds(CFG)).set_index("name").at["XX biomass tiny", "action"] == "keep"
    n = toy(biomass_demand_mw=416.0)   # 4,992 MWh: slack 108 >= 100 -> deleted
    assert dust_inventory(n, thresholds(CFG)).set_index("name").at["XX biomass tiny", "action"] == "delete"


@pytest.mark.skipif(not (B.exists() and K.exists()), reason="S4L-1 / S4K-3 builds not present")
def test_build():
    import pypsa
    n = pypsa.Network(str(B)); k = pypsa.Network(str(K))
    led = n.meta["research_dust_cleanup"]
    assert led["mode"] == "on" and led["thresholds"] == dict(energy_mwh=1000.0, capacity_mw=1.0)
    assert len(n.buses) == len(k.buses) - 128 and len(n.loads) == len(k.loads) - 38 and len(n.stores) == len(k.stores) - 2
    assert int((n.links.carrier == "biomass-to-methanol").sum()) == 11
    small = n.stores[(n.stores.research_role == "FINITE_RESOURCE") & (n.stores.e_nom < 1000.0)]
    assert sorted(small.index) == ["BN biomass cassava_residues", "BN biomass maize_residues", "BN biomass sugarcane_residues", "SG biomass cassava_residues", "SG biomass coconut_residues"]   # kept: fixed demand binding
    bal = {b["country"]: b for b in led["pool_balance_after"] if b["bus"].startswith("solid biomass")}
    assert all(b["slack_mwh"] >= -1e-6 for b in bal.values()) and bal["BN"]["binding"] and bal["SG"]["binding"] and bal["VN"]["binding"] and not bal["MY"]["binding"]
    assert set(n.meta["demand_owners"]) == set(n.loads.index)
    ft = n.links[n.links.carrier == "Fischer-Tropsch"]; assert len(ft) == int((k.links.carrier == "Fischer-Tropsch").sum())
