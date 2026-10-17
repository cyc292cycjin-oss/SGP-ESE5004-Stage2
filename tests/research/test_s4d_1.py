"""S4D-1 (decision 93): CO2 export only from coastal nodes (physical-coast rule, user decision 2026-10-17); Lao transit pricing (Stolaroff 2021)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4d_layers import TRANSIT_LINK, coastal_table, export_nodes_mode, transit_cost_id, transit_mode  # noqa: E402

CO2 = ROOT / "research_inputs/co2_v5"
REG = ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv"
BUILD = ROOT / "results_project/s4d/build_s4d1"
CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())


def reg():
    return pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id")


def test_coastal_table():
    t = pd.read_csv(CO2 / "COASTAL_NODES_S4D1_FINAL.csv").set_index("node")
    js = json.loads((CO2 / "COASTAL_NODES_S4D1_FINAL.json").read_text())
    assert len(t) == 100 and int(t.coastal.sum()) == 73 and js["buffered"] == dict(coastal=71, inland=26, inland_nodes=js["buffered"]["inland_nodes"])
    # the two nodes re-judged under the user decision: inland, with the basis written out
    assert not t.at["TH2 2", "coastal"] and "river port only: Bangkok" in t.at["TH2 2", "basis"] and "TH2 3" in t.at["TH2 2", "basis"]
    assert not t.at["KH2 4", "coastal"] and t.at["KH2 4", "region_distance_to_sea_km"] > 40
    assert not t.loc[t.country == "LA", "coastal"].any()
    assert (t.basis.str.len() > 0).all()
    assert all(t.loc[t.coastal & (t.coast_contact_km < 1.0), "basis"].str.contains("sea port|LNG|converter"))   # coastal without contact only by port / LNG / converter
    # sea mask: the internal and archipelagic waters named in the decision are sea, Tonle Sap is not; every land km2 is in a node region
    sc = js["sea_mask"]["spot_checks"]
    assert all(v for k, v in sc.items() if "Tonle" not in k) and not sc["Tonle Sap (lake)"]
    assert max(js["sea_mask"]["land_not_in_any_onshore_region_km2"].values()) == 0.0


def test_inland_reach():
    r = pd.read_csv(CO2 / "CO2_INLAND_PIPELINE_REACH_S4D1.csv")
    assert r[r.country != "LA"].reaches_coastal_node.all() and len(r[r.country != "LA"]) == 20
    assert not r[r.country == "LA"].reaches_coastal_node.any()


def test_transit_costs():
    R = reg(); tr = pd.read_csv(CO2 / "LAO_TRANSIT_S4D1.csv").set_index("node")
    f = float(R.at["conv_usd2018_to_eur2020", "value"])
    assert f == pytest.approx(105.377 / 102.291 * float(R.at["fx_usd_to_eur_2020", "value"]), rel=1e-9)
    rail, load = float(R.at["co2_land_transport_rail_unit_cost", "value"]), float(R.at["co2_land_transport_rail_loading_cost", "value"])
    assert rail == pytest.approx(0.044 * f, rel=1e-9) and load == pytest.approx(2.0 * f, rel=1e-9)
    assert float(R.at["co2_land_transport_truck_unit_cost", "value"]) == pytest.approx(0.111 * f, rel=1e-9) and R.at["co2_land_transport_truck_unit_cost", "status"] == "REFERENCE_ONLY"
    assert R.at["co2_land_transport_rail_unit_cost", "tier"] == "C" and R.at["co2_land_transport_rail_unit_cost", "source_sha256"]
    extra = float(R.at["co2_extra_asean_storage_cost", "value"])
    assert len(tr) == 6
    for node, z in tr.iterrows():
        assert z.coast_country in ("VN", "TH", "KH", "MM")
        assert z.route_km == pytest.approx(1.25 * z.great_circle_km, abs=0.11)
        r = R.loc[transit_cost_id(node)]
        assert r.status == "REGISTERED" and r.tier == "C" and r.country == "LA" and r.node == node
        assert float(r.value) == pytest.approx(z.route_km * rail + load, abs=0.01)
        assert float(r.sensitivity_low) == pytest.approx(0.5 * float(r.value)) and float(r.sensitivity_high) == pytest.approx(1.5 * float(r.value))
        assert z.transit_unit_cost_eur2020_per_t == pytest.approx(float(r.value) + extra, abs=1e-3)


def test_switches():
    assert export_nodes_mode(CFG) == "coastal" and transit_mode(CFG) == "on"
    s, p = coastal_table(CFG); assert int(s.sum()) == 73 and p.name == "COASTAL_NODES_S4D1_FINAL.csv"
    c = copy.deepcopy(CFG); del c["research"]["co2"]["extra_asean_export_nodes"]; del c["research"]["co2"]["landlocked_transit"]
    assert export_nodes_mode(c) == "all" and transit_mode(c) == "off"   # absent keys reproduce S4C-4
    c = copy.deepcopy(CFG); c["research"]["co2"]["extra_asean_export_nodes"] = "all"
    with pytest.raises(ValueError):
        transit_mode(c)   # transit needs coastal export nodes
    c["research"]["co2"]["extra_asean_export_nodes"] = "inland"
    with pytest.raises(ValueError):
        export_nodes_mode(c)


present = all((BUILD / t / f"{s}_2920_3h_unsolved.nc").exists() for t, s in [("integrated", "integrated"), ("disconnected", "disconnected"), ("integrated_allnodes", "integrated")])


@pytest.mark.skipif(not present, reason="S4D-1 builds not present")
def test_builds():
    import pypsa
    R = reg(); coast = pd.read_csv(CO2 / "COASTAL_NODES_S4D1_FINAL.csv").set_index("node").coastal
    for t, s in [("integrated", "integrated"), ("disconnected", "disconnected")]:
        n = pypsa.Network(str(BUILD / t / f"{s}_2920_3h_unsolved.nc"))
        buffered = {b[: -len(" co2 stored")] for b in n.stores.bus[n.stores.research_role == "CO2_BUFFER"]}
        ex = n.links[n.links.carrier == "CO2 export extra-ASEAN"]; tr = n.links[n.links.carrier == TRANSIT_LINK]
        assert {b[: -len(" co2 stored")] for b in ex.bus0} == {x for x in buffered if coast[x]} and len(ex) == 71
        assert {b[: -len(" co2 stored")] for b in tr.bus0} == {x for x in buffered if x.startswith("LA2")} and len(tr) == 6
        assert (n.links.loc[list(ex.index) + list(tr.index), "border_class"] == "domestic").all()
        assert (tr.bus1 == "co2 sequestered extra-ASEAN LA").all() and (tr.capital_cost == 0).all()
        for k, z in tr.iterrows():
            assert z.marginal_cost == pytest.approx(float(R.at[transit_cost_id(k.replace(" co2 transit export extra-ASEAN", "")), "value"]))
        assert len(n.stores[n.stores.carrier == "co2 sequestered extra-ASEAN"]) == 11
        led = n.meta["research_extra_asean_storage"]
        assert led["export_nodes"] == "coastal" and led["landlocked_transit"] == "on" and led["transit_links"] == 6
    n = pypsa.Network(str(BUILD / "integrated_allnodes" / "integrated_2920_3h_unsolved.nc"))
    assert (n.links.carrier == "CO2 export extra-ASEAN").sum() == 97 and not (n.links.carrier == TRANSIT_LINK).any()
