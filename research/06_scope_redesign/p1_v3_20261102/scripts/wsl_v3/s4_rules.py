"""Supplement 04: decision 179 in V3_RULES.md, before the build."""
p = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/V3_RULES.md"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)


rep("""**简化（写入局限）：** 专线不绑定电站，老挝其他机组也可经专线出口；合同容量低于或等于电站容量；""",
    """**简化（写入局限）：** ~~专线不绑定电站，老挝其他机组也可经专线出口~~（已被第 179 项取代，见第 2.4 节）；合同容量低于或等于电站容量；""")
rep("""**对照（不是来源）：** ACE 的 5,934.9 MW 比 EPPO 的 5,427 MW 高 507.9 MW，审阅决定以 EPPO 为唯一来源，这一差额未计入。
""", """**对照（不是来源）：** ACE 的 5,934.9 MW 比 EPPO 的 5,427 MW 高 507.9 MW，审阅决定以 EPPO 为唯一来源，这一差额未计入。

### 2.4 第 179 项：专线只输送存量电站出力（补充 04，2026-11-03，筛查前）

**依据：** `V3_REVIEW_DECISIONS_SUPP03.md` 第 2 节。**理由：** 专线是电站接到邻国电网的放射线。对照情景的定义是"没有新增跨境输电"，让新建风光接入专线，等于新建了跨境输电能力，与定义不符。本次修改是为了让对照情景的定义自洽，不是因为 B6 的数值。

**结构（不加自定义约束，`v3_layers.bind_dedicated_sources`）：** 对每个有专线出发的 LA 节点 n（`LA2 1`–`LA2 5`；`LA2 4` 有 TH、VN 两条，共用一个源母线；`LA2 0` 没有专线，不动）：

1. 新母线 `n dedicated src`：country = LA，carrier = AC，x、y、v_nom 同 n，location = n，`role = dedicated_plant_source`。
2. 把 n 上全部存量发电移到该母线，参数不变（只改母线）。负荷、可扩建机组、储能、其他线路和链路仍在 n。
3. 新链路 `n dedicated src to grid`：`n dedicated src` → n，载体 `dedicated plant source`，单向（`p_min_pu = 0`）、无损（效率 1）、不可扩建，`p_nom = p_nom_min = p_nom_max` = 移入出力上限合计，边际成本和投资成本都是 0，`research_role = asset_role = dedicated_src_to_grid`，`border_class = domestic`，`transport_carrier = electricity`。**不是跨境。**
4. 从 n 出发的专线起点改为 `n dedicated src`。容量、损耗、FOM、单向、线路名都不变；长度仍按 n 的坐标算（源母线坐标同 n）。
5. 一体化、`no_new_xb` 及修订桥相同；完全隔离没有专线，这一层不执行，连 `role` 列都没有。

结果：专线只能输送该节点存量电站的出力；存量电站照常向 LA 本地供电；新建机组只能经 APG 电网互联线（及一体化中的新建走廊）出口。

**移入判据：** 以构建回执的存量标识 `existing_unit_components` 为准。节点上 `p_nom_extendable=False` 的 Generator、StorageUnit，加 `bus1 = n` 且不可扩建的 Link，必须与 `node = n` 的标识逐一对应；多一个或少一个都使构建报错（`dedicated_stock_at`），不静默处理。`external coal`、`external lignite` 是燃料母线上的燃料供应，`process emissions`、`plastic waste` 不是发电机组，都不在 n 上，不移动。`existing_unit_components` 的 `node` 不改，仍是 LA 节点。某节点移入容量为 0，构建报错（审阅决定第 2.3 节的停止条件）。

**对审阅决定文字的三点补充（实施时发现，求解前写明）：**

- **存量火电是 Link，不是 Generator。** 第 2.1 节只写了 Generator 与 StorageUnit，括号里却列了火电。LA 的存量火电是燃料 Link：`existing_survivor::LA2 5::Lignite::…`（Hongsa，`lignite existing`，`p_nom` 5,690.91 MW 是燃料口径，出力 1,878 MW）、`existing_survivor::LA2 4::coal existing::S4A`（`p_nom` 842.70 MW，出力 300 MW）。移动的是它们的 `bus1`（输出端），燃料端 `bus0` 与排放端不变；计入源链路 `p_nom` 时按 `p_nom × efficiency`。不这样做，Hongsa 就留在 n 上而专线接不到它，与第 2.1 节"火电"的文字相反。
- **"存量"含在建机组。** `existing_survivor` 里有 GEM 状态为 construction 的机组（Luang Prabang、Pak Beng、Pak Lay 等，投运年 2030 前后）。审阅决定说以构建回执的存量标识为准，所以都移入。求解前的容量表（`RUN_PLAN_V3.md` 第 19.2 节）分列。
- **存量风电同样移入。** `existing_survivor::LA2 1::onwind existing::S4B1`（350 MW）是存量 Generator，按同一判据移入。这是"全部存量发电"的字面结果，它不是电站专线合同的一部分，属下文"非合同存量也可出口"的简化。

**源母线不是地理节点。** 它的 carrier 是 AC（审阅决定），但只是一个汇流点：`static_validate_s2` 的"100 个地理节点"和逐节点结构检查按 `role` 把它排除；`gate_b11_supply_routes` 不改，它没有负荷，按既有规则列为辅助节点；`struct_diff` 把机组移到本节点源母线列为 `moved_to_source_bus`，移到别处仍不通过。**阈值、判据都不改。**

**记账：** 源母线 country = LA，新链路两端都在 LA，由 `s4d_ledger.owners` 归 LA，成本为 0，既不产生结算也不进跨境账；专线的走廊实体不变，只是 LA 一端的结算点从 n 改为源母线。记账代码未改。

**静态检查：** `v3_layers.source_bus_problems`（构建时）和 `v3_static.source_check`（并入 `all_structural_passed`）核对：源母线上只有带标识的固定机组，没有抽水，没有负荷、Store、线路；出口只有一条源链路加该节点的专线；源链路无损、零成本、不可扩建、单向、domestic，容量等于出力上限合计；两情景逐条相同；完全隔离没有。
""")
rep("""| Link（`oil pool`，2026-11-02 补记） |""", """| Bus、Link（第 179 项，2026-11-03） | 增 5 条源母线 `LA2 n dedicated src`（carrier AC，不是地理节点）、5 条 `dedicated plant source` 链路；LA 专线节点的存量 Generator、StorageUnit、燃料 Link 的母线移到源母线（`moved_to_source_bus`），其余属性不变 |
| Link（`oil pool`，2026-11-02 补记） |""")
rep("""8. 电站专线（第 173 项）作为一般跨境容量建模：可双向、不绑定电站，是简化。专线改为单向（第 2 节）；仍不绑定电站，老挝其他机组也可经专线出口，这一点是简化。
""", """8. 电站专线（第 173 项）作为一般跨境容量建模。专线改为单向，只输送存量电站出力（第 2.3、2.4 节）。按聚类节点而不是按具体合同电站绑定，节点上非合同的存量电站也可经专线出口，是上界；不按购电合同份额限制。（本条按 `V3_REVIEW_DECISIONS_SUPP03.md` 第 2.1 节替换原句，原文见 `V3_LIMITATIONS_ITEM176.md`。）
""")
open(p, "w", encoding="utf-8").write(s)
print("rules patched")
