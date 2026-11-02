"""X1b patch 2: ACE line table, registry rows, tests, commit list."""
W = "/home/jin/wt_v3_20261102/"


def sub(path, pairs):
    s = open(path, encoding="utf-8", newline="").read()
    for a, b in pairs:
        assert s.count(a) == 1, (a[:70], s.count(a))
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8", newline="").write(s)


sub(W + "scripts_project/v3_dedicated_lines.py", [
    ('''OUT = ROOT / "research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv"
''', '''OUT = ROOT / "research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv"
OUT_ACE = ROOT / "research_inputs/corridors/APG_LA_TH_LINES_ACE2024.csv"
ACE_SHA_FILE = "ACE2024_APG_Interconnections_Project_Profiles.pdf (raw8), no. 9 Thailand - Lao PDR, profile p.21-23"
# every line of the profile is 115 kV HVAC with the agreement type Energy Exchange: the 955 MW of APG Table 1 are these seven lines, the 5,934.9 MW of generation-to-grid interconnections stand apart
ACE_LINES = [("Tha Li - Ken Thao", 100.0, 2020), ("Nong Khai - Dongphosy", 100.0, 2007), ("Nong Khai - Thanalaeng", 100.0, 1968), ("Bueng Kan - Pakxan", 100.0, 2002), ("Nakhon Phanom - Thakhek", 180.0, 2010),
             ("Mukdahan 2 - Pak Bo", 100.0, 1996), ("Sirindhorn 2 - Bang Yo", 275.0, 2020)]
'''),
    ('''    t = pd.DataFrame(rows); t.to_csv(OUT, index=False, float_format="%.10g")
''', '''    t = pd.DataFrame(rows); t.to_csv(OUT, index=False, float_format="%.10g")
    pd.DataFrame([dict(line=k, voltage_kv=115, agreement="Energy Exchange", line_capacity_mw=m, cod=y, source=ACE_SHA_FILE) for k, m, y in ACE_LINES]).to_csv(OUT_ACE, index=False)
'''),
])
sub(W + "scripts_project/v3_data.py", [
    ('''    for r in reg.rows:   # registry validation: numeric grade C rows carry a range; +-50 % like research.liquids.ship_cost_scale
''', '''    # ---- X1b, decisions 172, 173 ---------------------------------------------------------------------------------------------------------------------
    DL = ROOT / "research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv"; dl = pd.read_csv(DL); dl = dl[dl.counted.astype(bool)]; EPPO = "680ed5756fafcc82692c182cb774c0fa0c0a40a4ab38cb8ad431bfb041f2c25a"
    reg.add("dedicated_plant_lines_la_th_mw", "Lao IPP export lines to Thailand, contract capacity of the 9 EPPO projects, all operating in GEM GIPT 2026-09 and in the existing fleet of the network", float(dl[dl.other_country == "TH"].contract_mw.sum()), "MW", "B", "EPPO Power purchased from Laos PDR, page of 29 March 2016, archived 2026-06-11", "work/p2_data_intake/v3_20261102/01_industry/EPPO_power_purchased_from_Lao_PDR.pdf", EPPO, decision_ref="172,173")
    reg.add("dedicated_plant_lines_la_vn_mw", "Lao IPP export lines to Viet Nam: Xekaman 1 322 MW, Xekaman 3 250 MW (GEM, operating)", float(dl[dl.other_country == "VN"].contract_mw.sum()), "MW", "B", "GEM GIPT 2026-09, decision 100", "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv", sha256(ROOT / "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv"), decision_ref="172,173")
    reg.add("dedicated_plant_lines_table", "Project table: EPPO capacity, GEM status and start year, plant node, landing node (nearest node of the other country), line length", "research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv", "file", "B", "decisions 172, 173", "scripts_project/v3_dedicated_lines.py", sha256(DL), decision_ref="172,173")
    AL = ROOT / "research_inputs/corridors/APG_LA_TH_LINES_ACE2024.csv"; al = pd.read_csv(AL)
    reg.add("apg_la_th_grid_lines_mw", "The APG 955 MW of Thailand - Lao PDR: seven 115 kV Energy Exchange lines; no plant-dedicated line inside (X1b overlap check)", float(al.line_capacity_mw.sum()), "MW", "B", "ACE 2024 APG Interconnections Project Profiles no. 9", "p.21-23", sha256(AL), decision_ref="173")
    for r in reg.rows:   # registry validation: numeric grade C rows carry a range; +-50 % like research.liquids.ship_cost_scale
'''),
])
sub(W + "tests/research/test_v3.py", [
    ('''def b13_toy(extra: dict | None = None):
''', '''def test_x1b_table_and_the_apg_lines():
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
    for b in sorted(set(t.plant_node) | set(t.landing_node)):
        n.add("Bus", b, carrier="AC", x=100.0 + hash_free(b), y=15.0 + hash_free(b)); n.buses.loc[b, "country"] = b[:2]
    n.links["border_class"] = ""; n.links["transport_carrier"] = ""
    n.meta["existing_unit_components"] = {f"GEM:{i}": dict(node=r.plant_node) for _, r in t.iterrows() for i in r.gem_unit_ids.split(";")}
    n.meta["existing_cross_border_fom_eur"] = 5.0; n.meta["existing_cross_border_fom_ledger"] = [dict(component_type="Line", component="x", capacity_2025_mw=1.0, length_km=1.0, annual_fom_eur=5.0, cost_rows=[])]
    cfg = dict(research=dict(network=dict(dedicated_plant_lines_table="research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv", ac_losses="linear_proxy", ac_loss_reference_loading=0.5, transmission_losses="pypsa_eur"), cross_border=dict(electricity=electricity, H2=electricity, gas=electricity, co2=electricity)))
    costs = pd.DataFrame(dict(FOM=[2.0], investment=[500.0]), index=["HVAC overhead"])
    return n, add_dedicated_plant_lines(n, cfg, ROOT, costs, dict(fom_on_existing=True))


def hash_free(b: str) -> float:
    """a coordinate offset from the node name (no use of Python hash)"""
    return (sum(map(ord, b)) % 7) / 2.0


def test_x1b_layer_toy():
    from v3_static import stock_by_pair
    n, led = dedicated_toy()
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
'''),
])
sub("/home/jin/v3/commit.sh", [
    ('''git add -f research_inputs/industry_v3 research_inputs/transport_v3 research_inputs/liquids_v3 research_inputs/registry_v5/fragments/v3.csv 2>/dev/null || true
''', '''git add -f research_inputs/industry_v3 research_inputs/transport_v3 research_inputs/liquids_v3 research_inputs/registry_v5/fragments/v3.csv research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv research_inputs/corridors/APG_LA_TH_LINES_ACE2024.csv 2>/dev/null || true
'''),
])
print("patched")
