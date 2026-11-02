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
