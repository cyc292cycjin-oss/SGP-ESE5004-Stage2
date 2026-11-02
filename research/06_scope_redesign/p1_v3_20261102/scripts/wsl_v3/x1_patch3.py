p = "/home/jin/wt_v3_20261102/scripts_project/v3_static.py"
s = open(p, encoding="utf-8").read()
a = '''def stock_by_pair(n, bound: str) -> pd.Series:
    """electricity cross-border stock by country pair (MW): bound = "min" reads s_nom_min / p_nom_min (integrated), "" reads the fixed s_nom / p_nom (no_new_xb)"""
    c = n.buses.country.astype(str); rows = {}
    K = n.links[(n.links.border_class == "cross_border") & (n.links.transport_carrier.astype(str) == "electricity")]
    for x, nom in ((n.lines[n.lines.border_class == "cross_border"], "s_nom"), (K, "p_nom")):
        for _, z in x.iterrows():
            k = "-".join(sorted((c[z.bus0], c[z.bus1]))); rows[k] = rows.get(k, 0.0) + float(z[nom + ("_min" if bound else "")])
    return pd.Series(rows).loc[lambda s: s > 0].sort_index()
'''
b = '''def stock_by_pair(n, bound: str, usable: bool = False) -> pd.Series:
    """electricity cross-border stock by country pair (MW): bound = "min" reads s_nom_min / p_nom_min (integrated), "" reads the fixed s_nom / p_nom (no_new_xb). The -reversed twin of a link is the same
    asset and counts once. usable: lines times s_max_pu (the links carry their full rating)."""
    c = n.buses.country.astype(str); rows = {}
    K = n.links[(n.links.border_class == "cross_border") & (n.links.transport_carrier.astype(str) == "electricity") & ~n.links.index.astype(str).str.endswith("-reversed")]
    for x, nom in ((n.lines[n.lines.border_class == "cross_border"], "s_nom"), (K, "p_nom")):
        for _, z in x.iterrows():
            k = "-".join(sorted((c[z.bus0], c[z.bus1]))); f = float(z.s_max_pu) if (usable and nom == "s_nom") else 1.0
            rows[k] = rows.get(k, 0.0) + f * float(z[nom + ("_min" if bound else "")])
    return pd.Series(rows).loc[lambda s: s > 0].sort_index()
'''
assert s.count(a) == 1; s = s.replace(a, b)
a = '''    t["usable_mw_s_max_pu_0_7"] = t.no_new_xb_fixed_mw * 0.7   # lines only; the 300 MW DC of MY-TH is not derated, see the report
'''
b = '''    t["no_new_xb_usable_mw"] = t.pair.map(stock_by_pair(r, "", usable=True)).fillna(0.0)
'''
assert s.count(a) == 1; s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
t = "/home/jin/wt_v3_20261102/tests/research/test_v3.py"
s = open(t, encoding="utf-8").read()
a = '''        n.add("Link", "gas", bus0="a", bus1="b", p_nom=0.0); n.links["border_class"] = "cross_border"; n.links["transport_carrier"] = "gas"
        return n
'''
b = '''        n.add("Link", "gas", bus0="a", bus1="b", p_nom=0.0); n.add("Link", "dc", bus0="a", bus1="b", p_nom=45.0, p_nom_min=45.0); n.add("Link", "dc-reversed", bus0="b", bus1="a", p_nom=45.0, p_nom_min=45.0)
        n.links["border_class"] = "cross_border"; n.links["transport_carrier"] = ["gas", "electricity", "electricity"]; n.links["p_nom_extendable"] = False
        return n
'''
assert s.count(a) == 1; s = s.replace(a, b)
a = '''    apg = pd.DataFrame(dict(country_pair=["LA-TH"], apg_existing_mw=[955.0]))
    t, ok = stock_check(net(True, 955.0), net(False, 0.0), apg)
    assert ok and t.no_new_xb_fixed_mw.iloc[0] == 955.0
    assert not stock_check(net(True, 900.0), net(False, 0.0), apg)[1]   # the integrated lower bound differs from the source
    assert not stock_check(net(True, 955.0), net(True, 0.0), apg)[1]   # a cross-border component of no_new_xb is extendable
'''
b = '''    apg = pd.DataFrame(dict(country_pair=["LA-TH"], apg_existing_mw=[1000.0]))
    t, ok = stock_check(net(True, 955.0), net(False, 0.0), apg)
    assert ok and t.no_new_xb_fixed_mw.iloc[0] == 1000.0   # the -reversed twin of the DC link counts once
    assert t.no_new_xb_usable_mw.iloc[0] == pytest.approx(955.0 + 45.0)   # s_max_pu of the toy line is 1
    assert not stock_check(net(True, 900.0), net(False, 0.0), apg)[1]   # the integrated lower bound differs from the source
    assert not stock_check(net(True, 955.0), net(True, 0.0), apg)[1]   # a cross-border component of no_new_xb is extendable
'''
assert s.count(a) == 1; s = s.replace(a, b)
open(t, "w", encoding="utf-8").write(s)
l = "/home/jin/v3/x1_load.py"
s = open(l).read()
a = 'K = n.links[(n.links.border_class == "cross_border") & (n.links.transport_carrier.astype(str) == "electricity")] if "transport_carrier" in n.links else n.links.iloc[0:0]\n'
b = 'K = n.links[(n.links.border_class == "cross_border") & (n.links.transport_carrier.astype(str) == "electricity") & ~n.links.index.astype(str).str.endswith("-reversed")]   # the -reversed twin is the same asset: its flow and dual are added to the forward link\n'
assert s.count(a) == 1; s = s.replace(a, b)
a = '''    cap = float(z.p_nom); f = n.links_t.p0[name]
    mu = (n.links_t["mu_upper"][name].abs() + n.links_t["mu_lower"][name].abs()).div(w)
'''
b = '''    cap = float(z.p_nom); t = name + "-reversed"; f = n.links_t.p0[name] - (n.links_t.p0[t] if t in n.links_t.p0 else 0.0)
    mu = (n.links_t["mu_upper"][name].abs() + n.links_t["mu_lower"][name].abs() + (n.links_t["mu_upper"][t].abs() if t in n.links_t["mu_upper"] else 0.0)).div(w)
'''
assert s.count(a) == 1; s = s.replace(a, b)
open(l, "w").write(s)
