"""Supplement 05: tests of decision 180 in tests/research/test_v3.py; commit.sh force-adds the status table."""
p = "/home/jin/wt_v3_20261102/tests/research/test_v3.py"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)


rep('''def dedicated_toy(electricity=True, extras=False):
    """every plant unit of the table is a fixed Generator of 100 MW with its identity; extras: the other stock kinds of the real nodes (reservoir StorageUnit, fuel Link in fuel terms) and what has to stay on the node"""
''', '''def dedicated_toy(electricity=True, extras=False, mixed=False):
    """every plant unit of the table is a fixed Generator of 100 MW with its identity; extras: the other stock kinds of the real nodes (reservoir StorageUnit, fuel Link in fuel terms) and what has to stay on the node;
    mixed: a construction unit, and a component of LA2 3 and one of LA2 5 with units of both kinds (decision 180)"""
''')
rep('''        n.add("Line", "domestic 1", bus0="LA2 2", bus1="LA2 3", x=0.1, s_nom=500.0)
''', '''        n.add("Line", "domestic 1", bus0="LA2 2", bus1="LA2 3", x=0.1, s_nom=500.0)
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
''')
rep('''    return n, add_dedicated_plant_lines(n, cfg, ROOT, costs, dict(fom_on_existing=True))
''', '''    return n, add_dedicated_plant_lines(n, cfg, ROOT, costs, dict(fom_on_existing=True), status=status)
''')
rep('''    with pytest.raises(ValueError, match="no stock generation"):
        bind_dedicated_sources(n, line)
''', '''    with pytest.raises(ValueError, match="no operating non-thermal stock"):
        bind_dedicated_sources(n, line, {})
''')
rep('''    with pytest.raises(ValueError, match="existing_unit_components"):
        bind_dedicated_sources(n, line)
''', '''    with pytest.raises(ValueError, match="existing_unit_components"):
        bind_dedicated_sources(n, line, {})
''')
rep('''def test_179_ledger_books_the_source_link_to_laos():
''', '''def stock_net(*units):
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
''')
open(p, "w", encoding="utf-8").write(s)
p = "/home/jin/v3/commit.sh"; s = open(p, encoding="utf-8").read()
rep("research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv research_inputs/corridors/APG_LA_TH_LINES_ACE2024.csv", "research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv research_inputs/corridors/DEDICATED_STOCK_STATUS_V3.csv research_inputs/corridors/APG_LA_TH_LINES_ACE2024.csv")
open(p, "w", encoding="utf-8").write(s)
print("patched")
