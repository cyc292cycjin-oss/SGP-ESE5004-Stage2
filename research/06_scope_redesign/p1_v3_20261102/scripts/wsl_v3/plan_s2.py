"""Supplement 02, section 2.2: X1b rule in V3_RULES.md, registration in RUN_PLAN_V3.md (sections 3, 4, 5, 10, 11 untouched), before any solve."""
import json
from pathlib import Path
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_x1b")
d3 = json.loads(Path(D + "batch_def/BATCH_DEF_365x24h.json").read_text(encoding="utf-8")); d2 = json.loads(Path(D + "batch_def/BATCH_DEF_2920x3h.json").read_text(encoding="utf-8"))
sh = {**d3["registered_sha"], **d2["registered_sha"]}; by = {**d3["registered_bytes"], **d2["registered_bytes"]}
rows = "\n".join(f"| `{k}` | {by[k]:,} | `{sh[k]}` |" for k in ("integrated_2920_3h_unsolved.nc", "no_new_xb_2920_3h_unsolved.nc", "integrated_365_24h_unsolved.nc", "no_new_xb_365_24h_unsolved.nc", "disconnected_365_24h_unsolved.nc", "bridge_160_162_365_24h_unsolved.nc", "bridge_160_164_365_24h_unsolved.nc"))
p = D + "V3_RULES.md"; s = open(p, encoding="utf-8", newline="").read()
a = "## 3. 第 161 项：国家液体母线与船运\n"
b = """### 2.3 X1b 规则（第 172、173 项，B 级；补充 02 实施）

**来源：** LA–TH 为 EPPO「Power purchased from Laos PDR」（页面日期 2016-03-29，存档快照 2026-06-11，SHA256 `680ed575…`），9 个项目、合同容量 5,427 MW；LA–VN 为 GEM 的 Xekaman 1、3，合计 572 MW（第 100 项已引用）。表 `research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv`，脚本 `scripts_project/v3_dedicated_lines.py`。

**只计运营中：** 逐项核对 GEM GIPT 2026-09 的状态和网络的存量机组（`existing_unit_components`）。11 项全部 `operating`、全部在网络中，全部计入。EPPO 表是 2016 年状态，当时未投运的 Hongsa、Xayaburi、Xe Pian-Xe Namnoy、Nam Ngiep 1 在 GEM 中已投运（2015–2019）。

**与 APG 不重复：** ACE 2024 项目档案第 9 章（第 21–23 页）列出的现有线路是七条 115 kV、协议类型 Energy Exchange 的线路，容量合计正好 955 MW（`research_inputs/corridors/APG_LA_TH_LINES_ACE2024.csv`）。同章另述"约 5,934.9 MW 发电并网（generation-to-grid）互联"，与这 955 MW 分列。所以 APG 的 955 MW 不含电站专线，不用扣除。

**建模：**

- 按"电站所在 LA 节点 + 着陆节点"合并（审阅决定允许），得 6 条专线，每条一对 forward / `-reversed` Link，双向，不可扩建，`p_nom` = 合同容量之和。
- 着陆节点取距电站节点最近的 TH（或 VN）节点，长度 = 大圆距离 × 1.25（与模型线路同口径）。
- 效率 = 1 − λ × 长度，λ 按第 108 项线损代理的 380 kV 4-bundle 线型、α 0.5 计算，每 km 1.2348e-4。
- `border_class=cross_border`，`transport_carrier=electricity`，`stock=dedicated_plant_line`，`p_nom_min = p_nom`。`apply_stock_mode` 因此把它们当存量保留。
- 一体化、`no_new_xb` 及完全隔离之外的所有情景相同。完全隔离网络不加。
- 存量 FOM 规则照常适用：HVAC overhead 的 FOM% × 投资 × 长度 × 容量，6 条合计 15.87 M EUR/a，两情景相同，不影响 B6，计入完全隔离 − `no_new_xb`。

| 专线 | 项目 | MW | km | 效率 |
|---|---|---:|---:|---:|
| LA2 1 – TH2 4 | Xayaburi | 1,220 | 400.5 | 0.9506 |
| LA2 2 – TH2 1 | Nam Ngum 2、Nam Ngiep 1 | 866 | 351.9 | 0.9565 |
| LA2 3 – TH2 1 | Theun-Hinboun、扩建、Nam Theun 2 | 1,388 | 278.7 | 0.9656 |
| LA2 4 – TH2 1 | Houayho、Xe Pian-Xe Namnoy | 480 | 373.9 | 0.9538 |
| LA2 5 – TH2 4 | Hongsa | 1,473 | 444.0 | 0.9452 |
| LA2 4 – VN2 2 | Xekaman 1、3 | 572 | 230.9 | 0.9715 |

**简化（写入局限）：** 专线不绑定电站，可双向，也可供节点上其他机组使用；合同容量低于或等于电站容量；着陆节点按最近节点取，不是实际落点（如 Xayaburi 实际走向 TH 东北部）；线损用代理线型，不是实际 230 / 500 kV 线路；专线损耗全部计在受端，线路代理是两端各半。

**对照（不是来源）：** ACE 的 5,934.9 MW 比 EPPO 的 5,427 MW 高 507.9 MW，审阅决定以 EPPO 为唯一来源，这一差额未计入。

## 3. 第 161 项：国家液体母线与船运
"""
assert s.count(a) == 1; s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s)
p = D + "RUN_PLAN_V3.md"; s = open(p, encoding="utf-8", newline="").read()
assert "## 15." not in s
s = s.rstrip("\n") + f"""

## 15. 补充 02 登记（求解前）

依据 `V3_REVIEW_DECISIONS_SUPP01.md`。第 3、4、5、10、11 节的原有内容不改，本节是补充。

### 15.1 X1b 后的网络

构建提交 `{d3['build_commit']}`，输出 `results_project/v3/builds_x1b`。

| 文件 | 字节 | SHA256 |
|---|---:|---|
{rows}

修订桥两个网络由一体化构建加覆盖项得到：160–164 = `s2.demand.ev_structure=flat`；160–162 = 再加 `s2.industry.v3={{}}`。三者都含 X1b。差异表 `evidence/BRIDGE_DIFF_V3.csv`：v3 对 160–164 只有 EV 层；160–164 对 160–162 只有工业与过程载体。需求总量 7,621.451 / 7,621.451 / 7,628.637 TWh，后者等于 v2。

| LP | 列 | 行 | 非零 |
|---|---:|---:|---:|
| 一体化，56 时段 | 728,932 | 1,602,708 | 3,715,106 |
| `no_new_xb`，56 时段 | 707,578 | 1,555,126 | 3,564,872 |
| 一体化，365×24h | 4,692,784 | 10,376,145 | 24,242,772 |
| `no_new_xb`，365×24h | 4,555,555 | 10,069,003 | 23,267,199 |
| 完全隔离，365×24h | 4,536,210 | 10,021,188 | 23,146,749 |
| 修订桥 160–164，365×24h | 4,622,800 | 10,271,121 | 24,067,668 |
| 修订桥 160–162，365×24h | 4,701,839 | 10,479,370 | 24,458,417 |

存量表 `evidence/X1_STOCK_TABLE_V3.csv`：APG 2,870 MW + 专线 5,999 MW。LA 出口可用容量 `evidence/LA_EXPORT_USABLE_V3.csv`：

| 国家对 | APG 可用（MW） | 专线（MW） | 合计（MW） |
|---|---:|---:|---:|
| LA–TH | 668.5 | 5,427 | 6,095.5 |
| LA–VN | 0 | 572 | 572 |
| KH–LA | 210 | 0 | 210 |
| LA–MM | 21 | 0 | 21 |
| **合计** | **899.5** | **5,999** | **6,898.5** |

### 15.2 运行清单

脚本 `/home/jin/v3/smoke_s2.sh`，输出 `results_project/v3/smoke_s2`。档案 `formal_barrier_1e6_t16`，前 56 时段，TimeLimit 3,000 s，墙钟止损 3,600 s，串行，间隔 ≥ 330 s，不重试、不改参数。额度 2 次：一体化 E2、`no_new_xb` E2。调用前须用户确认 WLS 会话空闲、AnyConnect 已断开。

### 15.3 验收与闸门预告

验收同第 10.3 节：C1 (a)(b)(c) 全过且 GATES_V6 ACCEPTED，B16，B6 为正，SG 有来源，无松弛。

**今后的预告规则（审阅决定）：** 换档案或换网络后，预告取历次同类运行中出现过的全部失败闸门的并集。

- **56 时段（本补充）：** A1_A2、A1_A2_S4B、A3、A3_S4B、B1、B3、B8。来源：v2 冒烟、v3 第二轮（档案 A）、补充 01 四次。B8 只在 E2 下出现，只有 Transport，相对差 −4.1146e-05，这个值不应改变，改变则另行报告。
- **365×24h（筛查）：** A1_A2、A1_A2_S4B、A3、A3_S4B、B1、B2、B3、B3_S4B、B15。来源：DFX V1、V2。B8 是截短假象，全年网络预期通过；若 E2 的全年网络不通过，另行报告。
- 以上都是数值信息，不进验收（决定 4）。

### 15.4 56 时段预测（INFERENCE，以补充 01 第一次运行为基线）

| 项 | 预测 | 依据 |
|---|---|---|
| B6 | 下降 1–5 bn，仍为正（X1b 前 12.71 bn） | `no_new_xb` 的 LA 出口从 900 MW 增到 6,899 MW，X1b 前 LA–TH 走廊饱和，影子价格 531 EUR/MWh |
| `no_new_xb` 总成本 | 下降 1–5 bn | 同上 |
| 一体化总成本 | 变化绝对值 < 0.5 bn | 一体化本来就扩建，专线只省下部分线路投资，6 GW × 约 350 km 约 0.1 bn/a |
| LA 受益 | 下降，可能转负，−1.0 到 +0.04 bn | 对照情景里 LA 已能大量出口 |
| TH 受益 | 下降 0.5–3 bn | 对照情景里 TH 也能买到老挝电 |
| 液体、EV | 基本不变 | X1b 不直接涉及 |

### 15.5 365×24h 补充预测（X1b 之后，筛查前登记）

参考了补充 01 的冒烟，不是独立于冒烟的预测。第 5、11 节的原有预测不改。

| 项 | 预测 | 依据 |
|---|---|---|
| B6 = V2 − V1 | 为正；相对 X1b 前下降 1–4 bn，绝对值 9–13 bn | 同第 15.4 节；365×24h 没有 X1b 前的 v3 运行，这个"下降"只能由冒烟前后之差和 v2 的 14.6153 bn 间接判断 |
| LA 受益 | 低于 v2 筛查的 +1.229 bn，−0.5 到 +0.6 bn | 专线进入对照情景 |
| TH 受益 | 下降，0.5–2.5 bn（v2 筛查 +1.769 bn） | 同上 |
| V3 − V2（存量与专线的价值） | 为正，2–6 bn | v1 只算电力存量约 0.6 bn；LA 出口增加 6 GW，再加气管存量 |
| V5 − V1（EV 效应，365×24h） | 绝对值 < 2 bn | `to_daily` 基本抹掉日内形状，冒烟的 10 bn 不会出现 |

### 15.6 2920×3h 之后的 EV 敏感性计划（审阅决定，另行授权）

2920×3h 正式运行之后另做两个敏感性：flat（`s2.demand.ev_structure=flat`）、车队代理 ×0.5（`s2.demand.ev_fleet_scale=0.5`）。筛查看不到 E2 的日内效应，所以放在正式运行之后。东盟两三轮车占比高、车队代理偏大，列入第 176 项局限，并按第 175 (b) 项请师哥判断。

`no_new_xb` E2 在两种档案下都是 suboptimal，风险写入 2920×3h 运行计划，按 C1 与 GATES_V6 判定，不调参数。
"""
open(p, "w", encoding="utf-8", newline="").write(s); print("ok")
