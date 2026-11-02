p = "/home/jin/wt_v3_20261102/scripts_project/v3_static.py"
s = open(p, encoding="utf-8").read()
a = 'res["all_structural_passed"] = bool(res["gate_b5_no_new_xb"]["passed"]'
b = 'res["all_structural_passed"] = bool(res["stock_x1"]["passed"] and res["gate_b5_no_new_xb"]["passed"]'
assert s.count(a) == 1
s = s.replace(a, b)
a = 'print(json.dumps({k: res[k] for k in ("gate_b5_no_new_xb", '
b = 'print(json.dumps({k: res[k] for k in ("stock_x1", "gate_b5_no_new_xb", '
assert s.count(a) == 1
s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
t = "/home/jin/wt_v3_20261102/tests/research/test_v3.py"
s = open(t, encoding="utf-8").read()
a = "def b13_toy(extra: dict | None = None):"
b = '''def test_x1_apg_existing_is_the_stock_source():
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
        n.add("Link", "gas", bus0="a", bus1="b", p_nom=0.0); n.links["border_class"] = "cross_border"; n.links["transport_carrier"] = "gas"
        return n
    apg = pd.DataFrame(dict(country_pair=["LA-TH"], apg_existing_mw=[955.0]))
    t, ok = stock_check(net(True, 955.0), net(False, 0.0), apg)
    assert ok and t.no_new_xb_fixed_mw.iloc[0] == 955.0
    assert not stock_check(net(True, 900.0), net(False, 0.0), apg)[1]   # the integrated lower bound differs from the source
    assert not stock_check(net(True, 955.0), net(True, 0.0), apg)[1]   # a cross-border component of no_new_xb is extendable


def b13_toy(extra: dict | None = None):'''
assert s.count(a) == 1
s = s.replace(a, b)
open(t, "w", encoding="utf-8").write(s)
