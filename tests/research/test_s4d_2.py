"""S4D-2 (decision 92): intra-ASEAN CO2 shipping as maritime trade in both scenarios (IEAGHG 2004 chain x great-circle x route factor)."""
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
from s4d_layers import SHIP_CARRIER, shipping_mode  # noqa: E402
from scenario_network import MARITIME_TRADE_CARRIERS, tag_cross_border  # noqa: E402

CO2 = ROOT / "research_inputs/co2_v5"
REG = ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv"
BUILD = ROOT / "results_project/s4d/build_s4d2"
CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())


def reg():
    return pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id")


def test_chain_cost():
    R = reg(); f = float(R.at["conv_usd2004_to_eur2020", "value"])
    fixed, per_km = float(R.at["co2_ship_chain_fixed_cost", "value"]), float(R.at["co2_ship_chain_per_km_cost", "value"])
    # the line reproduces the printed IEAGHG 2004 Table 5-3 totals (100 bar inlet): 17.3 / 24.9 US$2004/t at 3,000 / 6,000 km
    assert (fixed + per_km * 3000) / f == pytest.approx(17.3, abs=0.06) and (fixed + per_km * 6000) / f == pytest.approx(24.9, abs=0.06)
    # and the S4C-4 extra-ASEAN shipping chain at 4,500 km (same source, same components)
    assert fixed + per_km * 4500 == pytest.approx(float(R.at["co2_extra_asean_shipping_chain_4500km", "value"]) * f, rel=1e-3)
    for k in ("co2_ship_chain_fixed_cost", "co2_ship_chain_per_km_cost", "co2_ship_route_factor"):
        assert R.at[k, "status"] == "REGISTERED" and R.at[k, "tier"] == "C" and R.at[k, "source_sha256"]
    rf = float(R.at["co2_ship_route_factor", "value"])
    assert float(R.at["co2_ship_route_factor", "sensitivity_low"]) == pytest.approx(0.75 * rf) and float(R.at["co2_ship_route_factor", "sensitivity_high"]) == pytest.approx(1.25 * rf)
    # documented cost ordering: shipping + receiver storage never undercuts the extra-ASEAN price in the main run
    assert fixed + float(CFG["research"]["s2"]["co2"]["sequestration_cost_eur_per_t"]) > float(R.at["co2_extra_asean_storage_cost", "value"])
    assert R.at["co2_intra_vs_extra_asean_cost_note", "status"] == "REFERENCE_ONLY"


def test_routes():
    r = pd.read_csv(CO2 / "CO2_SHIP_ROUTES_S4D2.csv"); js = json.loads((CO2 / "CO2_SHIP_ROUTES_S4D2.json").read_text())
    coast = pd.read_csv(CO2 / "COASTAL_NODES_S4D1_FINAL.csv").set_index("node")
    assert len(r) == 504 and r.origin.nunique() == 71 and set(r.receiver) == {"BN", "ID", "KH", "MY", "PH", "TH", "TL", "VN"}
    assert (r.origin_country != r.receiver).all() and coast.loc[r.landing, "coastal"].all() and (coast.loc[r.landing, "country"].to_numpy() == r.receiver.to_numpy()).all()
    assert coast.loc[r.origin, "coastal"].all() and coast.loc[r.origin, "co2_buffer"].all() and "LA" not in set(r.origin_country)
    assert (r.sea_km <= r.sea_km_nearest_gc + 1e-6).all()   # landing = shortest sea path
    assert js["route_factor_median"] == pytest.approx(r[r.gc_snapped_km >= 50].ratio.median(), abs=1e-4)
    assert float(reg().at["co2_ship_route_factor", "value"]) == pytest.approx(js["route_factor_median"])
    assert 1.0 <= js["grid_bias_straight_pairs"]["median_ratio"] < 1.03


def test_switch_and_tag():
    import pypsa
    assert shipping_mode(CFG) == "on" and "CO2 ship" in MARITIME_TRADE_CARRIERS
    c = copy.deepcopy(CFG); del c["research"]["co2"]["intra_asean_shipping"]; assert shipping_mode(c) == "off"
    c = copy.deepcopy(CFG); c["research"]["co2"]["extra_asean_export_nodes"] = "all"; c["research"]["co2"]["landlocked_transit"] = "off"
    with pytest.raises(ValueError):
        shipping_mode(c)
    n = pypsa.Network()
    for b, cty, car in [("a co2 stored", "SG", "co2 stored"), ("co2 sequestered MY", "MY", "co2 sequestered"), ("b co2 stored", "MY", "co2 stored")]:
        n.add("Bus", b, carrier=car); n.buses.loc[b, "country"] = cty
    n.add("Link", "ship", bus0="a co2 stored", bus1="co2 sequestered MY", carrier="CO2 ship")
    n.add("Link", "pipe", bus0="a co2 stored", bus1="b co2 stored", carrier="CO2 pipeline")
    s = tag_cross_border(n)
    assert n.links.at["ship", "border_class"] == "maritime_trade" and n.links.at["pipe", "border_class"] == "cross_border" and s["Link"]["maritime_trade"] == 1


present = all((BUILD / t / f"{s}_2920_3h_unsolved.nc").exists() for t, s in [("integrated", "integrated"), ("disconnected", "disconnected"), ("integrated_route125", "integrated")])


@pytest.mark.skipif(not present, reason="S4D-2 builds not present")
def test_builds():
    import pypsa
    R = reg(); fixed, per_km, rf = (float(R.at[k, "value"]) for k in ("co2_ship_chain_fixed_cost", "co2_ship_chain_per_km_cost", "co2_ship_route_factor"))
    routes = pd.read_csv(CO2 / "CO2_SHIP_ROUTES_S4D2.csv").set_index(["origin", "receiver"])
    for t, s, scale in [("integrated", "integrated", 1.0), ("disconnected", "disconnected", 1.0), ("integrated_route125", "integrated", 1.25)]:
        n = pypsa.Network(str(BUILD / t / f"{s}_2920_3h_unsolved.nc"))
        sl = n.links[n.links.carrier == SHIP_CARRIER]
        assert len(sl) == 504 and (sl.border_class == "maritime_trade").all() and (sl.capital_cost == 0).all()
        assert set(sl.bus1) == {f"co2 sequestered {c}" for c in n.stores.country[n.stores.carrier == "co2 sequestered"]}
        for k, z in sl.iterrows():
            o, j = k.split(" co2 ship to ")
            assert z.bus0 == f"{o} co2 stored" and n.buses.at[z.bus0, "country"] != j and z.country == n.buses.at[z.bus0, "country"]
            assert z.marginal_cost == pytest.approx(fixed + per_km * routes.at[(o, j), "gc_km"] * rf * scale, rel=1e-9)
        if s == "disconnected":   # B5 (network components only) unaffected: no cross-border line or link, shipping kept
            assert not (n.lines.border_class == "cross_border").any() and not (n.links.border_class == "cross_border").any()
        assert n.meta["research_intra_asean_shipping"]["route_factor_scale"] == scale
