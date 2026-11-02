"""X1b code patch: layer, build call, transport carrier, config key, static check, structure allow-list."""
W = "/home/jin/wt_v3_20261102/"


def sub(path, pairs):
    s = open(path, encoding="utf-8", newline="").read()
    for a, b in pairs:
        assert s.count(a) == 1, (a[:70], s.count(a))
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8", newline="").write(s)


sub(W + "scripts_project/v3_layers.py", [
    ('''  * apply_ev_structure: research.s2.demand.ev_structure = smart (main, E2) | smart_v2g (E3) | uncontrolled (E4) | flat (v2).
"""''', '''  * apply_ev_structure: research.s2.demand.ev_structure = smart (main, E2) | smart_v2g (E3) | uncontrolled (E4) | flat (v2);
  * add_dedicated_plant_lines (X1b, decisions 172, 173): the Lao IPP export lines of research.network.dedicated_plant_lines_table, merged by plant node and landing node, one fixed lossy forward / '-reversed'
    pair each, in every scenario with the cross-border electricity switch on; empty key = v2 state.
"""'''),
    ('''EV_MODES = ("flat", "smart", "smart_v2g", "uncontrolled")
''', '''EV_MODES = ("flat", "smart", "smart_v2g", "uncontrolled")
DEDICATED_CARRIER = "dedicated plant line"
DEDICATED_STOCK = "dedicated_plant_line"
DEDICATED_LENGTH_FACTOR = 1.25   # lines.length_factor of the electric base: LA2 3 - TH2 1 great circle 222.9 km, model line 278.66 km
DEDICATED_LOSS_TYPE = ("Al/St 240/40 4-bundle 380.0", 380.0, 0.7)   # type, v_nom, s_max_pu of the cross-border AC lines: the loss proxy of decision 108 per km
'''),
    ('''def add_liquid_shipping(n, cfg, registry: pd.DataFrame) -> dict:
''', '''def great_circle_km(x0: float, y0: float, x1: float, y1: float) -> float:
    p0, p1 = np.radians(y0), np.radians(y1); dl = np.radians(x1 - x0); dp = p1 - p0
    return float(2.0 * 6371.0 * np.arcsin(np.sqrt(np.sin(dp / 2.0) ** 2 + np.cos(p0) * np.cos(p1) * np.sin(dl / 2.0) ** 2)))


def add_dedicated_plant_lines(n, cfg, repo, costs, existing_cfg) -> dict:
    """X1b: see the module docstring and V3_RULES.md section 2.2. After apply_ac_losses (the lossy split is done here: efficiency = 1 - proxy lambda over the length). The stock FOM rule of the corridors applies.
    Not added with the cross-border electricity switch off (fully disconnected network). p_nom_min = p_nom marks the stock for apply_stock_mode."""
    from s2_layers import add_link
    from s4d_layers import coalition_members
    from s4k_layers import ac_loss_mode, reference_loading, type_lambda_per_km
    R = cfg["research"]; table = (R.get("network") or {}).get("dedicated_plant_lines_table"); led = dict(table=table, links=0)
    if not table or not R["cross_border"]["electricity"]:
        n.meta["research_dedicated_lines"] = led
        return led
    t = pd.read_csv(Path(repo) / table); t = t[t.counted.astype(bool)]; units = n.meta["existing_unit_components"]; members = coalition_members(R["cross_border"]); gone = []
    for _, r in t.iterrows():
        for i in str(r.gem_unit_ids).split(";"):
            if units[f"GEM:{i}"]["node"] != r.plant_node:
                raise ValueError(f"X1b: {r.project} unit {i} is not at {r.plant_node}")
    ptype, v_nom, s_max = DEDICATED_LOSS_TYPE
    lam_km = type_lambda_per_km(n, ptype, reference_loading(cfg), s_max, v_nom) if ac_loss_mode(cfg) == "linear_proxy" else 0.0
    if "stock" not in n.links:
        n.links["stock"] = ""
    rows = []
    for (a, b), g in t.groupby(["plant_node", "landing_node"], sort=True):
        ca, cb = str(n.buses.at[a, "country"]), str(n.buses.at[b, "country"])
        if members is not None and not {ca, cb} <= members:
            gone.append(f"{a}-{b}")
            continue
        km = great_circle_km(float(n.buses.at[a, "x"]), float(n.buses.at[a, "y"]), float(n.buses.at[b, "x"]), float(n.buses.at[b, "y"])) * DEDICATED_LENGTH_FACTOR
        mw = float(g.contract_mw.sum()); eta = 1.0 - lam_km * km; name = f"dedicated plant line {a} - {b}"
        for x, f, to, co, rev in ((name, a, b, ca, False), (f"{name}-reversed", b, a, cb, True)):
            add_link(n, x, co, DEDICATED_CARRIER, [f, to], [eta], role="EXISTING_CROSS_BORDER_STOCK", length=0.0 if rev else km, extra={"length_original": km})
            n.links.loc[x, ["p_nom", "p_nom_min", "p_nom_max"]] = [mw, mw, mw]
            n.links.loc[x, "p_nom_extendable"] = False; n.links.loc[x, "reversed"] = rev; n.links.loc[x, "asset_role"] = "existing_cross_border_stock"
            n.links.loc[x, "border_class"] = "cross_border"; n.links.loc[x, "transport_carrier"] = "electricity"; n.links.loc[x, "stock"] = DEDICATED_STOCK
        fom = (float(costs.at["HVAC overhead", "FOM"]) / 100.0 * float(costs.at["HVAC overhead", "investment"]) * km * mw) if existing_cfg["fom_on_existing"] else 0.0
        rows.append(dict(link=name, plant_node=a, landing_node=b, pair="-".join(sorted((ca, cb))), projects=sorted(g.project), contract_mw=mw, length_km=km, efficiency=eta, annual_fom_eur=fom))
    if rows:
        fl = list(n.meta.get("existing_cross_border_fom_ledger", [])) + [dict(component_type="Link", component=r["link"], capacity_2025_mw=r["contract_mw"], length_km=r["length_km"], annual_fom_eur=r["annual_fom_eur"], cost_rows=["HVAC overhead"]) for r in rows if r["annual_fom_eur"]]
        n.meta["existing_cross_border_fom_ledger"] = fl; n.meta["existing_cross_border_fom_eur"] = float(sum(r["annual_fom_eur"] for r in fl))
    led.update(links=len(rows), lines=rows, total_mw=float(sum(r["contract_mw"] for r in rows)), loss_per_km=lam_km, coalition_removed=gone, annual_fom_eur=float(sum(r["annual_fom_eur"] for r in rows)))
    n.meta["research_dedicated_lines"] = led
    return led


def add_liquid_shipping(n, cfg, registry: pd.DataFrame) -> dict:
'''),
])
sub(W + "scripts_project/s2_network.py", [
    ('from v3_layers import add_liquid_shipping, apply_ev_structure\n', 'from v3_layers import add_dedicated_plant_lines, add_liquid_shipping, apply_ev_structure\n'),
    ('''    carbon_meta = install_carbon_metadata(n, R["carbon"])
    scaling = apply_cost_scaling(n, R["cost_scaling"])
''', '''    dedicated = add_dedicated_plant_lines(n, cfg, repo, costs, R["existing_cross_border_electricity"])   # V3 X1b (decisions 172, 173): fixed Lao IPP export lines, not in the disconnected network
    carbon_meta = install_carbon_metadata(n, R["carbon"])
    scaling = apply_cost_scaling(n, R["cost_scaling"])
'''),
])
sub(W + "scripts_project/scenario_network.py", [
    ("""TRANSPORT_CARRIERS={'AC':'electricity','DC':'electricity','B2B':'electricity','H2 pipeline':'H2','gas pipeline':'gas','CO2 pipeline':'co2'}""",
     """TRANSPORT_CARRIERS={'AC':'electricity','DC':'electricity','B2B':'electricity','dedicated plant line':'electricity','H2 pipeline':'H2','gas pipeline':'gas','CO2 pipeline':'co2'}"""),
])
sub(W + "configs/research/baseline.yaml", [
    ('''    ac_loss_reference_loading: 0.5        # S4K-1 (decision 108): alpha, reference loading as a share of the allowed loading of one circuit (main 0.5; sensitivity 1.0 = upper bound)
''', '''    ac_loss_reference_loading: 0.5        # S4K-1 (decision 108): alpha, reference loading as a share of the allowed loading of one circuit (main 0.5; sensitivity 1.0 = upper bound)
    dedicated_plant_lines_table: research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv   # V3 X1b (decisions 172, 173; scripts_project/v3_dedicated_lines.py, V3_RULES.md section 2.2): fixed Lao IPP export lines at contract capacity, in every scenario except the fully disconnected one | empty = v2 state
'''),
])
sub(W + "scripts_project/v3_static.py", [
    ('from v3_layers import LOAD_CARRIERS, SHIP_CARRIERS, TRANSIT_CARRIER   # noqa: E402', 'from v3_layers import DEDICATED_CARRIER, DEDICATED_STOCK, LOAD_CARRIERS, SHIP_CARRIERS, TRANSIT_CARRIER   # noqa: E402'),
    ('''               "Link": {"oil non-fossil ship", "methanol ship", "ammonia ship", TRANSIT_CARRIER, "oil pool",''', '''               "Link": {DEDICATED_CARRIER, "oil non-fossil ship", "methanol ship", "ammonia ship", TRANSIT_CARRIER, "oil pool",'''),
    ('''def stock_check(i, r, apg: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """X1 (V3_RULES section 2.1): APG existing = integrated lower bound = fixed capacity of no_new_xb, pair by pair; no cross-border electricity component of no_new_xb is extendable."""
    a = apg[apg.apg_existing_mw.notna()].groupby("country_pair").apg_existing_mw.sum().sort_index()
    t = pd.DataFrame(dict(apg_existing_mw=a, integrated_nom_min_mw=stock_by_pair(i, "min"), no_new_xb_fixed_mw=stock_by_pair(r, ""))).fillna(0.0).rename_axis("pair").reset_index()
    t["no_new_xb_usable_mw"] = t.pair.map(stock_by_pair(r, "", usable=True)).fillna(0.0)
    ok = bool(((t.apg_existing_mw - t.integrated_nom_min_mw).abs().max() <= 0.01) and ((t.apg_existing_mw - t.no_new_xb_fixed_mw).abs().max() <= 0.01))
''', '''def stock_check(i, r, apg: pd.DataFrame, dedicated: pd.DataFrame | None = None) -> tuple[pd.DataFrame, bool]:
    """X1, X1b (V3_RULES sections 2.1, 2.2): APG existing + counted plant lines = integrated lower bound = fixed capacity of no_new_xb, pair by pair; no cross-border electricity component of no_new_xb is extendable."""
    a = apg[apg.apg_existing_mw.notna()].groupby("country_pair").apg_existing_mw.sum().sort_index()
    d = pd.Series(dtype=float) if dedicated is None else dedicated[dedicated.counted.astype(bool)].assign(pair=lambda x: "LA-" + x.other_country).groupby("pair").contract_mw.sum()
    t = pd.DataFrame(dict(apg_existing_mw=a, dedicated_mw=d, integrated_nom_min_mw=stock_by_pair(i, "min"), no_new_xb_fixed_mw=stock_by_pair(r, ""))).fillna(0.0).rename_axis("pair").reset_index()
    t["no_new_xb_usable_mw"] = t.pair.map(stock_by_pair(r, "", usable=True)).fillna(0.0)
    e = t.apg_existing_mw + t.dedicated_mw
    ok = bool(((e - t.integrated_nom_min_mw).abs().max() <= 0.01) and ((e - t.no_new_xb_fixed_mw).abs().max() <= 0.01))
'''),
    ('''def demand_check(n) -> pd.Series:
''', '''def dedicated_links(n) -> pd.DataFrame:
    cols = ["bus0", "bus1", "carrier", "p_nom", "p_nom_min", "p_nom_max", "efficiency", "length_original", "p_nom_extendable", "border_class", "transport_carrier"]
    if "stock" not in n.links:
        return pd.DataFrame(columns=cols)
    return n.links[n.links.stock.astype(str) == DEDICATED_STOCK][cols]


def dedicated_check(i, r, d=None) -> tuple[pd.DataFrame, bool]:
    """X1b: the plant lines of integrated and no_new_xb, line by line (same buses, capacity, efficiency, not extendable, forward = reverse capacity); none in the disconnected network d."""
    x, y = dedicated_links(i), dedicated_links(r); fwd = x[~x.index.str.endswith("-reversed")]
    ok = bool(len(x) and x.equals(y) and not x.p_nom_extendable.astype(bool).any() and (x.border_class == "cross_border").all() and (x.transport_carrier == "electricity").all() and len(x) == 2 * len(fwd))
    ok = bool(ok and all(x.at[k + "-reversed", "p_nom"] == fwd.at[k, "p_nom"] and x.at[k + "-reversed", "bus0"] == fwd.at[k, "bus1"] for k in fwd.index))
    if d is not None:
        ok = bool(ok and not len(dedicated_links(d)))
    return fwd.rename_axis("link").reset_index(), ok


def demand_check(n) -> pd.Series:
'''),
    ('''    st, ok3 = stock_check(I3, R3, apg); _, ok1 = stock_check(I1, R1, apg); (a.out / "evidence").mkdir(exist_ok=True); st.to_csv(a.out / "evidence/X1_STOCK_TABLE_V3.csv", index=False)
    res["stock_x1"] = dict(passed=bool(ok3 and ok1), total_mw=float(st.apg_existing_mw.sum()), pairs=int(len(st)))
''', '''    ded = pd.read_csv(HERE.parent / "research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv")
    st, ok3 = stock_check(I3, R3, apg, ded); _, ok1 = stock_check(I1, R1, apg, ded); (a.out / "evidence").mkdir(exist_ok=True); st.to_csv(a.out / "evidence/X1_STOCK_TABLE_V3.csv", index=False)
    res["stock_x1"] = dict(passed=bool(ok3 and ok1), total_mw=float(st.apg_existing_mw.sum()), dedicated_mw=float(st.dedicated_mw.sum()), pairs=int(len(st)))
    f1 = a.dir / "disconnected/disconnected_365_24h_unsolved.nc"; D1 = pypsa.Network(str(f1)) if f1.exists() else None
    dl, dok3 = dedicated_check(I3, R3); _, dok1 = dedicated_check(I1, R1, D1); dl.to_csv(a.out / "evidence/X1B_LINES_V3.csv", index=False)
    res["dedicated_lines"] = dict(passed=bool(dok3 and dok1), links=int(len(dl)), total_mw=float(dl.p_nom.sum()), disconnected_checked=D1 is not None)
    us = st[st.pair.str.contains("LA")].assign(apg_usable_mw=lambda x: x.no_new_xb_usable_mw - x.dedicated_mw); us.to_csv(a.out / "evidence/LA_EXPORT_USABLE_V3.csv", index=False)
'''),
    ('''res["stock_x1"]["passed"] and res["gate_b5_no_new_xb"]["passed"]''', '''res["stock_x1"]["passed"] and res["dedicated_lines"]["passed"] and res["gate_b5_no_new_xb"]["passed"]'''),
    ('''{k: res[k] for k in ("stock_x1", "gate_b5_no_new_xb",''', '''{k: res[k] for k in ("stock_x1", "dedicated_lines", "gate_b5_no_new_xb",'''),
])
print("patched")
