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


def dedicated_toy(electricity=True):
    import pypsa
    from v3_layers import add_dedicated_plant_lines
    t = pd.read_csv(ROOT / "research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv")
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=2, freq="3h"))
    for i, b in enumerate(sorted(set(t.plant_node) | set(t.landing_node))):
        n.add("Bus", b, carrier="AC", x=100.0 + i, y=15.0 + 0.5 * i); n.buses.loc[b, "country"] = b[:2]
    n.links["border_class"] = ""; n.links["transport_carrier"] = ""
    n.meta["existing_unit_components"] = {f"GEM:{i}": dict(node=r.plant_node) for _, r in t.iterrows() for i in r.gem_unit_ids.split(";")}
    n.meta["existing_cross_border_fom_eur"] = 5.0; n.meta["existing_cross_border_fom_ledger"] = [dict(component_type="Line", component="x", capacity_2025_mw=1.0, length_km=1.0, annual_fom_eur=5.0, cost_rows=[])]
    cfg = dict(research=dict(network=dict(dedicated_plant_lines_table="research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv", ac_losses="linear_proxy", ac_loss_reference_loading=0.5, transmission_losses="pypsa_eur"), cross_border=dict(electricity=electricity, H2=electricity, gas=electricity, co2=electricity)))
    costs = pd.DataFrame(dict(FOM=[2.0], investment=[500.0]), index=["HVAC overhead"])
    return n, add_dedicated_plant_lines(n, cfg, ROOT, costs, dict(fom_on_existing=True))


def test_x1b_layer_toy(tmp_path):
    from v3_static import stock_by_pair
    n, led = dedicated_toy(); n.lines["border_class"] = pd.Series(dtype=str)
    n.links["country"] = n.links["country"].astype(str); n.export_to_netcdf(tmp_path / "toy.nc")   # the build exports the network: no mixed column
    assert led["links"] == 6 and led["total_mw"] == 5999.0 and len(n.links) == 12 and not n.links.p_nom_extendable.any() and (n.links.border_class == "cross_border").all()
    f = n.links.loc["dedicated plant line LA2 3 - TH2 1"]; r = n.links.loc["dedicated plant line LA2 3 - TH2 1-reversed"]
    assert f.p_nom == r.p_nom == 1388.0 and f.p_nom_min == f.p_nom and f.bus0 == r.bus1 and f.efficiency == r.efficiency and f.stock == r.stock == "dedicated_plant_line" and r.reversed and not f.reversed
    assert 0.0 < f.efficiency < 1.0 and 1.0 - f.efficiency == pytest.approx(led["loss_per_km"] * f.length) and led["loss_per_km"] * 100.0 == pytest.approx(0.012, rel=0.2)
    p = stock_by_pair(n, "min"); assert p["LA-TH"] == 5427.0 and p["LA-VN"] == 572.0   # the twin counts once
    assert n.meta["existing_cross_border_fom_eur"] == pytest.approx(5.0 + led["annual_fom_eur"]) and len(n.meta["existing_cross_border_fom_ledger"]) == 7


def test_x1b_not_in_the_disconnected_network():
    n, led = dedicated_toy(electricity=False)
    assert led["links"] == 0 and not len(n.links)


def test_x1b_stock_mode_keeps_the_lines_fixed():
    from m08a_layers import apply_stock_mode
    from v3_static import dedicated_check
    n, _ = dedicated_toy(); n.lines["border_class"] = pd.Series(dtype=str); base = n.copy(); base.links["stock"] = n.links["stock"]; base.meta = dict(n.meta)
    led = apply_stock_mode(n, "no_new_xb")
    assert led["kept_links_forward"] == 6 and led["kept_reversed_twins"] == 6 and led["removed_links"] == 0
    t, ok = dedicated_check(base, n)
    assert ok and len(t) == 6 and t.p_nom.sum() == 5999.0


def test_x1b_stock_check_counts_the_lines():
    from v3_static import stock_check
    n, _ = dedicated_toy(); n.lines["border_class"] = pd.Series(dtype=str)
    d = pd.DataFrame(dict(counted=[True, True], other_country=["TH", "VN"], contract_mw=[5427.0, 572.0]))
    apg = pd.DataFrame(dict(country_pair=["LA-TH"], apg_existing_mw=[0.0]))
    t, ok = stock_check(n, n, apg, d)
    assert ok and t.set_index("pair").dedicated_mw.to_dict() == {"LA-TH": 5427.0, "LA-VN": 572.0}
    assert not stock_check(n, n, apg, d.assign(contract_mw=[5000.0, 572.0]))[1]


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
