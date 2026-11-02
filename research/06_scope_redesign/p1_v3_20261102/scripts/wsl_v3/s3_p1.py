"""Supplement 03 items 2.1: one-way plant lines (LA -> TH, LA -> VN): layer, static check, tests, rules, limitations of decision 176, screening plan note."""
W = "/home/jin/wt_v3_20261102/"; D = W + "research/06_scope_redesign/p1_v3_20261102/"


def sub(path, pairs):
    s = open(path, encoding="utf-8", newline="").read()
    for a, b in pairs:
        assert s.count(a) == 1, (a[:80], s.count(a))
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8", newline="").write(s)


sub(W + "scripts_project/v3_layers.py", [
    ('''  * add_dedicated_plant_lines (X1b, decisions 172, 173): the Lao IPP export lines of research.network.dedicated_plant_lines_table, merged by plant node and landing node, one fixed lossy forward / '-reversed'
    pair each, in every scenario with the cross-border electricity switch on; empty key = v2 state.
''', '''  * add_dedicated_plant_lines (X1b, decisions 172, 173; supplement 03): the Lao IPP export lines of research.network.dedicated_plant_lines_table, merged by plant node and landing node, one fixed lossy one-way
    link LA -> other country each, in every scenario with the cross-border electricity switch on; empty key = v2 state.
'''),
    ('''    """X1b: see the module docstring and V3_RULES.md section 2.2. After apply_ac_losses (the lossy split is done here: efficiency = 1 - proxy lambda over the length). The stock FOM rule of the corridors applies.
''', '''    """X1b: see the module docstring and V3_RULES.md section 2.3. After apply_ac_losses (efficiency = 1 - proxy lambda over the length). One way, LA -> other country: an IPP line carries the plant output and no back feed (supplement 03). The stock FOM rule of the corridors applies.
'''),
    ('''        for x, f, to, co, rev in ((name, a, b, ca, False), (f"{name}-reversed", b, a, cb, True)):
            add_link(n, x, co, DEDICATED_CARRIER, [f, to], [eta], role="EXISTING_CROSS_BORDER_STOCK", length=0.0 if rev else km, extra={"length_original": km})
            n.links.loc[x, ["p_nom", "p_nom_min", "p_nom_max"]] = [mw, mw, mw]
            n.links.loc[x, "p_nom_extendable"] = False; n.links.loc[x, "reversed"] = rev; n.links.loc[x, "asset_role"] = "existing_cross_border_stock"
            n.links.loc[x, "border_class"] = "cross_border"; n.links.loc[x, "transport_carrier"] = "electricity"; n.links.loc[x, "stock"] = DEDICATED_STOCK
''', '''        add_link(n, name, ca, DEDICATED_CARRIER, [a, b], [eta], role="EXISTING_CROSS_BORDER_STOCK", length=km, extra={"length_original": km})
        n.links.loc[name, ["p_nom", "p_nom_min", "p_nom_max"]] = [mw, mw, mw]
        n.links.loc[name, "p_nom_extendable"] = False; n.links.loc[name, "reversed"] = False; n.links.loc[name, "asset_role"] = "existing_cross_border_stock"
        n.links.loc[name, "border_class"] = "cross_border"; n.links.loc[name, "transport_carrier"] = "electricity"; n.links.loc[name, "stock"] = DEDICATED_STOCK
'''),
])
sub(W + "scripts_project/v3_static.py", [
    ('''    cols = ["bus0", "bus1", "carrier", "p_nom", "p_nom_min", "p_nom_max", "efficiency", "length_original", "p_nom_extendable", "border_class", "transport_carrier"]
''', '''    cols = ["bus0", "bus1", "carrier", "p_nom", "p_nom_min", "p_nom_max", "p_min_pu", "efficiency", "length_original", "p_nom_extendable", "border_class", "transport_carrier"]
'''),
    ('''    """X1b: the plant lines of integrated and no_new_xb, line by line (same buses, capacity, efficiency, not extendable, forward = reverse capacity); none in the disconnected network d."""
    x, y = dedicated_links(i), dedicated_links(r); fwd = x[~x.index.str.endswith("-reversed")]
    ok = bool(len(x) and x.equals(y) and not x.p_nom_extendable.astype(bool).any() and (x.border_class == "cross_border").all() and (x.transport_carrier == "electricity").all() and len(x) == 2 * len(fwd))
    ok = bool(ok and all(x.at[k + "-reversed", "p_nom"] == fwd.at[k, "p_nom"] and x.at[k + "-reversed", "bus0"] == fwd.at[k, "bus1"] for k in fwd.index))
    if d is not None:
        ok = bool(ok and not len(dedicated_links(d)))
    return fwd.rename_axis("link").reset_index(), ok
''', '''    """X1b, supplement 03: the plant lines of integrated and no_new_xb, line by line (same buses, capacity, efficiency, not extendable); one way from a Lao node (no reverse link, p_min_pu 0); none in the disconnected network d."""
    x, y = dedicated_links(i), dedicated_links(r)
    ok = bool(len(x) and x.equals(y) and not x.p_nom_extendable.astype(bool).any() and (x.border_class == "cross_border").all() and (x.transport_carrier == "electricity").all())
    ok = bool(ok and (x.p_min_pu == 0.0).all() and x.bus0.str.startswith("LA").all() and not x.index.str.endswith("-reversed").any())
    if d is not None:
        ok = bool(ok and not len(dedicated_links(d)))
    return x.rename_axis("link").reset_index(), ok
'''),
])
sub(W + "tests/research/test_v3.py", [
    ('''    assert led["links"] == 6 and led["total_mw"] == 5999.0 and len(n.links) == 12 and not n.links.p_nom_extendable.any() and (n.links.border_class == "cross_border").all()
    f = n.links.loc["dedicated plant line LA2 3 - TH2 1"]; r = n.links.loc["dedicated plant line LA2 3 - TH2 1-reversed"]
    assert f.p_nom == r.p_nom == 1388.0 and f.p_nom_min == f.p_nom and f.bus0 == r.bus1 and f.efficiency == r.efficiency and f.stock == r.stock == "dedicated_plant_line" and r.reversed and not f.reversed
''', '''    assert led["links"] == 6 and led["total_mw"] == 5999.0 and len(n.links) == 6 and not n.links.p_nom_extendable.any() and (n.links.border_class == "cross_border").all()
    f = n.links.loc["dedicated plant line LA2 3 - TH2 1"]
    assert f.p_nom == 1388.0 and f.p_nom_min == f.p_nom and f.bus0 == "LA2 3" and f.bus1 == "TH2 1" and f.stock == "dedicated_plant_line" and not f.reversed and f.p_min_pu == 0.0   # one way, supplement 03
    assert n.links.bus0.str.startswith("LA").all() and n.links.p_min_pu.eq(0.0).all()
'''),
    ('''    p = stock_by_pair(n, "min"); assert p["LA-TH"] == 5427.0 and p["LA-VN"] == 572.0   # the twin counts once
''', '''    p = stock_by_pair(n, "min"); assert p["LA-TH"] == 5427.0 and p["LA-VN"] == 572.0
'''),
    ('''    assert led["kept_links_forward"] == 6 and led["kept_reversed_twins"] == 6 and led["removed_links"] == 0
''', '''    assert led["kept_links_forward"] == 6 and led["kept_reversed_twins"] == 0 and led["removed_links"] == 0
'''),
    ('''def test_x1b_stock_check_counts_the_lines():
''', '''def test_x1b_check_refuses_a_reverse_link():
    from v3_static import dedicated_check
    n, _ = dedicated_toy(); r = n.copy(); r.links.loc[r.links.index[0], "p_min_pu"] = -1.0; r.links["stock"] = n.links["stock"]
    assert dedicated_check(n, n)[1] and not dedicated_check(r, r)[1]


def test_x1b_stock_check_counts_the_lines():
'''),
])
sub(D + "V3_RULES.md", [
    ('''- 按"电站所在 LA 节点 + 着陆节点"合并（审阅决定允许），得 6 条专线，每条一对 forward / `-reversed` Link，双向，不可扩建，`p_nom` = 合同容量之和。
''', '''- 按"电站所在 LA 节点 + 着陆节点"合并（审阅决定允许），得 6 条专线，每条一根**单向** Link（`p_min_pu = 0`，只允许 LA → TH、LA → VN，没有 `-reversed` 孪生），不可扩建，`p_nom` = 合同容量之和。APG 955 MW 电网互联线保持双向。
'''),
    ('''**简化（写入局限）：** 专线不绑定电站，可双向，也可供节点上其他机组使用；合同容量低于或等于电站容量；''', '''**单向的理由（补充 03，2026-11-03，取代补充 02 的双向）：** 补充 02 的冒烟里，`no_new_xb` 的 LA–TH 来回电量从 4.3 增到 25.7 TWh，净出口只增 1.6 TWh，专线被用作双向调节。现实中电站专线把电站出力送往泰国（越南）电网，不承担反向送电；双向会高估对照情景中老挝与泰国（越南）的互联程度。容量、损耗、FOM 不变。

**简化（写入局限）：** 专线不绑定电站，老挝其他机组也可经专线出口；合同容量低于或等于电站容量；'''),
])
p = D + "V3_RULES.md"; s = open(p, encoding="utf-8", newline="").read(); i = s.index("## 10. 局限（第 176 项，不完整）")
s = s[:i] + """## 10. 局限（第 176 项）

冒烟之后补入，只是局限说明，不涉及求解规则或预测。原文见 `V3_LIMITATIONS_ITEM176.md`（审阅端从决策清单抄出，用户 2026-11-03 已确认）。

1. ID 官方统计（HEESI）无工业子部门，只对有色金属自下而上，"其他"仍占 ID 工业约三分之二；镍产量 2019→2023 增三倍，2023 基年作敏感性。
2. VN 子部门用 APEC 2022，与 2019 基年不一致；套用 PyPSA-Eur 2050 载体比例后，VN 工业固定生物质 181.4 TWh 约为 APEC 2022 VN 工业生物质的 3 倍，VN 固定生物质需求 197.6 TWh 超过可持续潜力 125.8 TWh，超出 71.9 TWh 按第 133 项规则改为有用热；属欧洲载体结构套用到东盟的局限。
3. 设施分布按 2024–2026 存量外推到 2050 的 3–4 倍增长。
4. EV 曲线为欧洲乘用车（RAMP），东盟两三轮车比例高、电池小；车队代理 C 级，可能高估 EV 灵活性；flat 与车队 ×0.5 敏感性在 2920×3h 正式运行后做。
5. 液体码头与船运无容量约束（固定上界不绑定）；国内液体配送加价取 0。
6. MY–SG 天然气管道容量缺失（DATA_PENDING），主算不建。
7. 365×24h 筛查看不到 EV 日内效应，筛查 B6 与 2920×3h 正式值的差距可能大于 v2。
8. 电站专线（第 173 项）作为一般跨境容量建模：可双向、不绑定电站，是简化。专线改为单向（第 2 节）；仍不绑定电站，老挝其他机组也可经专线出口，这一点是简化。

已核实非问题：建筑电力小时形状来自 GEGIS 逐国曲线（相关系数 ≈ 1.0；LA、TL 借用 KH、ID，第 131 项），不是单一曲线套用。

**审阅决定另加的备注（`V3_REVIEW_DECISIONS_SUPP02.md`）：** ACE 2024 的 5,934.9 MW 发电并网互联比 EPPO 的 5,427 MW 高 507.9 MW。维持 EPPO 为唯一来源，这个差额作为上界敏感性备注，不运行。
"""
open(p, "w", encoding="utf-8", newline="").write(s)
sub(D + "RUN_PLAN_SCREEN_V3.md", [
    ('''修订桥三步：v2（DFX V1）→ V4 → V5 → V1。全部含 X1b。
''', '''修订桥三步：v2（DFX V1）→ V4 → V5 → V1。全部含 X1b，专线为单向（补充 03）。

`RUN_PLAN_V3.md` 第 15.5 节中 B6"相对 X1b 前"那一项**无法直接检验**：365×24h 没有不含专线的 v3 运行，审阅决定不加这次运行。筛查报告如实说明；若师哥审阅时问到，再作为敏感性补跑。
'''),
])
print("patched")
