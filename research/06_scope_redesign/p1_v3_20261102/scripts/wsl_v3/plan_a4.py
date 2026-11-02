"""Supplement 04 section 2.4 items 1, 2: registration before the solve. Section 17.1 keeps its table with a note that it is superseded."""
import json
from pathlib import Path

import pandas as pd
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
d3 = json.loads(Path(D + "batch_def/BATCH_DEF_365x24h.json").read_text(encoding="utf-8")); d2 = json.loads(Path(D + "batch_def/BATCH_DEF_2920x3h.json").read_text(encoding="utf-8"))
sh = {**d3["registered_sha"], **d2["registered_sha"]}; by = {**d3["registered_bytes"], **d2["registered_bytes"]}
rows = "\n".join(f"| `{k}` | {by[k]:,} | `{sh[k]}` |" for k in ("integrated_2920_3h_unsolved.nc", "no_new_xb_2920_3h_unsolved.nc", "integrated_365_24h_unsolved.nc", "no_new_xb_365_24h_unsolved.nc", "disconnected_365_24h_unsolved.nc", "bridge_160_162_365_24h_unsolved.nc", "bridge_160_164_365_24h_unsolved.nc"))
t = pd.read_csv(D + "evidence/SOURCE_CAPACITY_V3.csv"); st = pd.read_csv(D + "evidence/SOURCE_CAPACITY_STATUS_V3.csv")
f = lambda v: f"{v:,.0f}" if v else "—"
cap = "\n".join(f"| `{r.node}` | {f(r.mw_hydro)} | {f(r.mw_ror)} | {f(r.mw_onwind)} | {f(r.mw_coal)} | {f(r.mw_lignite)} | {r.moved_mw:,.0f} | {r.non_thermal_mw:,.0f} | {r.contract_mw:,.0f} | {r.ratio_moved:.2f} | {r.ratio_non_thermal:.2f} |" for r in t.itertuples())
tot = t[["mw_hydro", "mw_ror", "mw_onwind", "mw_coal", "mw_lignite", "moved_mw", "non_thermal_mw", "contract_mw"]].sum()
cap += f"\n| **合计** | **{tot.mw_hydro:,.0f}** | **{tot.mw_ror:,.0f}** | **{tot.mw_onwind:,.0f}** | **{tot.mw_coal:,.0f}** | **{tot.mw_lignite:,.0f}** | **{tot.moved_mw:,.0f}** | **{tot.non_thermal_mw:,.0f}** | **{tot.contract_mw:,.0f}** | **{tot.moved_mw / tot.contract_mw:.2f}** | **{tot.non_thermal_mw / tot.contract_mw:.2f}** |"
sea = "\n".join(f"| `{r.node}` | {r.contract_mw:,.0f} | {r.avail_dry_week_mw:,.0f} | {r.avail_jan_mw:,.0f} | {r.avail_sep_mw:,.0f} | {r.avail_year_mw:,.0f} | {r.ratio_dry_week:.2f} | {r.ratio_year:.2f} |" for r in t.itertuples())
a = t[["contract_mw", "avail_dry_week_mw", "avail_jan_mw", "avail_sep_mw", "avail_year_mw"]].sum()
sea += f"\n| **合计** | **{a.contract_mw:,.0f}** | **{a.avail_dry_week_mw:,.0f}** | **{a.avail_jan_mw:,.0f}** | **{a.avail_sep_mw:,.0f}** | **{a.avail_year_mw:,.0f}** | **{a.avail_dry_week_mw / a.contract_mw:.2f}** | **{a.avail_year_mw / a.contract_mw:.2f}** |"
c = st[st.gem_status == "construction"]; cn = c.groupby(["node", "carrier"]).mw.sum().unstack().fillna(0.0)
con = "\n".join(f"| `{r.node}` | {r.carrier} | {r.mw:,.0f} | {r.years} |" for r in c.itertuples()); ct = float(c.mw.sum())
p = D + "RUN_PLAN_V3.md"; s = open(p, encoding="utf-8", newline="").read()
a_ = "### 17.1 单向专线后的网络\n\n"
b_ = "### 17.1 单向专线后的网络\n\n**已被第 179 项取代：** 本节的 SHA256 和 LP 规模是专线接在节点上的版本，现行登记见第 19.1 节。\n\n"
assert s.count(a_) == 1; s = s.replace(a_, b_); assert "## 19." not in s
s = s.rstrip("\n") + f"""

## 19. 补充 04 登记（求解前）

依据 `V3_REVIEW_DECISIONS_SUPP03.md` 第 2 节（决策清单第 179 项）。第 3、4、5、10、11、15、17 节的原有内容不改（第 17.1 节只加了取代标注）。

### 19.1 第 179 项后的网络

构建提交 `{d3['build_commit']}`，输出 `results_project/v3/builds_bound`。规则见 `V3_RULES.md` 第 2.4 节。静态检查 `all_structural_passed = true`，含新增的 `plant_sources`（5 条源链路，合计 {tot.moved_mw:,.0f} MW）。

| 文件 | 字节 | SHA256 |
|---|---:|---|
{rows}

完全隔离网络没有专线，与上一版逐字节相同（SHA256 不变）。

| LP | 列 | 行 | 非零 |
|---|---:|---:|---:|
| 一体化，56 时段 | 728,876 | 1,602,876 | 3,714,882 |
| `no_new_xb`，56 时段 | 707,522 | 1,555,294 | 3,564,648 |
| 一体化，365×24h | 4,692,419 | 10,377,240 | 24,241,312 |
| `no_new_xb`，365×24h | 4,555,190 | 10,070,098 | 23,265,739 |
| 完全隔离，365×24h | 4,536,210 | 10,021,188 | 23,146,749 |
| 修订桥 160–164，365×24h | 4,622,435 | 10,272,216 | 24,066,208 |
| 修订桥 160–162，365×24h | 4,701,474 | 10,480,465 | 24,456,957 |

相对第 17.1 节：每个时段多 5 列、15 行（5 条源链路及其上下界、5 个节点平衡），56 时段 +280 列、+840 行，365×24h +1,825 列、+5,475 行。

### 19.2 容量表（审阅决定第 2.3 节，`evidence/SOURCE_CAPACITY_V3.csv`）

**没有移入容量为 0 的节点，不触发停止条件。**

**(a) 移入的存量（MW，出力口径；燃料 Link 按 `p_nom × efficiency`）**

| 源节点 | 水库水电 | 径流 | 风电 | 煤电 | 褐煤 | 移入合计 | 不含火电 | 专线合同 | 合计 / 合同 | 不含火电 / 合同 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{cap}

**(b) 2050 年净零约束下可运行的部分。** 按排放分两类：水电、径流、风电不受排放约束，上表"不含火电"一列全部可运行。火电 {tot.mw_coal + tot.mw_lignite:,.0f} MW（`LA2 5` Hongsa 褐煤 1,878 MW，`LA2 4` 煤电 300 MW）在国家净零约束下基本不能运行：补充 03 冒烟（单向网络，枯水周，只作参考）里，一体化两台都是 0；`no_new_xb` 里 Hongsa 平均 33.5 MW（只有一个时段满发），煤电平均 5.4 MW。所以 `LA2 5` 的合同容量 1,473 MW 名义上正是 Hongsa，实际只能由该节点水电承担。

**按铭牌：** 不含火电的存量都不低于专线合同容量，最低是 `LA2 3`（1.28 倍）。**没有铭牌不足的节点。**

**(c) 按来水的可用出力（MW）。** 铭牌掩盖了季节性，所以另列：径流 `p_nom × p_max_pu`，水库 `min(来水, p_nom)`，风电 `p_nom × p_max_pu`，不含火电。库容约 7 小时，调节不了季节。

| 源节点 | 专线合同 | 枯水周（56 时段） | 1 月 | 9 月 | 全年平均 | 枯水周 / 合同 | 全年 / 合同 |
|---|---:|---:|---:|---:|---:|---:|---:|
{sea}

**按来水，可用出力低于专线容量的节点：** 枯水周 5 个节点全部低于（合计只有合同的 {a.avail_dry_week_mw / a.contract_mw * 100:.0f} %）；全年平均 `LA2 1`、`LA2 3`、`LA2 4`、`LA2 5` 低于，只有 `LA2 2` 略高。也就是说第 179 项之后，专线全年大部分时间是不满载的，满载只在雨季。这一点对预测最重要。

**(d) "存量"含在建机组（`evidence/SOURCE_CAPACITY_STATUS_V3.csv`）。** 审阅决定说以构建回执的存量标识为准，都移入。GEM 状态为 construction 的合计 {ct:,.0f} MW，占移入的 {ct / tot.moved_mw * 100:.0f} %，投运年都在 2026 年以后：

| 源节点 | 载体 | MW | 投运年 |
|---|---|---:|---|
{con}

水电追踪表（Hydropower Tracker）来的机组没有 GIPT 状态字段，上表只含带 construction 标记的；`LA2 5` 的 Hongsa 来自煤电追踪表，投运 2015–2016 年。

### 19.3 运行与验收

脚本 `/home/jin/v3/smoke_s4.sh`，输出 `results_project/v3/smoke_s4`。档案 `formal_barrier_1e6_t16`，前 56 时段，TimeLimit 3,000 s，墙钟止损 3,600 s，串行，间隔 ≥ 330 s，不重试、不改参数。额度 2 次：一体化、`no_new_xb`。

用户在任务执行中两次明确答复（2026-11-03），原话："wsl可用无需再次询问"、"AnyConnect未连接冒烟直接进行"。所以按用户指示不再停下询问；`smoke_s4.sh` 在启动前和每次求解前仍做到令牌服务器的 TCP 预检，不通就不启动。

验收同第 15.3 节：C1 (a)(b)(c) 全过且 GATES_V6 ACCEPTED，B16，B6 为正，SG 有来源，无松弛。另加审阅决定第 3 节的停止条件：记账不闭合或新 Link 被计为跨境；冒烟不可行或 C1 不过。闸门预告用并集规则：A1_A2、A1_A2_S4B、A3、A3_S4B、B1、B3、B8，B8 只有 Transport，相对差 −4.1146e-05。

### 19.4 56 时段预测（INFERENCE，以第 18 节单向结果为基线；这一周是枯水期）

参考了补充 03 冒烟（`V3_REPORT_SUPPLEMENT03.md` 第 3 节）和第 19.2 节的来水，不是独立于冒烟的预测。已登记的第 5、11、15、17 节预测不改。

结构上的界（不是预测）：第 179 项是单向网络的收紧，又比无专线网络宽松（无专线的解在新网络可行，只多专线 FOM 0.0159 bn）。所以一体化 329.1463–329.2134 bn，`no_new_xb` 341.6165–341.9234 bn。

| 项 | 预测 | 依据 |
|---|---|---|
| `no_new_xb` 的 LA 净出口 | 从 +17.42 降到 +6 到 +13 TWh | 枯水周存量可用出力只有 1,343 MW（年化 11.8 TWh），专线流量不能再超过它；补充 03 的专线流量 17.07 TWh。部分时段存量留在 LA 本地更划算；APG 线路可多出口 1–3 TWh |
| `no_new_xb` 的专线合计流量 | 6–12 TWh，LA–VN 明显低于 3.39 TWh | 同上；`LA2 4` 的两条专线共用 329 MW 的存量 |
| `no_new_xb` 的 LA 新建风光 | 陆风加光伏发电 42–50 TWh（单向 54.6，无专线 35.8）；容量 18–24 GW（单向 25.9，无专线 18.7） | 新建机组不再能上专线，但替换了改为出口的存量，所以不会回到无专线水平 |
| `no_new_xb` 总成本 | 上升 0.05–0.13 bn | 补充 03 相对无专线省 0.29 bn 对应净出口 +16.9 TWh；收益随出口递减 |
| 一体化总成本 | 上升不超过 0.03 bn | 补充 03 里专线合计 11.58 TWh，只有 `LA2 1` 明显超过存量；新建走廊可以替代 |
| B6 | 12.48–12.65 bn（单向 12.47，无专线 12.71） | 以上两项之差 |
| LA 受益 | 上升，−0.12 到 +0.03 bn（单向 −0.138，无专线 +0.041） | 对照情景里 LA 经专线卖的电变少 |
| TH 受益 | 基本不变，4.03–4.10 bn（单向 4.057） | 补充 03 里 TH 的受益在无专线和单向之间几乎不动，这一周不能外推 |
| LA 水电出力 | 不变：径流 4.9、水库 6.2 TWh | 枯水周来水全部用上 |
| Hongsa | 年化出力 < 1 TWh | 净零约束，见第 19.2 节 (b) |

### 19.5 第 179 项后的 365×24h 预测（筛查前登记）

参考了补充 03 冒烟和第 19.2 节的逐月来水，不是独立于冒烟的预测。第 11、15.5、17.4 节的原有预测不改。**365×24h 没有第 179 项之前的 v3 运行，"相对第 17.4 节"只能比区间，不能比数值。**

结构上的上界（VERIFIED，`evidence/SOURCE_LINE_BOUND_V3.json`）：5 个源节点存量可用出力全年 37.3–37.6 TWh，逐时段与各节点专线合同取小后，专线全年最多送 **26.0–26.2 TWh**（不含火电），即**年均利用率上界约 50 %**。逐月上界：1–4 月 600–940 MW（不超过 16 %），8–9 月 5,880–5,910 MW（约 98 %）。LA 全年负荷 36.8 TWh。

| 项 | 预测 | 依据 |
|---|---|---|
| `no_new_xb` 的 LA 净出口 | +15 到 +30 TWh | 专线 26 TWh 为上界，部分存量留在本地；APG 线路另有净出口 |
| 专线利用率 | 全年平均 30–48 %（第 17.4 节 40–70 %），8–9 月接近满载，1–4 月不超过 16 % | 第 179 项后专线只有存量可送，全年平均不可能超过约 50 %；火电基本不运行 |
| B6 = V2 − V1 | 为正，9.6–13.8 bn；相对第 17.4 节区间上移不超过 0.4 bn | 雨季专线本来就被水电占满，第 179 项不绑定；影响集中在其余约 9 个月 |
| LA 受益 | 低于 v2 筛查的 +1.229 bn，−0.3 到 +0.8 bn；相对第 17.4 节上移 | 对照情景里 LA 经专线的出口变少 |
| TH 受益 | 0.6–2.6 bn，低于无专线情形（v2 筛查 +1.769 bn，不可直接比） | TH 仍能在雨季买到老挝水电，枯水期买不到新建风光 |
| V3 − V2（存量与专线的价值） | 为正，1.2–5.2 bn；相对第 17.4 节下移不超过 0.4 bn | `no_new_xb` 成本上升，完全隔离不变 |

第 15.5 节中"相对 X1b 前"那一项仍**无法直接检验**，筛查报告如实说明。
"""
open(p, "w", encoding="utf-8", newline="").write(s)
print("plan ok", tot.to_dict())
