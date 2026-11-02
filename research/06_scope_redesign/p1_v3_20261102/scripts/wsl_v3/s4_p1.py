"""Supplement 04: tests of decision 179 in tests/research/test_v3.py (toy with the stock kinds of the real nodes, source structure, ledger, B5, refusals)."""
p = "/home/jin/wt_v3_20261102/tests/research/test_v3.py"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)


rep('''def dedicated_toy(electricity=True):
    import pypsa
    from v3_layers import add_dedicated_plant_lines
''', '''def dedicated_toy(electricity=True, extras=False):
    """every plant unit of the table is a fixed Generator of 100 MW with its identity; extras: the other stock kinds of the real nodes (reservoir StorageUnit, fuel Link in fuel terms) and what has to stay on the node"""
    import pypsa
    from v3_layers import add_dedicated_plant_lines
''')
rep('''        n.add("Bus", b, carrier="AC", x=100.0 + i, y=15.0 + 0.5 * i); n.buses.loc[b, "country"] = b[:2]
    n.links["border_class"] = ""; n.links["transport_carrier"] = ""
    n.meta["existing_unit_components"] = {f"GEM:{i}": dict(node=r.plant_node) for _, r in t.iterrows() for i in r.gem_unit_ids.split(";")}
''', '''        n.add("Bus", b, carrier="AC", x=100.0 + i, y=15.0 + 0.5 * i, v_nom=380.0); n.buses.loc[b, "country"] = b[:2]
    n.links["border_class"] = ""; n.links["transport_carrier"] = ""
    ident = n.meta["existing_unit_components"] = {}
    for _, r in t.iterrows():
        for i in r.gem_unit_ids.split(";"):
            name = f"existing_survivor::GEM:{i}"
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
''')
rep('''    n.links["country"] = n.links["country"].astype(str); n.export_to_netcdf(tmp_path / "toy.nc")   # the build exports the network: no mixed column
    assert led["links"] == 6 and led["total_mw"] == 5999.0 and len(n.links) == 6 and not n.links.p_nom_extendable.any() and (n.links.border_class == "cross_border").all()
    f = n.links.loc["dedicated plant line LA2 3 - TH2 1"]
    assert f.p_nom == 1388.0 and f.p_nom_min == f.p_nom and f.bus0 == "LA2 3" and f.bus1 == "TH2 1" and f.stock == "dedicated_plant_line" and not f.reversed and f.p_min_pu == 0.0   # one way, supplement 03
    assert n.links.bus0.str.startswith("LA").all() and n.links.p_min_pu.eq(0.0).all()
''', '''    n.links["country"] = n.links["country"].astype(str); n.export_to_netcdf(tmp_path / "toy.nc")   # the build exports the network: no mixed column
    K = n.links[n.links.carrier == "dedicated plant line"]
    assert led["links"] == 6 and led["total_mw"] == 5999.0 and len(K) == 6 and not n.links.p_nom_extendable.any() and (K.border_class == "cross_border").all()
    f = n.links.loc["dedicated plant line LA2 3 - TH2 1"]
    assert f.p_nom == 1388.0 and f.p_nom_min == f.p_nom and f.bus0 == "LA2 3 dedicated src" and f.bus1 == "TH2 1" and f.stock == "dedicated_plant_line" and not f.reversed and f.p_min_pu == 0.0   # one way, supplement 03; source bus, decision 179
    assert n.links.bus0.str.startswith("LA").all() and n.links.p_min_pu.eq(0.0).all()
''')
rep('''    n, led = dedicated_toy(electricity=False)
    assert led["links"] == 0 and not len(n.links)
''', '''    from v3_layers import dedicated_source_buses
    n, led = dedicated_toy(electricity=False)
    assert led["links"] == 0 and not len(n.links) and "role" not in n.buses and not len(dedicated_source_buses(n)) and not n.buses.index.str.endswith("dedicated src").any()
''')
rep('''    assert not stock_check(n, n, apg, d.assign(contract_mw=[5000.0, 572.0]))[1]


''', '''    assert not stock_check(n, n, apg, d.assign(contract_mw=[5000.0, 572.0]))[1]


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
    with pytest.raises(ValueError, match="no stock generation"):
        bind_dedicated_sources(n, line)
    n = pypsa.Network(); n.add("Bus", "LA2 1", carrier="AC"); n.buses.loc["LA2 1", "country"] = "LA"; n.meta["existing_unit_components"] = {}
    n.add("Generator", "fixed without identity", bus="LA2 1", p_nom=5.0)
    with pytest.raises(ValueError, match="existing_unit_components"):
        bind_dedicated_sources(n, line)


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


''')
open(p, "w", encoding="utf-8").write(s)
print("patched")
