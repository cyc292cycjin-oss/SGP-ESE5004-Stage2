"""V3 (decisions 160-165): unit tests without solver; table and network checks are in scripts_project/v3_tables.py and v3_static.py."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))


def registry():
    return pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")


def test_config_identities():
    from phase4_static import config
    a, b = config(ROOT, "integrated")["research"], config(ROOT, "no_new_xb")["research"]
    assert b["scenario"] == "no_new_xb" and b["cross_border"]["stock_mode"] == "no_new_xb" and a["cross_border"]["stock_mode"] == "remove_all"
    assert a["liquids"]["structure"] == "national_ship" and a["bunkers"]["attribution"] == "asean_account_nodal" and a["s2"]["demand"]["ev_structure"] == "smart"
    assert all(b["cross_border"][k] is True for k in ("electricity", "H2", "gas", "co2"))


def test_ev_series_mean_and_clock():
    from v3_ev import ev_series
    week = np.zeros(168); week[7] = 168.0   # Monday 07:00 local
    sn = pd.date_range("2013-01-07", periods=56, freq="3h")   # a Monday, UTC
    s = ev_series(sn, 7.0, week)   # Monday 00:00 UTC = Monday 07:00 local at UTC+7
    assert s.argmax() == 0 and s[0] == pytest.approx(168.0 / 3.0)
    s2 = ev_series(sn, 6.5, week)   # half-hour offset: linear interpolation keeps the energy
    assert s2[0] == pytest.approx(56.0) and s2.sum() == pytest.approx(s.sum())


def test_weekly_shape_table():
    t = pd.read_csv(ROOT / "research_inputs/transport_v3/EV_WEEKLY_LOCAL_SHAPE_V3.csv")
    assert len(t) == 168 and t.consumption_norm.mean() == pytest.approx(1.0) and t.plugin.between(0, 1).all()
    assert t[t.weekday == 6].consumption_norm.mean() < t[t.weekday == 2].consumption_norm.mean()


def test_nickel_final_energy_from_wei_2020():
    from v3_industry import nickel_unit_energy
    e = nickel_unit_energy()
    assert e["electricity_mwh_per_t_ni"] == pytest.approx(8.318 / 0.35)
    assert e["fuel_mwh_per_t_ni"] == pytest.approx((616 * 50 + 569 * 29) / 3600 / 0.35)
    assert e["useful_heat_mwh_per_t_ni"] == pytest.approx(0.9 * e["fuel_mwh_per_t_ni"])


def test_country_totals_conserved():
    from d1_common import DEMAND_DIR
    from v3_industry import CARRIERS, SUMMARY, V3_DIR, col
    a = pd.read_csv(DEMAND_DIR / SUMMARY).set_index("country"); cols = [col(c) for c in CARRIERS]
    for sfx in ("", "_NF2023", "_NIUPPER"):
        b = pd.read_csv(V3_DIR / f"INDUSTRY_2050_SUMMARY_V3{sfx}.csv").set_index("country")
        assert np.allclose(a[cols].sum(axis=1), b.loc[a.index, cols].sum(axis=1), rtol=1e-9, atol=1e-6)


def test_vn_matrix_two_reads():
    t = pd.read_csv(ROOT / "research_inputs/industry_v3/APEC2022_VN_INDUSTRY_PJ.csv")
    assert (t.read1_total_pj == t.read2_total_pj).all() and abs(t.printed_total_pj.sum() - 1542) <= 1
    row = t[["coal_pj", "oil_pj", "gas_pj", "biomass_pj", "electricity_pj"]].sum(axis=1)
    assert (row - t.printed_total_pj).abs().max() <= 1.0


def test_node_shares_sum_to_one():
    d = ROOT / "research_inputs/industry_v3"
    assert np.allclose(pd.read_csv(d / "INDUSTRY_NODE_SHARES_V3.csv").groupby(["country", "subsector"]).share.sum(), 1.0)
    assert np.allclose(pd.read_csv(d / "INDUSTRY_CARRIER_NODE_SHARES_V3.csv").groupby(["case", "country", "carrier"]).share.sum(), 1.0)
    assert np.allclose(pd.read_csv(d / "PROCESS_NEU_NODE_SHARES_V3.csv").groupby(["country", "key"]).share.sum(), 1.0)


def test_ship_unit_cost():
    from v3_layers import ship_unit
    reg = registry(); cfg = dict(research=dict(liquids=dict(ship_cost_basis="td_tanker", ship_cost_scale=1.0)))
    c, eta = ship_unit(cfg, reg, "methanol", 1000.0)
    assert c == pytest.approx(0.1213, abs=2e-3) and eta == pytest.approx(0.996)
    cfg["research"]["liquids"]["ship_cost_scale"] = 1.5
    assert ship_unit(cfg, reg, "methanol", 1000.0)[0] == pytest.approx(1.5 * c)
    cfg["research"]["liquids"].update(ship_cost_basis="ieaghg", ship_cost_scale=1.0)
    c2, eta2 = ship_unit(cfg, reg, "methanol", 1000.0)
    assert c2 == pytest.approx(0.93 + 0.534, abs=5e-3) and eta2 == 1.0


def test_hubs_and_routes():
    h = pd.read_csv(ROOT / "research_inputs/liquids_v3/LIQUID_HUB_NODES_V3.csv").set_index("country")
    r = pd.read_csv(ROOT / "research_inputs/liquids_v3/LIQUID_SHIP_ROUTES_V3.csv")
    assert h.at["MM", "hub_node"] == "MM2 1" and h.at["ID", "hub_node"] == "ID_Java-Bali1 0" and len(h) == 11 and len(r) == 90
    assert (r.sea_km > 0).all() and "LA" not in set(r.origin) | set(r.destination)


def test_smoke_eval_toy():
    import pypsa
    from v3_smoke_eval import liquid_balance, sg_marine, ship_duals, slack_use
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=2, freq="3h")); n.snapshot_weightings.loc[:, :] = 4380.0
    for b, c in (("ID methanol", "ID"), ("SG methanol", "SG"), ("SG2 0 shipping methanol", "ASEAN")):
        n.add("Bus", b, carrier="methanol"); n.buses.loc[b, "country"] = c
    n.add("Link", "ID ship", bus0="ID methanol", bus1="SG methanol", carrier="methanol ship", p_nom=100.0, efficiency=0.99)
    n.add("Link", "SG feed", bus0="SG methanol", bus1="SG2 0 shipping methanol", carrier="shipping methanol link", p_nom=100.0)
    n.add("Load", "SG marine", bus="SG2 0 shipping methanol", carrier="shipping methanol", p_set=10.0); n.loads["country"] = "ASEAN"
    n.add("Generator", "SG methanol import", bus="SG methanol", carrier="methanol import", p_nom=1.0)
    n.generators_t.p = pd.DataFrame({"SG methanol import": [1.0, 1.0]}, index=n.snapshots)
    n.links_t.p0 = pd.DataFrame({"ID ship": [10.0, 10.0], "SG feed": [10.9, 10.9]}, index=n.snapshots)
    n.links_t.p1 = pd.DataFrame({"ID ship": [-9.9, -9.9], "SG feed": [-10.9, -10.9]}, index=n.snapshots)
    n.links_t["mu_upper"] = pd.DataFrame({"ID ship": [0.0, 2190.0]}, index=n.snapshots)   # the stored dual carries the snapshot weight 4380
    d = ship_duals(n, "x").set_index("link"); b = liquid_balance(n, "x")
    assert d.at["ID ship", "mu_upper_max_abs"] == 0.5 and d.at["ID ship", "max_utilisation"] == pytest.approx(0.1) and d.at["ID ship", "flow_twh"] == pytest.approx(0.0876)
    assert b[(b.country == "ID") & (b.term == "ship out")].twh.sum() == pytest.approx(-0.0876)
    s = sg_marine(n, b)
    assert s["marine_load_twh"] == pytest.approx(0.0876) and s["ship_in_twh_by_origin"]["ID"] == pytest.approx(0.086724) and s["import_outside_asean_twh"] == pytest.approx(0.00876) and s["has_source"]
    assert slack_use(n)["Generator"]["components"] == 0


def test_x1_apg_existing_is_the_stock_source():
    a = pd.read_csv(ROOT / "research_inputs/corridors/CORRIDOR_APG_CROSSCHECK_2024.csv")
    s = a[a.apg_existing_mw.notna()].groupby("country_pair").apg_existing_mw.sum()
    assert s.sum() == 2870.0 and s["LA-TH"] == 955.0 and s["MY-TH"] == 380.0 and "MM-TH" not in s and len(s) == 8


def test_x1_stock_check_toy():
    import pypsa
    from v3_static import stock_check
    def net(extendable, nom_min):
        n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=2, freq="3h"))
        for b, c in (("a", "LA"), ("b", "TH")):
            n.add("Bus", b); n.buses.loc[b, "country"] = c
        n.add("Line", "l", bus0="a", bus1="b", x=0.1, s_nom=955.0, s_nom_min=nom_min, s_nom_extendable=extendable); n.lines["border_class"] = "cross_border"
        n.add("Link", "gas", bus0="a", bus1="b", p_nom=0.0); n.add("Link", "dc", bus0="a", bus1="b", p_nom=45.0, p_nom_min=45.0); n.add("Link", "dc-reversed", bus0="b", bus1="a", p_nom=45.0, p_nom_min=45.0)
        n.links["border_class"] = "cross_border"; n.links["transport_carrier"] = ["gas", "electricity", "electricity"]; n.links["p_nom_extendable"] = False
        return n
    apg = pd.DataFrame(dict(country_pair=["LA-TH"], apg_existing_mw=[1000.0]))
    t, ok = stock_check(net(True, 955.0), net(False, 0.0), apg)
    assert ok and t.no_new_xb_fixed_mw.iloc[0] == 1000.0   # the -reversed twin of the DC link counts once
    assert t.no_new_xb_usable_mw.iloc[0] == pytest.approx(955.0 + 45.0)   # s_max_pu of the toy line is 1
    assert not stock_check(net(True, 900.0), net(False, 0.0), apg)[1]   # the integrated lower bound differs from the source
    assert not stock_check(net(True, 955.0), net(True, 0.0), apg)[1]   # a cross-border component of no_new_xb is extendable


def test_x1b_table_and_the_apg_lines():
    t = pd.read_csv(ROOT / "research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv")
    assert len(t) == 11 and t.counted.all() and (t.gem_status == "operating").all()
    assert t[t.other_country == "TH"].contract_mw.sum() == 5427.0 and t[t.other_country == "VN"].contract_mw.sum() == 572.0
    assert t[t.eppo_section.fillna("").str.startswith("1")].contract_mw.sum() == 2111.0 and t[t.eppo_section.fillna("").str.startswith("2")].contract_mw.sum() == 3047.0
    assert t.plant_node.str.startswith("LA").all() and (t.contract_mw <= t.gem_capacity_mw).all() and t[t.other_country == "VN"].landing_node.str.startswith("VN").all()
    a = pd.read_csv(ROOT / "research_inputs/corridors/APG_LA_TH_LINES_ACE2024.csv")
    assert a.line_capacity_mw.sum() == 955.0 and (a.agreement == "Energy Exchange").all() and (a.voltage_kv == 115).all()   # the APG stock holds no plant line: nothing to deduct


def dedicated_toy(electricity=True, extras=False, mixed=False):
    """every plant unit of the table is a fixed Generator of 100 MW with its identity; extras: the other stock kinds of the real nodes (reservoir StorageUnit, fuel Link in fuel terms) and what has to stay on the node;
    mixed: a construction unit, and a component of LA2 3 and one of LA2 5 with units of both kinds (decision 180)"""
    import pypsa
    from v3_layers import add_dedicated_plant_lines
    t = pd.read_csv(ROOT / "research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv")
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=2, freq="3h"))
    for i, b in enumerate(sorted(set(t.plant_node) | set(t.landing_node))):
        n.add("Bus", b, carrier="AC", x=100.0 + i, y=15.0 + 0.5 * i, v_nom=380.0); n.buses.loc[b, "country"] = b[:2]
    n.buses["location"] = n.buses.index; n.links["border_class"] = ""; n.links["transport_carrier"] = ""
    ident = n.meta["existing_unit_components"] = {}
    for _, r in t.iterrows():
        for i in r.gem_unit_ids.split(";"):
            name = f"existing_survivor::GEM:{i}"
            if name not in n.generators.index:   # one GEM unit for Theun-Hinboun and its expansion
                n.add("Generator", name, bus=r.plant_node, p_nom=100.0, carrier="ror existing")
            ident[f"GEM:{i}"] = dict(component_type="Generator", component=name, capacity_mw=100.0, node=r.plant_node)
    if extras:
        n.add("StorageUnit", "existing_survivor::LA2 3::Hydro::x", bus="LA2 3", p_nom=300.0, carrier="hydro existing", max_hours=7.0, efficiency_store=0.0)
        ident["GEM:su"] = dict(component_type="StorageUnit", component="existing_survivor::LA2 3::Hydro::x", capacity_mw=300.0, node="LA2 3")
        n.add("Bus", "LA2 5 lignite", carrier="lignite"); n.buses.loc["LA2 5 lignite", "country"] = "LA"
        n.add("Link", "existing_survivor::LA2 5::Lignite::x", bus0="LA2 5 lignite", bus1="LA2 5", p_nom=6000.0, efficiency=0.33, carrier="lignite existing")
        n.links.loc["existing_survivor::LA2 5::Lignite::x", ["border_class", "transport_carrier"]] = ["domestic", "local"]
        ident["GEM:lig"] = dict(component_type="Link", component="existing_survivor::LA2 5::Lignite::x", capacity_mw=1980.0, node="LA2 5")
        n.add("Generator", "LA2 3 onwind-2025", bus="LA2 3", p_nom_extendable=True, carrier="onwind")
        n.add("StorageUnit", "LA2 3 hydro_new", bus="LA2 3", p_nom_extendable=True, carrier="hydro")
        n.add("Load", "LA2 3 demand", bus="LA2 3", p_set=50.0)
        n.add("Line", "domestic 1", bus0="LA2 2", bus1="LA2 3", x=0.1, s_nom=500.0)
    status = {k: "operating" for k in ident}
    if mixed:
        n.add("Generator", "existing_survivor::LA2 1::onwind existing::S4B1", bus="LA2 1", p_nom=350.0, carrier="onwind existing")
        ident["GEM:wind"] = dict(component_type="Generator", component="existing_survivor::LA2 1::onwind existing::S4B1", capacity_mw=350.0, node="LA2 1", gem_status="construction"); status["GEM:wind"] = "construction"
        n.add("StorageUnit", "existing_survivor::LA2 3::hydro existing::S4A", bus="LA2 3", p_nom=400.0, carrier="hydro existing", max_hours=7.0, efficiency_store=0.0)
        n.storage_units["existing_annual_fixed_om_eur"] = 0.0; n.storage_units.loc["existing_survivor::LA2 3::hydro existing::S4A", "existing_annual_fixed_om_eur"] = 80.0
        n.storage_units_t.inflow = pd.DataFrame({"existing_survivor::LA2 3::hydro existing::S4A": [40.0, 80.0]}, index=n.snapshots)
        for k, mw, st in (("GEM:h1", 100.0, "operating"), ("GEM:h2", 300.0, "construction")):
            ident[k] = dict(component_type="StorageUnit", component="existing_survivor::LA2 3::hydro existing::S4A", capacity_mw=mw, node="LA2 3"); status[k] = st
        n.add("Generator", "existing_survivor::LA2 5::ror existing::S4A", bus="LA2 5", p_nom=948.0, carrier="ror existing")
        n.generators_t.p_max_pu = pd.DataFrame({"existing_survivor::LA2 5::ror existing::S4A": [0.5, 0.25]}, index=n.snapshots)
        for k, mw, st in (("GEM:r1", 912.0, "construction"), ("GEM:r2", 36.0, "operating")):
            ident[k] = dict(component_type="Generator", component="existing_survivor::LA2 5::ror existing::S4A", capacity_mw=mw, node="LA2 5"); status[k] = st
    n.meta["existing_cross_border_fom_eur"] = 5.0; n.meta["existing_cross_border_fom_ledger"] = [dict(component_type="Line", component="x", capacity_2025_mw=1.0, length_km=1.0, annual_fom_eur=5.0, cost_rows=[])]
    cfg = dict(research=dict(network=dict(dedicated_plant_lines_table="research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv", ac_losses="linear_proxy", ac_loss_reference_loading=0.5, transmission_losses="pypsa_eur"), cross_border=dict(electricity=electricity, H2=electricity, gas=electricity, co2=electricity)))
    costs = pd.DataFrame(dict(FOM=[2.0], investment=[500.0]), index=["HVAC overhead"])
    return n, add_dedicated_plant_lines(n, cfg, ROOT, costs, dict(fom_on_existing=True), status=status)


def test_x1b_layer_toy(tmp_path):
    from v3_static import stock_by_pair
    n, led = dedicated_toy(); n.lines["border_class"] = pd.Series(dtype=str)
    n.links["country"] = n.links["country"].astype(str); n.export_to_netcdf(tmp_path / "toy.nc")   # the build exports the network: no mixed column
    K = n.links[n.links.carrier == "dedicated plant line"]
    assert led["links"] == 6 and led["total_mw"] == 5999.0 and len(K) == 6 and not n.links.p_nom_extendable.any() and (K.border_class == "cross_border").all()
    f = n.links.loc["dedicated plant line LA2 3 - TH2 1"]
    assert f.p_nom == 1388.0 and f.p_nom_min == f.p_nom and f.bus0 == "LA2 3 dedicated src" and f.bus1 == "TH2 1" and f.stock == "dedicated_plant_line" and not f.reversed and f.p_min_pu == 0.0   # one way, supplement 03; source bus, decision 179
    assert n.links.bus0.str.startswith("LA").all() and n.links.p_min_pu.eq(0.0).all()
    assert 0.0 < f.efficiency < 1.0 and 1.0 - f.efficiency == pytest.approx(led["loss_per_km"] * f.length) and led["loss_per_km"] * 100.0 == pytest.approx(0.012, rel=0.2)
    p = stock_by_pair(n, "min"); assert p["LA-TH"] == 5427.0 and p["LA-VN"] == 572.0
    assert n.meta["existing_cross_border_fom_eur"] == pytest.approx(5.0 + led["annual_fom_eur"]) and len(n.meta["existing_cross_border_fom_ledger"]) == 7


def test_x1b_not_in_the_disconnected_network():
    from v3_layers import dedicated_source_buses
    n, led = dedicated_toy(electricity=False)
    assert led["links"] == 0 and not len(n.links) and "role" not in n.buses and not len(dedicated_source_buses(n)) and not n.buses.index.str.endswith("dedicated src").any()


def test_x1b_stock_mode_keeps_the_lines_fixed():
    from m08a_layers import apply_stock_mode
    from v3_static import dedicated_check
    n, _ = dedicated_toy(); n.lines["border_class"] = pd.Series(dtype=str); base = n.copy(); base.links["stock"] = n.links["stock"]; base.meta = dict(n.meta)
    led = apply_stock_mode(n, "no_new_xb")
    assert led["kept_links_forward"] == 6 and led["kept_reversed_twins"] == 0 and led["removed_links"] == 0
    t, ok = dedicated_check(base, n)
    assert ok and len(t) == 6 and t.p_nom.sum() == 5999.0


def test_x1b_check_refuses_a_reverse_link():
    from v3_static import dedicated_check
    n, _ = dedicated_toy(); r = n.copy(); r.links.loc[r.links.index[0], "p_min_pu"] = -1.0; r.links["stock"] = n.links["stock"]
    assert dedicated_check(n, n)[1] and not dedicated_check(r, r)[1]


def test_x1b_stock_check_counts_the_lines():
    from v3_static import stock_check
    n, _ = dedicated_toy(); n.lines["border_class"] = pd.Series(dtype=str)
    d = pd.DataFrame(dict(counted=[True, True], other_country=["TH", "VN"], contract_mw=[5427.0, 572.0]))
    apg = pd.DataFrame(dict(country_pair=["LA-TH"], apg_existing_mw=[0.0]))
    t, ok = stock_check(n, n, apg, d)
    assert ok and t.set_index("pair").dedicated_mw.to_dict() == {"LA-TH": 5427.0, "LA-VN": 572.0}
    assert not stock_check(n, n, apg, d.assign(contract_mw=[5000.0, 572.0]))[1]


def test_179_source_buses_hold_the_stock(tmp_path):
    from v3_layers import dedicated_source_buses, source_bus_problems
    n, led = dedicated_toy(extras=True); n.lines["border_class"] = "domestic"
    src = "LA2 3 dedicated src"; z = n.buses.loc[src]
    assert sorted(dedicated_source_buses(n)) == [f"LA2 {i} dedicated src" for i in range(1, 6)]
    assert z.role == "dedicated_plant_source" and z.country == "LA" and z.carrier == "AC" and z.location == "LA2 3" and (z.x, z.y, z.v_nom) == tuple(n.buses.loc["LA2 3", ["x", "y", "v_nom"]])
    g = n.generators; u = n.storage_units
    assert g.bus[~g.p_nom_extendable].str.endswith("dedicated src").all() and u.at["existing_survivor::LA2 3::Hydro::x", "bus"] == src   # the fixed units moved, parameters unchanged
    assert g.at["LA2 3 onwind-2025", "bus"] == "LA2 3" and u.at["LA2 3 hydro_new", "bus"] == "LA2 3" and n.loads.at["LA2 3 demand", "bus"] == "LA2 3" and n.lines.at["domestic 1", "bus1"] == "LA2 3"   # extendable units, loads and other lines stay
    t = n.links.loc["existing_survivor::LA2 5::Lignite::x"]; assert t.bus0 == "LA2 5 lignite" and t.bus1 == "LA2 5 dedicated src" and t.p_nom == 6000.0 and t.efficiency == 0.33   # the fuel port stays, the output moves
    k = n.links.loc[src + " to grid"]
    assert k.bus0 == src and k.bus1 == "LA2 3" and k.efficiency == 1.0 and k.p_min_pu == 0.0 and k.marginal_cost == 0.0 and k.capital_cost == 0.0 and not k.p_nom_extendable and k.border_class == "domestic" and k.research_role == "dedicated_src_to_grid"
    assert k.p_nom == g[g.bus == src].p_nom.sum() + 300.0
    assert n.links.at["LA2 5 dedicated src to grid", "p_nom"] == pytest.approx(g[g.bus == "LA2 5 dedicated src"].p_nom.sum() + 6000.0 * 0.33)   # output side of the fuel Link: p_nom x efficiency
    assert not source_bus_problems(n)
    s = {r["node"]: r for r in led["sources"]}
    assert set(s) == {f"LA2 {i}" for i in range(1, 6)} and s["LA2 3"]["moved_mw_by_carrier"]["hydro existing"] == 300.0 and s["LA2 5"]["moved_mw_by_carrier"]["lignite existing"] == pytest.approx(1980.0) and s["LA2 3"]["contract_mw"] == 1388.0
    n.links["country"] = n.links["country"].astype(str); n.export_to_netcdf(tmp_path / "toy.nc")
    import pypsa
    back = pypsa.Network(str(tmp_path / "toy.nc")); assert list(dedicated_source_buses(back)) == list(dedicated_source_buses(n)) and not source_bus_problems(back)


def test_179_two_lines_share_one_source():
    n, led = dedicated_toy()
    both = n.links.loc[["dedicated plant line LA2 4 - TH2 1", "dedicated plant line LA2 4 - VN2 2"]]
    assert (both.bus0 == "LA2 4 dedicated src").all() and {r["node"]: r["contract_mw"] for r in led["sources"]}["LA2 4"] == 1052.0
    assert int((n.links.carrier == "dedicated plant source").sum()) == 5 and sorted(next(r for r in led["sources"] if r["node"] == "LA2 4")["plant_lines"]) == sorted(both.index)


def test_179_stops_without_stock_or_with_a_unit_without_identity():
    import pypsa
    from v3_layers import bind_dedicated_sources
    n = pypsa.Network(); n.add("Bus", "LA2 1", carrier="AC"); n.buses.loc["LA2 1", "country"] = "LA"; n.meta["existing_unit_components"] = {}
    line = [dict(plant_node="LA2 1", link="x", contract_mw=1.0)]
    with pytest.raises(ValueError, match="no operating non-thermal stock"):
        bind_dedicated_sources(n, line, {})
    n = pypsa.Network(); n.add("Bus", "LA2 1", carrier="AC"); n.buses.loc["LA2 1", "country"] = "LA"; n.meta["existing_unit_components"] = {}
    n.add("Generator", "fixed without identity", bus="LA2 1", p_nom=5.0)
    with pytest.raises(ValueError, match="existing_unit_components"):
        bind_dedicated_sources(n, line, {})


def stock_net(*units):
    """one plant node; units: (identity, type, status, gem_status); the fixed components carry 10 MW each"""
    import pypsa
    n = pypsa.Network(); n.buses["location"] = ""; n.add("Bus", "LA2 1", carrier="AC"); n.buses.loc["LA2 1", ["country", "location"]] = ["LA", "LA2 1"]; n.add("Bus", "LA2 1 lignite", carrier="lignite"); n.buses.loc["LA2 1 lignite", "country"] = "LA"
    n.links["border_class"] = ""; n.links["transport_carrier"] = ""; n.links["stock"] = ""; n.links["reversed"] = False; ident = n.meta["existing_unit_components"] = {}; st = {}
    for k, t, s, g in units:
        c = "c " + k
        if t == "Link":
            n.add("Link", c, bus0="LA2 1 lignite", bus1="LA2 1", p_nom=10.0, efficiency=0.5, carrier="lignite existing")
        else:
            n.add(t, c, bus="LA2 1", p_nom=10.0, carrier="ror existing")
        ident[k] = dict(component_type=t, component=c, capacity_mw=10.0, node="LA2 1", **({"gem_status": g} if g else {}))
        if s:
            st[k] = s
    return n, st


LINE = [dict(plant_node="LA2 1", link="x", contract_mw=1.0)]


def test_180_status_table_and_the_receipt_agree():
    t = pd.read_csv(ROOT / "research_inputs/corridors/DEDICATED_STOCK_STATUS_V3.csv", keep_default_na=False)
    assert len(t) == 65 and t.identity.is_unique and t.gipt_status.isin(["operating", "construction"]).all() and (t.capacity_mw == t.gipt_capacity_mw).all()
    assert t[t.gipt_status == "construction"].capacity_mw.sum() == 5202.0 and t[t.gipt_status == "operating"].capacity_mw.sum() == 11673.0
    f = t[t.gem_status_in_receipt != ""]; assert len(f) == 22 and (f.gem_status_in_receipt == f.gipt_status).all()
    assert set(pd.read_csv(ROOT / "research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv").gem_unit_ids.str.split(";").explode()) <= set(t[t.gipt_status == "operating"].gem_unit_id)   # every contract plant is operating


def test_180_only_operating_units_on_the_source_bus():
    from v3_layers import source_bus_problems
    n, led = dedicated_toy(extras=True, mixed=True); n.lines["border_class"] = "domestic"
    w = "existing_survivor::LA2 1::onwind existing::S4B1"
    assert n.generators.at[w, "bus"] == "LA2 1" and n.generators.at[w, "p_nom"] == 350.0   # construction: back on the node, parameters unchanged
    s = {r["node"]: r for r in led["sources"]}
    assert s["LA2 1"]["stayed_units"] == ["GEM:wind"] and "onwind existing" not in s["LA2 1"]["moved_mw_by_carrier"]
    assert n.links.at["LA2 1 dedicated src to grid", "p_nom"] == n.generators[n.generators.bus == "LA2 1 dedicated src"].p_nom.sum()
    assert not source_bus_problems(n)


def test_180_mixed_component_is_split_and_adds_up():
    from v3_layers import source_bus_problems
    from v3_static import merged, merged_series
    n, led = dedicated_toy(extras=True, mixed=True); n.lines["border_class"] = "domestic"
    u = n.storage_units; a = "existing_survivor::LA2 3::hydro existing::S4A"; b = a + " operating"
    assert u.at[a, "bus"] == "LA2 3" and u.at[b, "bus"] == "LA2 3 dedicated src" and (u.at[a, "p_nom"], u.at[b, "p_nom"]) == (300.0, 100.0) and u.at[b, "max_hours"] == u.at[a, "max_hours"]
    assert u.at[a, "existing_annual_fixed_om_eur"] + u.at[b, "existing_annual_fixed_om_eur"] == 80.0 and u.at[b, "existing_annual_fixed_om_eur"] == 20.0
    i = n.storage_units_t.inflow; assert i[b].tolist() == [10.0, 20.0] and i[a].tolist() == [30.0, 60.0]
    g = n.generators; c = "existing_survivor::LA2 5::ror existing::S4A"; d = c + " operating"
    assert g.at[c, "bus"] == "LA2 5" and g.at[d, "bus"] == "LA2 5 dedicated src" and (g.at[c, "p_nom"], g.at[d, "p_nom"]) == (912.0, 36.0)
    assert n.generators_t.p_max_pu[d].tolist() == n.generators_t.p_max_pu[c].tolist() == [0.5, 0.25]   # per unit: copied, not shared out
    ident = n.meta["existing_unit_components"]; assert ident["GEM:h1"]["component"] == b and ident["GEM:h2"]["component"] == a and ident["GEM:h1"]["node"] == "LA2 3"
    assert merged(n, "StorageUnit").at[a, "p_nom"] == 400.0 and merged_series(i, "inflow")[a].tolist() == [40.0, 80.0] and b not in merged(n, "StorageUnit").index
    assert not source_bus_problems(n)
    x = {r["node"]: r for r in led["sources"]}; assert x["LA2 3"]["split"][0]["moved_mw"] == 100.0 and x["LA2 5"]["split"][0]["rest"] == c


def test_180_missing_or_conflicting_status_stops_the_build():
    from v3_layers import bind_dedicated_sources
    n, st = stock_net(("GEM:a", "Generator", None, None))
    with pytest.raises(ValueError, match="no status"):
        bind_dedicated_sources(n, LINE, st)
    n, st = stock_net(("GEM:a", "Generator", "operating", "construction"))
    with pytest.raises(ValueError, match="gem_status"):
        bind_dedicated_sources(n, LINE, st)


def test_180_a_node_with_operating_thermal_only_stops_the_build():
    from v3_layers import bind_dedicated_sources
    n, st = stock_net(("GEM:a", "Generator", "construction", "construction"), ("GEM:b", "Link", "operating", None))
    with pytest.raises(ValueError, match="no operating non-thermal stock"):
        bind_dedicated_sources(n, LINE, st)


def test_180_check_refuses_a_construction_unit_on_the_source():
    from v3_layers import source_bus_problems
    n, _ = dedicated_toy(extras=True, mixed=True); n.lines["border_class"] = "domestic"; assert not source_bus_problems(n)
    n.meta["existing_unit_components"]["GEM:h1"]["gipt_status_2026"] = "construction"
    assert any("not operating" in x for x in source_bus_problems(n))
    n, _ = dedicated_toy(extras=True, mixed=True); n.lines["border_class"] = "domestic"
    n.meta["existing_unit_components"]["GEM:wind"]["gipt_status_2026"] = "operating"
    assert any("outside the source bus" in x for x in source_bus_problems(n))


def test_180_struct_diff_folds_the_split_back():
    import pypsa
    from v3_static import struct_diff

    def net(split):
        n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=2, freq="3h"))
        for b in ("LA2 3", "LA2 3 dedicated src"):
            n.add("Bus", b, carrier="AC", country="LA")
        k = "existing_survivor::x"; n.add("StorageUnit", k, bus="LA2 3", p_nom=300.0 if split else 400.0, carrier="hydro existing"); n.storage_units_t.inflow = pd.DataFrame({k: [30.0, 60.0] if split else [40.0, 80.0]}, index=n.snapshots)
        if split:
            n.add("StorageUnit", k + " operating", bus="LA2 3 dedicated src", p_nom=100.0, carrier="hydro existing"); n.storage_units_t.inflow[k + " operating"] = [10.0, 20.0]
        return n

    t, bad = struct_diff(net(False), net(True))
    assert not bad and "split_for_source_bus" in set(t.change)
    assert not struct_diff(net(True), net(True))[1]
    m = net(True); m.storage_units.loc["existing_survivor::x", "p_nom"] = 290.0
    assert struct_diff(net(False), m)[1]   # a part that does not add up still fails


def test_179_ledger_books_the_source_link_to_laos():
    """hand-made solved network: stock 10 MW at 1 EUR/MWh on the source bus, 4 MW to the node, 6 MW over the plant line (5.7 arrive); duals 10 in LA, 20 in TH; two 3-hour snapshots. No settlement on the source link."""
    import pypsa
    from s4d_ledger import bus_entities, country_cost_ledger, ledger_gate, ledger_table, owners
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=2, freq="3h")); n.snapshot_weightings.loc[:, :] = 3.0
    for b, c in (("LA2 1 dedicated src", "LA"), ("LA2 1", "LA"), ("TH2 4", "TH")):
        n.add("Bus", b, carrier="AC"); n.buses.loc[b, "country"] = c
    n.add("Generator", "stock", bus="LA2 1 dedicated src", p_nom=10.0, marginal_cost=1.0, carrier="ror existing")
    n.add("Load", "la", bus="LA2 1", carrier="AC"); n.add("Load", "th", bus="TH2 4", carrier="AC")
    n.add("Link", "LA2 1 dedicated src to grid", bus0="LA2 1 dedicated src", bus1="LA2 1", p_nom=10.0, carrier="dedicated plant source")
    n.add("Link", "dedicated plant line LA2 1 - TH2 4", bus0="LA2 1 dedicated src", bus1="TH2 4", p_nom=6.0, efficiency=0.95, carrier="dedicated plant line")
    n.links["border_class"] = ["domestic", "cross_border"]; n.links["p_nom_opt"] = n.links.p_nom; n.generators["p_nom_opt"] = n.generators.p_nom
    i = n.snapshots
    n.generators_t.p = pd.DataFrame({"stock": [10.0, 10.0]}, index=i); n.loads_t.p = pd.DataFrame({"la": [4.0, 4.0], "th": [5.7, 5.7]}, index=i)
    n.links_t.p0 = pd.DataFrame({"LA2 1 dedicated src to grid": [4.0, 4.0], "dedicated plant line LA2 1 - TH2 4": [6.0, 6.0]}, index=i)
    n.links_t.p1 = pd.DataFrame({"LA2 1 dedicated src to grid": [-4.0, -4.0], "dedicated plant line LA2 1 - TH2 4": [-5.7, -5.7]}, index=i)
    n.buses_t.marginal_price = pd.DataFrame({"LA2 1 dedicated src": [10.0, 10.0], "LA2 1": [10.0, 10.0], "TH2 4": [20.0, 20.0]}, index=i)
    n.objective = 60.0
    own = owners(n, bus_entities(n))
    assert own["Link"]["LA2 1 dedicated src to grid"] == "LA" and own["Link"]["dedicated plant line LA2 1 - TH2 4"].startswith("XB:LA|TH") and own["Generator"]["stock"] == "LA"
    L, ident, _ = country_cost_ledger(n); T = ledger_table(L)
    assert not (L.carrier == "dedicated plant source").any()   # zero cost, both ports in LA: not one row of the ledger
    assert T.at["LA", "total"] == pytest.approx(60.0 - 360.0 - 162.0) and T.at["TH", "total"] == pytest.approx(684.0 - 162.0)   # sale at the LA dual, corridor rent 324 half and half
    assert ident["relative_error"] < 1e-12 and ledger_gate(ident)["passed"]


def test_179_no_new_xb_keeps_the_cross_border_capacity():
    from m08a_layers import apply_stock_mode
    from v3_static import source_check, stock_by_pair
    from v5.v5_gates import gate_b5_no_new_xb
    n, _ = dedicated_toy(extras=True); n.lines["border_class"] = "domestic"; base = n.copy(); base.links["stock"] = n.links["stock"]; base.buses["role"] = n.buses["role"]; base.meta = dict(n.meta)
    led = apply_stock_mode(n, "no_new_xb")
    assert led["removed_links"] == 0 and gate_b5_no_new_xb(base, n)["passed"] and stock_by_pair(n, "").to_dict() == {"LA-TH": 5427.0, "LA-VN": 572.0}
    t, ok, bad = source_check(base, n)
    assert ok and not bad and len(t) == 5 and (t.border_class == "domestic").all()


def test_179_checks_refuse_a_broken_source():
    from v3_layers import source_bus_problems
    from v3_static import source_check

    def broken(f):
        n, _ = dedicated_toy(); n.lines["border_class"] = pd.Series(dtype=str); f(n); return source_bus_problems(n)

    k = "LA2 1 dedicated src to grid"
    assert not broken(lambda n: None)
    assert broken(lambda n: n.links.__setitem__("marginal_cost", n.links.marginal_cost.where(n.links.index != k, 1.0)))
    assert broken(lambda n: n.links.__setitem__("efficiency", n.links.efficiency.where(n.links.index != k, 0.99)))
    assert broken(lambda n: n.links.__setitem__("border_class", n.links.border_class.where(n.links.index != k, "cross_border")))
    assert broken(lambda n: n.links.__setitem__("p_nom", n.links.p_nom.where(n.links.index != k, 1.0)))
    assert broken(lambda n: n.add("Generator", "new wind", bus="LA2 1 dedicated src", p_nom_extendable=True))
    assert broken(lambda n: n.add("Load", "load on the source", bus="LA2 1 dedicated src", p_set=1.0))
    n, _ = dedicated_toy(); n.lines["border_class"] = pd.Series(dtype=str); r = n.copy(); r.buses["role"] = n.buses["role"]; r.links["stock"] = n.links["stock"]; r.meta = dict(n.meta)
    assert source_check(n, r)[1]
    r.links.loc[k, "border_class"] = "cross_border"
    assert not source_check(n, r)[1]


def test_179_struct_diff_reports_the_move_and_refuses_another_bus():
    import pypsa
    from v3_static import struct_diff

    def net(bus):
        n = pypsa.Network(); n.add("Bus", "LA2 3", carrier="AC", country="LA")
        for b in ("LA2 3 dedicated src", "LA2 4 dedicated src"):
            n.add("Bus", b, carrier="AC", country="LA")
        n.add("Generator", "existing_survivor::x", bus=bus, p_nom=10.0, carrier="ror existing")
        return n

    t, bad = struct_diff(net("LA2 3"), net("LA2 3 dedicated src"))
    assert not bad and "moved_to_source_bus:bus" in set(t.change)
    assert "changed Generator bus ror existing" in struct_diff(net("LA2 3"), net("LA2 4 dedicated src"))[1]
    assert not struct_diff(net("LA2 3 dedicated src"), net("LA2 3 dedicated src"))[1]   # bridge against v3: both sides on the source bus


def b13_toy(extra: dict | None = None):
    """two national liquid buses, a node bus, an ordinary link and a ship; extra = one more link: dict(name, bus0, bus1, border_class)"""
    import pypsa
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=2, freq="3h"))
    for b in ("ID methanol", "SG methanol", "ID1 0"):
        n.add("Bus", b)
    n.add("Link", "plant", bus0="ID1 0", bus1="ID methanol", p_nom=1.0, carrier="methanolisation")
    n.add("Link", "ship", bus0="ID methanol", bus1="SG methanol", p_nom=1.0, carrier="methanol ship")
    n.links["border_class"] = ["domestic", "maritime_trade"]
    if extra:
        n.add("Link", extra["name"], bus0=extra["bus0"], bus1=extra["bus1"], p_nom=1.0, carrier="toy")
        n.links.loc[extra["name"], "border_class"] = extra["border_class"]
    return n


def test_b13_ship_between_national_buses_passes():
    from v5.v5_gates import gate_b13_imports_one_way
    g = gate_b13_imports_one_way(b13_toy())
    assert g["passed"] and g["checks"]["pool_links_without_national_port"] == []


def test_b13_counterexamples_still_fail():
    from v5.v5_gates import gate_b13_imports_one_way
    # a link between two national buses that is not a ship or transit link: nothing in the rule explains it
    g = gate_b13_imports_one_way(b13_toy(dict(name="odd", bus0="ID methanol", bus1="SG methanol", border_class="domestic")))
    assert not g["passed"] and g["checks"]["pool_links_without_national_port"] == ["odd"]
    # the same with the column absent (a network from before V3)
    n = b13_toy(dict(name="odd", bus0="ID methanol", bus1="SG methanol", border_class="domestic")); n.links = n.links.drop(columns="border_class")
    assert not gate_b13_imports_one_way(n)["passed"]
    # a ship with a port outside the model: the maritime tag does not excuse it, energy would leave the network
    n = b13_toy(dict(name="leak", bus0="ID methanol", bus1="SG methanol", border_class="maritime_trade")); n.links.loc["leak", "bus1"] = "OUTSIDE methanol"
    g = gate_b13_imports_one_way(n)
    assert not g["passed"] and g["checks"]["pool_links_without_national_port"] == ["leak"]


def test_no_new_xb_stock_mode_toy():
    import pypsa
    from m08a_layers import apply_stock_mode
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=2, freq="3h"))
    for b, c in (("a", "AA"), ("b", "BB"), ("c", "BB")):
        n.add("Bus", b); n.buses.loc[b, "country"] = c
    n.add("Line", "stock", bus0="a", bus1="b", x=0.1, s_nom=100.0, s_nom_min=100.0, s_nom_extendable=True, s_nom_max=2100.0)
    n.add("Line", "cand", bus0="a", bus1="c", x=0.1, s_nom=0.0, s_nom_extendable=True)
    n.add("Line", "dom", bus0="b", bus1="c", x=0.1, s_nom=10.0, s_nom_extendable=True)
    n.add("Link", "gas", bus0="a", bus1="b", p_nom=50.0, p_nom_min=50.0, p_nom_extendable=True, p_nom_max=9e9)
    n.add("Link", "h2", bus0="a", bus1="b", p_nom=0.0, p_nom_extendable=True)
    n.lines["border_class"] = ["cross_border", "cross_border", "domestic"]; n.links["border_class"] = ["cross_border", "cross_border"]
    apply_stock_mode(n, "no_new_xb")
    assert set(n.lines.index) == {"stock", "dom"} and set(n.links.index) == {"gas"}
    assert not n.lines.at["stock", "s_nom_extendable"] and not n.links.at["gas", "p_nom_extendable"] and n.lines.at["dom", "s_nom_extendable"]
    assert n.lines.at["stock", "s_nom"] == 100.0 and n.links.at["gas", "p_nom"] == 50.0
