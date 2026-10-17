"""S4E-2 (decision 95): unified CO2 storage cost basis, pair-specific sea distances, Lao transit then shipping, registered sensitivities."""
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
from s4d_layers import ship_distance_mode  # noqa: E402
from s4e_layers import extra_asean_cost_basis, extra_asean_unit_cost, lao_shipping_mode, lao_transit_legs  # noqa: E402

CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
REG = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
B = ROOT / "results_project/s4e/build_s4e2"
SHIP = float(REG.at["co2_extra_asean_shipping_chain_4500km", "value"]) * float(REG.at["conv_usd2004_to_eur2020", "value"])


def test_unified_price():
    assert SHIP == pytest.approx(24.698, abs=1e-3)
    u = REG.loc["co2_extra_asean_storage_cost_unified"]
    assert float(u.value) == pytest.approx(SHIP + 30.0) and float(u.value) == pytest.approx(54.698, abs=1e-3) and u.decision_ref == "95,89"
    assert float(u.sensitivity_low) == pytest.approx(0.5 * float(u.value)) and float(u.sensitivity_high) == pytest.approx(1.5 * float(u.value))
    assert float(REG.at["co2_storage_cost_zep_sensitivity", "value"]) == pytest.approx(16.0535, abs=1e-4)
    assert extra_asean_cost_basis(CFG) == "unified" and extra_asean_unit_cost(CFG, REG)["price"] == pytest.approx(SHIP + 30.0)
    c = copy.deepcopy(CFG); c["research"]["s2"]["co2"]["sequestration_cost_eur_per_t"] = 16.0535   # ZEP for every storage
    assert extra_asean_unit_cost(c, REG)["price"] == pytest.approx(float(REG.at["co2_extra_asean_storage_cost", "value"]), abs=1e-3)   # = the former 40.75
    c = copy.deepcopy(CFG); del c["research"]["co2"]["extra_asean_cost_basis"]
    assert extra_asean_cost_basis(c) == "s4c4" and extra_asean_unit_cost(c, REG)["price"] == pytest.approx(40.7520, abs=1e-3)


def test_switches_and_transit_legs():
    assert ship_distance_mode(CFG) == "sea_path" and lao_shipping_mode(CFG) == "on"
    c = copy.deepcopy(CFG); del c["research"]["co2"]["ship_distance"]; assert ship_distance_mode(c) == "route_factor"
    legs = lao_transit_legs(CFG, REG)
    assert len(legs) == 6
    for node, g in legs.items():   # main = the registered S4D-1 rail leg to the nearest coast
        assert g["land_cost"] == pytest.approx(float(REG.at["co2_lao_transit_land_cost_" + node.replace(" ", "_"), "value"])) and g["coastal_node"] in ("VN2 2", "VN2 3")
    c = copy.deepcopy(CFG); c["research"]["co2"]["lao_transit_destination"] = "existing_port"; c["research"]["co2"]["lao_transit_mode"] = "truck"
    t = pd.read_csv(ROOT / "research_inputs/co2_v5/LAO_TRANSIT_S4D1.csv").set_index("node"); truck = float(REG.at["co2_land_transport_truck_unit_cost", "value"])
    for node, g in lao_transit_legs(c, REG).items():
        assert g["land_cost"] == pytest.approx(truck * t.at[node, "alt_port_route_km"]) and g["coastal_node"] in ("TH2 3", "VN2 4")


present = all((B / t).exists() for t in ("integrated", "disconnected", "sens_zep", "sens_routefactor", "sens_lao_port_truck", "sens_lng_uncapped"))


def _n(tag, sc):
    import pypsa
    return pypsa.Network(str(B / tag / f"{sc}_2920_3h_unsolved.nc"))


@pytest.mark.skipif(not present, reason="S4E-2 builds not present")
def test_builds():
    routes = pd.read_csv(ROOT / "research_inputs/co2_v5/CO2_SHIP_ROUTES_S4D2.csv").set_index(["origin", "receiver"])
    fixed, per_km = float(REG.at["co2_ship_chain_fixed_cost", "value"]), float(REG.at["co2_ship_chain_per_km_cost", "value"])
    for tag, sc in (("integrated", "integrated"), ("disconnected", "disconnected")):
        n = _n(tag, sc)
        ex = n.stores[n.stores.carrier == "co2 sequestered extra-ASEAN"]; nat = n.stores[n.stores.carrier == "co2 sequestered"]
        assert np.allclose(ex.capital_cost, SHIP + 30.0) and np.allclose(nat.capital_cost, 30.0)   # one storage basis
        sl = n.links[n.links.carrier == "CO2 ship"]
        for k, z in sl.iterrows():
            o, j = k.split(" co2 ship to ")
            assert z.marginal_cost == pytest.approx(fixed + per_km * routes.at[(o, j), "sea_km"], rel=1e-9)   # pair-specific sea path
        ts = n.links[n.links.carrier == "CO2 transit ship"]
        assert len(ts) == 42 and (ts.border_class == "maritime_trade").all() and set(n.buses.country[ts.bus0]) == {"LA"}
        for k, z in ts.iterrows():
            src, j = k.split(" co2 transit ship to ")
            assert z.marginal_cost == pytest.approx(z.land_leg_eur_per_t + fixed + per_km * routes.at[(z.via_coastal_node, j), "sea_km"], rel=1e-9)
        if sc == "disconnected":
            assert not (n.lines.border_class == "cross_border").any() and not (n.links.border_class == "cross_border").any()
    z = _n("sens_zep", "integrated")
    assert np.allclose(z.stores[z.stores.carrier == "co2 sequestered"].capital_cost, 16.0535)
    assert np.allclose(z.stores[z.stores.carrier == "co2 sequestered extra-ASEAN"].capital_cost, SHIP + 16.0535)
    r = _n("sens_routefactor", "integrated"); rf = float(REG.at["co2_ship_route_factor", "value"])
    sl = r.links[r.links.carrier == "CO2 ship"]
    assert all(v.marginal_cost == pytest.approx(fixed + per_km * routes.at[tuple(k.split(" co2 ship to ")), "gc_km"] * rf, rel=1e-9) for k, v in sl.iterrows())
    lng = _n("sens_lng_uncapped", "integrated")
    g = lng.generators[lng.generators.carrier == "LNG import"]
    assert np.isinf(g.p_nom_max).all() and (g.capital_cost > 0).all()
    from v5.v5_gates import gate_b14_terminal_caps
    assert gate_b14_terminal_caps(lng)["passed"] and gate_b14_terminal_caps(_n("integrated", "integrated"))["passed"]
