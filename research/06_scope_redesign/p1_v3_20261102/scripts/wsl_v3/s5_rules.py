"""Supplement 05: decision 180 in V3_RULES.md, before the build."""
p = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/V3_RULES.md"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)


rep("""- **"存量"含在建机组。** `existing_survivor` 里有 GEM 状态为 construction 的机组（Luang Prabang、Pak Beng、Pak Lay 等，投运年 2030 前后）。审阅决定说以构建回执的存量标识为准，所以都移入。求解前的容量表（`RUN_PLAN_V3.md` 第 19.2 节）分列。
""", """- **"存量"含在建机组（已被第 180 项取代，见第 2.5 节）。** `existing_survivor` 里有 GEM 状态为 construction 的机组（Luang Prabang、Pak Beng、Pak Lay 等，投运年 2030 前后）。审阅决定说以构建回执的存量标识为准，所以都移入。求解前的容量表（`RUN_PLAN_V3.md` 第 19.2 节）分列。
""")
rep("""- **存量风电同样移入。** `existing_survivor::LA2 1::onwind existing::S4B1`（350 MW）是存量 Generator，按同一判据移入。这是"全部存量发电"的字面结果，它不是电站专线合同的一部分，属下文"非合同存量也可出口"的简化。
""", """- **存量风电同样移入（第 180 项后不再移入：它是在建机组，回到节点）。** `existing_survivor::LA2 1::onwind existing::S4B1`（350 MW）是存量 Generator，按同一判据移入。这是"全部存量发电"的字面结果，它不是电站专线合同的一部分，属下文"非合同存量也可出口"的简化。
""")
rep("""## 3. 第 161 项：国家液体母线与船运
""", """### 2.5 第 180 项：源母线只放运营中机组（补充 05，2026-11-03，筛查前）

**依据：** `V3_REVIEW_DECISIONS_SUPP04.md` 第 2 节；状态判据是用户的决定（`V3_S5_STOP_NOTE.md` 第 4 节，用户 2026-11-03 原话"用 GIPT Status 继续"）。

**理由：** 第 160 项与第 175 (a) 项定的主算口径是"只计运营中，在建作敏感性"。在建机组在现实中多是新的出口电站，各自有新建的送出线和自己的购电合同，并不使用现有电站专线。在建机组连同各自的送出线，一并属于第 175 (a) 项的敏感性。

**规则：**

1. 源母线上只放状态为运营中（operating）的存量机组。在建及其他非运营状态的存量机组回到节点 n，参数不变，仍是两情景相同的存量发电，**发电存量口径不变**。
2. 源链路 `p_nom` 按新的移入合计重算，其余属性同第 2.4 节。
3. **状态判据：** GIPT 2026-09 的 `Status`，按 GEM 机组 ID 查表，表 `research_inputs/corridors/DEDICATED_STOCK_STATUS_V3.csv`（5 个源节点全部 65 台，由 `v3_dedicated_lines.py --status-table` 生成）。审阅决定写的是与状态表用同一字段 `gem_status`；这个字段取自同一列，但回执只给新加的机组写了它，冻结存量 43 台 11,028 MW 是空白的。已有 `gem_status` 的 22 台必须与查表结果一致，不一致构建报错。
4. **构建报错（停止条件）：** 某台机组查不到状态；某节点运营中不含火电容量为 0。低于合同容量的节点只列出，不停。

**混合组件要拆开（审阅决定未写到，实施时发现）：** 机队组件按节点和批次聚合，有 2 个组件同时含运营中和在建机组，只改母线做不到"只放运营中"：

| 组件 | 合计（MW） | 运营中（上源母线） | 在建（留在节点） |
|---|---:|---|---|
| `existing_survivor::LA2 1::hydro existing::S4A` | 564 | Nam Ngum 4 240、Nam Sum 3 156、Nam Ngiep 3A 44，合计 440 | Nam Neun 1 124 |
| `existing_survivor::LA2 5::ror existing::S4A` | 948 | Nam Beng 36 | Pak Beng 912 |

做法（`split_stock_component`）：运营中部分成为新组件 `<原名> operating`，在建部分保留原名。容量、年固定运维费、水库来水按容量份额分，单位化序列（`p_max_pu`）照抄，其余属性相同，所以两部分合起来就是原组件；`existing_unit_components` 里运营中机组的 `component` 改指新组件，`node` 不变。这是规则 1 的直接结果，不改变存量、成本或来水的合计。所以审阅决定第 3 条"差异只应是在建机组的母线与源链路 `p_nom`"之外，多这两组拆分。

**静态检查：** `source_bus_problems` 另核对两点：源母线上每台机组的状态都是运营中；节点上每台运营中机组都在源母线上。`struct_diff` 把拆分的两部分合回一个组件再比较，合不回原值仍不通过。

**记账：** 账本和分摊代码不改。拆出的组件沿用 `country = LA`，年固定运维费之和不变。

## 3. 第 161 项：国家液体母线与船运
""")
rep("""| Bus、Link（第 179 项，2026-11-03） | 增 5 条源母线 `LA2 n dedicated src`（carrier AC，不是地理节点）、5 条 `dedicated plant source` 链路；LA 专线节点的存量 Generator、StorageUnit、燃料 Link 的母线移到源母线（`moved_to_source_bus`），其余属性不变 |
""", """| Bus、Link（第 179 项，2026-11-03） | 增 5 条源母线 `LA2 n dedicated src`（carrier AC，不是地理节点）、5 条 `dedicated plant source` 链路；LA 专线节点的存量 Generator、StorageUnit、燃料 Link 的母线移到源母线（`moved_to_source_bus`），其余属性不变 |
| Generator、StorageUnit（第 180 项，2026-11-03） | 只有运营中机组移到源母线；2 个混合组件拆成 `<原名> operating` 与原名两部分（`split_for_source_bus`），合计不变 |
""")
rep("""按聚类节点而不是按具体合同电站绑定，节点上非合同的存量电站也可经专线出口，是上界；不按购电合同份额限制。（本条按 `V3_REVIEW_DECISIONS_SUPP03.md` 第 2.1 节替换原句，原文见 `V3_LIMITATIONS_ITEM176.md`。）
""", """按聚类节点而不是按具体合同电站绑定，节点上非合同的存量电站也可经专线出口，是上界；不按购电合同份额限制。（本条按 `V3_REVIEW_DECISIONS_SUPP03.md` 第 2.1 节替换原句，原文见 `V3_LIMITATIONS_ITEM176.md`。）只绑定运营中机组；在建机组与其送出线一并属于第 175 (a) 项敏感性。`LA2 1` 的 350 MW 存量风电全年平均 `p_max_pu` 0.009，位置未核实，网络不改。
""")
open(p, "w", encoding="utf-8").write(s)
print("rules patched")
