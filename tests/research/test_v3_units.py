"""V3 independent review S2-5 / S3-4 (HPC package instruction V14 section 1 items 4-5): unit tests of v3 layer functions on toy networks, no solver.
(i) apply_ev_structure, (ii) s4c_layers._apply_bunker_nodal, (iii) add_liquid_shipping, (iv) the carrier node shares of add_demand_layer, plus the single
source of the direct-cost subjects (s4d_ledger / m12_allocation)."""
import inspect
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))


def registry():
    return pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")


def rv(reg, p):
    return float(reg.loc[p, "value"])


# ---------------------------------------------------------------------------------------------------------------- (i) EV structure
EV_NODES = {"MM2 1": (6.5, "MM", 0), "TH2 1": (7.0, "TH", 0), "MY_Peninsular2 1": (8.0, "MY", 21), "TL11 0": (9.0, "TL", 21)}   # node: (UTC offset, country, UTC hour of the 3-h slot holding local 07:00)


def ev_network(p_set=1000.0):
    from s2_layers import add_bus
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=2920, freq="3h")); n.snapshot_weightings.loc[:, :] = 3.0
    for node, (_, c, _) in EV_NODES.items():
        add_bus(n, node, "AC", c, node); add_bus(n, f"{node} EV battery", "Li ion", c, node)
        n.add("Load", f"{node} land transport EV", bus=f"{node} EV battery", carrier="land transport EV", p_set=p_set)
        n.add("Link", f"{node} BEV charger", bus0=node, bus1=f"{node} EV battery", carrier="BEV charger", efficiency=0.9, p_nom_extendable=True, p_max_pu=0.8)
    return n


@pytest.mark.parametrize("scale", [1.0, 0.5])
def test_ev_structure_toy_timezones_energy_charger(scale):
    from v3_layers import apply_ev_structure
    reg = registry(); n = ev_network(); cfg = dict(research=dict(s2=dict(demand=dict(ev_structure="smart", ev_fleet_scale=scale))))
    led = apply_ev_structure(n, cfg, ROOT, reg)
    a = rv(reg, "ev_annual_km_per_vehicle") / (rv(reg, "share_transport_electric_efficiency") * 100.0)
    assert led["stores"] == 4 and led["fleet_scale"] == scale and a == pytest.approx(12000.0 / 5319.0)
    w = n.snapshot_weightings.generators
    for node, (off, _, utc_hour) in EV_NODES.items():
        st, ch, ld = f"{node} EV battery store", f"{node} BEV charger", f"{node} land transport EV"
        lo = n.stores_t.e_min_pu[st]
        hits = lo[lo > 0]
        assert len(hits) == 365 and (hits == 0.8).all() and set(hits.index.hour) == {utc_hour}   # one slot per day, the one holding local 07:00
        lh = (utc_hour + off) % 24.0
        assert lh <= 7.0 < lh + 3.0
        assert float((n.loads_t.p_set[ld] * w).sum()) == pytest.approx(1000.0 * 8760.0, rel=1e-12)   # the annual energy of the load is kept
        N = 1000.0 * 8760.0 / a * scale
        assert n.links.at[ch, "p_nom"] == pytest.approx(N * rv(reg, "share_bev_charge_rate")) and not n.links.at[ch, "p_nom_extendable"]
        assert n.stores.at[st, "e_nom"] == pytest.approx(N * rv(reg, "share_bev_energy") * rv(reg, "share_bev_dsm_availability")) and bool(n.stores.at[st, "e_cyclic"])
        assert n.links_t.p_max_pu[ch].between(0.0, 1.0).all() and n.links.at[ch, "p_max_pu"] == 1.0
    assert led["charger_mw_total"] == pytest.approx(4 * 1000.0 * 8760.0 / a * scale * rv(reg, "share_bev_charge_rate"))


# ---------------------------------------------------------------------------------------------------------------- (ii) bunker nodes
def test_bunker_nodal_toy_terminal_buses_co2_port_owner():
    from s2_layers import S2_OWNER_KIND, add_bus, add_link
    from s4c_layers import BUNKER_CO2_BUS, _apply_bunker_nodal, validate_bunker_account
    cfg = dict(research=dict(liquids=dict(structure="national_ship")))
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=2, freq="3h"))
    av, sh = "ID_Java-Bali1 0", "SG2 0"
    n.add("Bus", "_seed"); n.buses["location"] = ""; n.buses["country"] = ""; n.remove("Bus", "_seed")   # the research networks carry a location column (PyPSA 0.30 has none)
    for node, c in ((av, "ID"), (sh, "SG")):
        add_bus(n, node, "AC", c, node); add_bus(n, f"co2 atmosphere {c}", "co2", c, "")
    add_bus(n, f"{av} oil", "oil", "ID", av); add_bus(n, f"{av} aviation international oil final", "oil final energy", "ID", av)
    add_link(n, f"{av} aviation international oil meter", "ID", "aviation oil meter", [f"{av} oil", f"{av} aviation international oil final", "co2 atmosphere ID"], [1.0, 0.2571])
    n.add("Load", "L_av", bus=f"{av} aviation international oil final", carrier="kerosene for aviation", p_set=10.0)
    add_bus(n, "SG methanol", "methanol", "SG", sh); add_bus(n, f"{sh} shipping methanol final", "methanol final energy", "SG", sh)
    add_link(n, f"{sh} shipping methanol feeder", "SG", "shipping methanol", ["SG methanol", f"{sh} shipping methanol final", "co2 atmosphere SG"], [1.0, 0.2482])
    n.add("Load", "L_sh", bus=f"{sh} shipping methanol final", carrier="shipping methanol", p_set=20.0)
    n.loads["country"] = ["ID", "SG"]
    n.meta = dict(demand_owners={}, demand_identity={}, required_constraint_hooks=[])
    src = pd.DataFrame([dict(load="L_av", country="ID", carrier="oil", sector="InternationalAviationBunker", account="InternationalAviationBunker", annual_mwh=87600.0),
                        dict(load="L_sh", country="SG", carrier="shipping methanol", sector="InternationalShippingBunker", account="InternationalShippingBunker", annual_mwh=175200.0)])
    demand = dict(loads=[dict(load="L_av", bus=f"{av} aviation international oil final"), dict(load="L_sh", bus=f"{sh} shipping methanol final")])
    led = dict(asean_loads={}, loads_moved=0, links_removed=0, buses_removed=0, notes=[])
    _apply_bunker_nodal(n, cfg, demand, src, led)
    # aviation: the node final bus becomes ASEAN, the fossil meter books its CO2 into the bunker account (not the national atmosphere)
    assert n.buses.at[f"{av} aviation international oil final", "country"] == "ASEAN" and n.links.at[f"{av} aviation international oil meter", "bus2"] == BUNKER_CO2_BUS
    assert n.loads.at["L_av", "bus"] == f"{av} aviation international oil final" and n.links.at[f"{av} aviation international oil meter", "country"] == "ID"
    # shipping: own ASEAN final bus at the node, fed from the national methanol bus without a carbon port; the old bus and its feeder are gone
    nb, nl = f"{sh} bunker shipping methanol final", f"{sh} bunker shipping methanol"
    assert n.loads.at["L_sh", "bus"] == nb and n.buses.at[nb, "country"] == "ASEAN" and n.buses.at[nb, "location"] == sh
    assert n.links.at[nl, "bus0"] == "SG methanol" and n.links.at[nl, "bus1"] == nb and n.links.at[nl, "country"] == "SG"
    assert str(n.links.at[nl, "bus2"]) in ("", "nan") if "bus2" in n.links else True
    assert f"{sh} shipping methanol final" not in n.buses.index and f"{sh} shipping methanol feeder" not in n.links.index and led["buses_removed"] == 1 and led["links_removed"] == 1
    # the account has exactly the aviation meter as an emission port; loads are owned by ASEAN; the demand ledger follows the new buses
    acc = validate_bunker_account(n)
    assert acc["present"] and [p["link"] for p in acc["ports"]] == [f"{av} aviation international oil meter"]
    assert (n.loads.country == "ASEAN").all() and n.meta["demand_owners"]["L_sh"].startswith("S2:ASEAN:") and n.meta["demand_identity"]["L_av"]["owner_kind"] == S2_OWNER_KIND
    assert [r["bus"] for r in demand["loads"]] == [f"{av} aviation international oil final", nb] and led["loads_moved"] == 2


# ---------------------------------------------------------------------------------------------------------------- (iii) liquid shipping
def liquid_network():
    from carrier_architecture import COUNTRIES
    from s2_layers import add_bus
    n = pypsa.Network(); n.set_snapshots(pd.DatetimeIndex(["2013-01-01"])); n.snapshot_weightings.loc[:, :] = 8760.0
    for c in COUNTRIES:
        for k in ("oil", "oil non-fossil", "methanol", "ammonia"):
            add_bus(n, f"{c} {k}", k, c, "")
    for name, car, p in (("x_meoh", "shipping methanol", 1000.0), ("x_nh3", "industry ammonia", 200.0), ("x_oil", "oil final energy", 500.0)):
        n.add("Load", name, bus="SG methanol", carrier=car, p_set=p)
    return n


@pytest.mark.parametrize("basis", ["ieaghg", "td_tanker"])
def test_liquid_shipping_toy_links_bounds_transit(basis):
    from v3_layers import SHIP_CARRIERS, TRANSIT_CARRIER, add_liquid_shipping
    reg = registry(); n = liquid_network()
    cfg = dict(research=dict(liquids=dict(structure="national_ship", hubs_table="research_inputs/liquids_v3/LIQUID_HUB_NODES_V3.csv", routes_table="research_inputs/liquids_v3/LIQUID_SHIP_ROUTES_V3.csv",
                                          ship_capacity_factor=10.0, ship_cost_basis=basis, ship_cost_scale=1.0)))
    led = add_liquid_shipping(n, cfg, reg)
    routes = pd.read_csv(ROOT / "research_inputs/liquids_v3/LIQUID_SHIP_ROUTES_V3.csv")
    ships = n.links[n.links.carrier.isin(list(SHIP_CARRIERS.values()))]; tr = n.links[n.links.carrier == TRANSIT_CARRIER]
    assert len(routes) == 90 and len(ships) == 270 and len(tr) == 7 and led["links"] == 270 and led["transit_links"] == 7
    assert "LA" not in set(routes.origin) | set(routes.destination) and not ships.bus0.str.startswith("LA ").any() and not ships.bus1.str.startswith("LA ").any()
    assert not ships.bus0.str.match(r"^[A-Z]{2} oil$").any() and not ships.bus1.str.match(r"^[A-Z]{2} oil$").any()   # fossil oil is never shipped
    cap = {"methanol": 1000.0 * 10.0, "ammonia": 200.0 * 10.0, "oil non-fossil": 500.0 * 10.0, "oil": 500.0 * 10.0}   # annual demand / 8,760 x 10
    for k, link_car in SHIP_CARRIERS.items():
        s = ships[ships.carrier == link_car]
        assert len(s) == 90 and np.allclose(s.p_nom, cap[k]) and not s.p_nom_extendable.any()
    key = {"oil non-fossil": "oil", "methanol": "methanol", "ammonia": "ammonia"}
    for _, r in routes.iterrows():
        for k in SHIP_CARRIERS:
            name = f"{r.origin} {k} ship to {r.destination}"; km = float(r.sea_km)
            if basis == "ieaghg":   # S-A (decision 187): fixed + km term, full chain cost, eta 1
                assert n.links.at[name, "marginal_cost"] == pytest.approx(rv(reg, f"liquid_ship_fixed_ieaghg_{key[k]}") + rv(reg, f"liquid_ship_ckm_ieaghg_{key[k]}") * km, rel=1e-12)
                assert n.links.at[name, "efficiency"] == 1.0
            else:                   # S-B: km term, cargo loss
                assert n.links.at[name, "marginal_cost"] == pytest.approx(rv(reg, f"liquid_ship_ckm_td_{key[k]}") * km, rel=1e-12)
                assert n.links.at[name, "efficiency"] == pytest.approx(1.0 - rv(reg, "liquid_ship_cargo_loss_per_km") * km, rel=1e-12)
    assert "VN oil transit to LA" in tr.index and "LA oil transit to VN" not in tr.index   # fossil oil only enters LA
    for k in ("oil non-fossil", "methanol", "ammonia"):
        assert {f"VN {k} transit to LA", f"LA {k} transit to VN"} <= set(tr.index)
    assert all(n.links.at[x, "p_nom"] == pytest.approx(cap[x.split(" transit")[0][3:]]) for x in tr.index) and (tr.efficiency == 1.0).all()
    assert led["ship_cost_basis"] == basis


# ---------------------------------------------------------------------------------------------------------------- (iv) carrier node shares
def test_carrier_share_keys_missing_key_raises():
    import s2_layers
    from s2_layers import check_carrier_share_keys
    cs = {"electricity": {"a": 0.4, "b": 0.6}, "gas": {"a": 1.0}, "biomass": {"b": 1.0}}
    check_carrier_share_keys("XX", {"electricity": 5.0, "gas": 2.0, "oil": 0.0}, cs, 0.0)   # zero demand needs no key
    with pytest.raises(ValueError, match=r"\['oil'\]"):
        check_carrier_share_keys("XX", {"electricity": 5.0, "oil": 1.0}, cs, 0.0)
    with pytest.raises(ValueError, match="heat_high"):
        check_carrier_share_keys("XX", {"heat_high": 3.0}, cs, 0.0, ("medium_a", "medium_b", "high"))
    with pytest.raises(ValueError, match="biomass"):   # the industrial overflow follows the biomass shares
        check_carrier_share_keys("XX", {"electricity": 5.0}, {"electricity": {"a": 1.0}}, 7.0)
    with pytest.raises(ValueError, match="gas"):       # a key whose shares sum to zero counts as missing
        check_carrier_share_keys("XX", {"gas": 1.0}, {"gas": {"a": 0.0}}, 0.0)
    src = inspect.getsource(s2_layers.add_demand_layer)
    assert "check_carrier_share_keys(c, ind_car, cs, ov_ind, band_up)" in src and src.index("check_carrier_share_keys(") < src.index('S = (lambda k, node=node: cs.get(k, {}).get(node, 0.0))')


def test_carrier_share_table_covers_every_carrier_with_demand():
    """the shares table of the v3 build: every country x carrier key sums to 1 and passes the check (the builds of F1-F4 run the check on the real demand)"""
    from s2_layers import check_carrier_share_keys
    t = pd.read_csv(ROOT / "research_inputs/industry_v3/INDUSTRY_CARRIER_NODE_SHARES_V3.csv"); t = t[t.case == "main"]
    assert t.country.nunique() >= 1
    for c, g in t.groupby("country"):
        cs = {k: dict(zip(h.node, h.share)) for k, h in g.groupby("carrier")}
        for k, v in cs.items():
            assert sum(v.values()) == pytest.approx(1.0, abs=1e-9), (c, k)
        check_carrier_share_keys(c, {k: 1.0 for k in cs}, cs, 0.0)


# ---------------------------------------------------------------------------------------------------------------- S3-4 direct-cost subjects
def test_direct_subjects_single_source():
    import m12_allocation
    import s4d_ledger
    assert m12_allocation.DIRECT is s4d_ledger.DIRECT_SUBJECTS
    assert set(s4d_ledger.FREIGHT_SUBJECTS.values()) <= set(s4d_ledger.DIRECT_SUBJECTS) and "co2_transit_rail_freight" in s4d_ledger.DIRECT_SUBJECTS
    assert s4d_ledger.DIRECT_SUBJECTS[:3] == ("capex_new", "fom_existing", "variable_cost") and len(set(s4d_ledger.DIRECT_SUBJECTS)) == len(s4d_ledger.DIRECT_SUBJECTS)
    assert "DIRECT_SUBJECTS" in inspect.getsource(s4d_ledger.country_cost_ledger)


@pytest.mark.parametrize("sh", [1.0, 0.5])
def test_ev_smart_share_energy(sh):
    """V5 X20 (3-3): the smart share s scales fleet, charger, battery and the battery-bus load; the rest is a grid-side uncontrolled load on the
    charger's bus0 (final energy conserved: smart final + uncontrolled grid x efficiency = the original load); s = 1 is the unchanged structure."""
    from v3_layers import EV_UNCONTROLLED_CARRIER, apply_ev_structure
    reg = registry(); n = ev_network(); cfg = dict(research=dict(s2=dict(demand=dict(ev_structure="smart", ev_smart_share=sh))))
    dem = {"loads": [dict(load=f"{node} land transport EV", bus=f"{node} EV battery", carrier="land transport EV", annual_mwh=1000.0 * 8760.0) for node in EV_NODES]}
    led = apply_ev_structure(n, cfg, ROOT, reg, dem)
    a = rv(reg, "ev_annual_km_per_vehicle") / (rv(reg, "share_transport_electric_efficiency") * 100.0)
    w = n.snapshot_weightings.generators
    for node in EV_NODES:
        ld, ch, un = f"{node} land transport EV", f"{node} BEV charger", f"{node} {EV_UNCONTROLLED_CARRIER}"
        smart = float((n.loads_t.p_set[ld] * w).sum())
        assert smart == pytest.approx(sh * 1000.0 * 8760.0, rel=1e-12)
        assert n.links.at[ch, "p_nom"] == pytest.approx(1000.0 * 8760.0 / a * sh * rv(reg, "share_bev_charge_rate"))
        if sh < 1.0:
            assert n.loads.at[un, "bus"] == node and n.loads.at[un, "carrier"] == EV_UNCONTROLLED_CARRIER
            grid = float((n.loads_t.p_set[un] * w).sum())
            assert smart + grid * 0.9 == pytest.approx(1000.0 * 8760.0, rel=1e-12)                   # charger efficiency 0.9 of the toy charger? registry value below
        else:
            assert un not in n.loads.index and "ev_smart_share" not in led
    if sh < 1.0:
        assert abs(sum(r["annual_mwh"] for r in dem["loads"]) - 4 * 1000.0 * 8760.0) < 1e-6 and len(dem["loads"]) == 8
