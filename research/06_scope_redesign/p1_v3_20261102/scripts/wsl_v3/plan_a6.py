"""Supplement 05 section 2 items 2-4: registration before the solve. Section 19 keeps its tables with a note that they are superseded."""
import json
from pathlib import Path

import pandas as pd
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
d3 = json.loads(Path(D + "batch_def/BATCH_DEF_365x24h.json").read_text(encoding="utf-8")); d2 = json.loads(Path(D + "batch_def/BATCH_DEF_2920x3h.json").read_text(encoding="utf-8"))
sh = {**d3["registered_sha"], **d2["registered_sha"]}; by = {**d3["registered_bytes"], **d2["registered_bytes"]}
rows = "\n".join(f"| `{k}` | {by[k]:,} | `{sh[k]}` |" for k in ("integrated_2920_3h_unsolved.nc", "no_new_xb_2920_3h_unsolved.nc", "integrated_365_24h_unsolved.nc", "no_new_xb_365_24h_unsolved.nc", "disconnected_365_24h_unsolved.nc", "bridge_160_162_365_24h_unsolved.nc", "bridge_160_164_365_24h_unsolved.nc"))
t = pd.read_csv(D + "evidence/SOURCE_CAPACITY_OP_V3.csv"); j = json.loads(Path(D + "evidence/SOURCE_LINE_BOUND_OP_V3.json").read_text()); c = pd.read_csv(D + "evidence/SOURCE_CAPACITY_OP_V3.csv")
f = lambda v: f"{v:,.0f}" if v else "—"
cap = "\n".join(f"| `{r.node}` | {f(r.mw_hydro)} | {f(r.mw_ror)} | {f(r.mw_lignite)} | {r.moved_mw:,.0f} | {r.non_thermal_mw:,.0f} | {r.contract_mw:,.0f} | {r.ratio_non_thermal:.2f} | {r.avail_dry_week_mw:,.0f} | {r.avail_year_mw:,.0f} | {r.avail_sep_mw:,.0f} | {r.ratio_dry_week:.2f} | {r.ratio_year:.2f} |" for r in t.itertuples())
s_ = t[["mw_hydro", "mw_ror", "mw_lignite", "moved_mw", "non_thermal_mw", "contract_mw", "avail_dry_week_mw", "avail_year_mw", "avail_sep_mw"]].sum()
cap += f"\n| **合计** | **{s_.mw_hydro:,.0f}** | **{s_.mw_ror:,.0f}** | **{s_.mw_lignite:,.0f}** | **{s_.moved_mw:,.0f}** | **{s_.non_thermal_mw:,.0f}** | **{s_.contract_mw:,.0f}** | **{s_.non_thermal_mw / s_.contract_mw:.2f}** | **{s_.avail_dry_week_mw:,.0f}** | **{s_.avail_year_mw:,.0f}** | **{s_.avail_sep_mw:,.0f}** | **{s_.avail_dry_week_mw / s_.contract_mw:.2f}** | **{s_.avail_year_mw / s_.contract_mw:.2f}** |"
b3, b1 = j["2920x3h"], j["365x24h"]
p = D + "RUN_PLAN_V3.md"; s = open(p, encoding="utf-8", newline="").read()
a_ = "### 19.1 第 179 项后的网络\n\n"
b_ = "### 19.1 第 179 项后的网络\n\n**已被第 180 项取代：** 第 19.1、19.2 节的 SHA256、规模和容量表是在建机组也在源母线上的版本，现行登记见第 21 节。\n\n"
assert s.count(a_) == 1; s = s.replace(a_, b_); assert "## 21." not in s
s = s.rstrip("\n") + f"""

## 21. 补充 05 登记（求解前）

依据 `V3_REVIEW_DECISIONS_SUPP04.md` 第 2 节（决策清单第 180 项）和 `V3_S5_STOP_NOTE.md`。第 3、4、5、10、11、15、17、19 节的原有内容不改（第 19.1 节只加了取代标注）。

### 21.1 第 180 项后的网络

构建提交 `{d3['build_commit']}`，输出 `results_project/v3/builds_op`。规则见 `V3_RULES.md` 第 2.5 节。静态检查 `all_structural_passed = true`，`plant_sources` 5 条源链路合计 {s_.moved_mw:,.0f} MW。

| 文件 | 字节 | SHA256 |
|---|---:|---|
{rows}

完全隔离网络没有专线，与上一版逐字节相同（SHA256 不变）。

| LP | 列 | 行 | 非零 |
|---|---:|---:|---:|
| 一体化，56 时段 | 729,156 | 1,603,380 | 3,715,722 |
| `no_new_xb`，56 时段 | 707,802 | 1,555,798 | 3,565,488 |
| 一体化，365×24h | 4,694,244 | 10,380,525 | 24,246,787 |
| `no_new_xb`，365×24h | 4,557,015 | 10,073,383 | 23,271,214 |
| 完全隔离，365×24h | 4,536,210 | 10,021,188 | 23,146,749 |
| 修订桥 160–164，365×24h | 4,624,260 | 10,275,501 | 24,071,683 |
| 修订桥 160–162，365×24h | 4,703,299 | 10,483,750 | 24,462,432 |

相对第 19.1 节：每个时段多 5 列、9 行，来自 2 个拆分组件（56 时段 +280 列、+504 行，365×24h +1,825 列、+3,285 行）。

**逐组件比较（`evidence/OP_VS_BOUND_DIFF.json`，四个网络都通过，按位比较）：** 差异只有：回到节点的 6 台 Generator、5 台 StorageUnit、1 条煤电 Link 的母线；5 条源链路的容量；2 个拆分组件。拆分的两部分合计容量、年固定运维费、来水都等于原组件，`p_max_pu` 相同。机组标识集合不变，两个目标函数常数不变。审阅决定预期差异只有前两类，第三类是混合组件的直接结果，见 `V3_RULES.md` 第 2.5 节。

### 21.2 容量表（`evidence/SOURCE_CAPACITY_OP_V3.csv`，只含运营中）

**没有运营中不含火电容量为 0 的节点，不触发停止条件。** 单位 MW，出力口径；可用出力不含火电，口径同第 19.2 节 (c)。

| 源节点 | 水库 | 径流 | 褐煤 | 移入合计 | 不含火电 | 专线合同 | 不含火电 / 合同 | 枯水周可用 | 全年平均可用 | 9 月可用 | 枯水周 / 合同 | 全年 / 合同 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{cap}

**低于合同容量的节点（列出，不停）：**

- 按铭牌（不含火电）：没有。但 `LA2 5` 是 1,476 MW 对 1,473 MW，只高 3 MW；`LA2 3` 是 1.13 倍。
- 按来水：枯水周、全年平均 5 个节点全部低于；9 月 `LA2 3`（1,241 MW 对 1,388 MW）、`LA2 5`（1,242 MW 对 1,473 MW）低于。

`LA2 5`（审阅决定要求重新给出）：移入 3,354 MW，其中 Hongsa 1,878 MW，水库 1,440 MW（Nam Ou 梯级、Nam Tha），径流 36 MW（Nam Beng）。Luang Prabang 1,460 MW、Pak Beng 912 MW 回到节点。这条 1,473 MW 专线现在由 Hongsa 和运营中的水电使用；不含火电的 1,476 MW 全部是非合同电站。

**专线全年可送电量的结构上界（`evidence/SOURCE_LINE_BOUND_OP_V3.json`，不含火电）：** 存量可用出力全年 {b3['stock_twh']:.1f}–{b1['stock_twh']:.1f} TWh，逐时段与合同取小后 **{b3['line_bound_twh']:.1f}–{b1['line_bound_twh']:.1f} TWh，年均利用率 {b3['line_bound_share_of_contract'] * 100:.1f}–{b1['line_bound_share_of_contract'] * 100:.1f} %**（第 19.5 节为 26.0–26.2 TWh、约 50 %）。逐月上界：1–4 月 386–604 MW（不超过 10 %），8–9 月约 5,550–5,620 MW（约 93 %）。

### 21.3 运行与验收

脚本 `/home/jin/v3/smoke_s5.sh`，输出 `results_project/v3/smoke_s5`。档案 `formal_barrier_1e6_t16`，前 56 时段，TimeLimit 3,000 s，墙钟止损 3,600 s，串行，间隔 ≥ 330 s，不重试、不改参数。额度 2 次：一体化、`no_new_xb`。

审阅决定第 2 节第 5 条：用户已在本会话中给出明确答复的，按原话执行并记入运行计划。用户原话（2026-11-03）："wsl可用无需再次询问"、"AnyConnect未连接冒烟直接进行"。`smoke_s5.sh` 在启动前和每次求解前仍做到令牌服务器的 TCP 预检，不通就不启动。

验收同第 15.3 节：C1 (a)(b)(c) 全过且 GATES_V6 ACCEPTED，B16，B6 为正，SG 有来源，无松弛。另加审阅决定第 3 节的停止条件：记账不闭合；冒烟不可行或 C1 不过。闸门预告用并集规则：A1_A2、A1_A2_S4B、A3、A3_S4B、B1、B3、B8，B8 只有 Transport，相对差 −4.1146e-05。

### 21.4 第 180 项后的 56 时段预测（INFERENCE，以第 20 节结果为基线；这一周是枯水期）

参考了补充 04 冒烟（`V3_REPORT_SUPPLEMENT04.md` 第 5 节）和第 21.2 节的来水，不是独立于冒烟的预测。已登记的第 5、11、15、17、19 节预测不改。

结构上的界（不是预测）：第 180 项是补充 04 网络的收紧，又比无专线网络宽松。所以一体化 329.1921–329.2134 bn，`no_new_xb` 341.7188–341.9234 bn。枯水周专线可用的存量上限 871 MW，年化 7.6 TWh（不含火电）。

| 项 | 预测 | 依据 |
|---|---|---|
| `no_new_xb` 的 LA 净出口 | 下降，+5.5 到 +8.5 TWh（补充 04 +7.76） | 专线上限从 11.8 降到 7.6 TWh；补充 04 的专线流量 7.25 TWh 已接近新上限。在建水电留在节点供 LA 本地，运营中机组更多上专线，APG 线路可略增 |
| `no_new_xb` 的专线合计流量 | 5.0–7.8 TWh（补充 04 7.25） | 补充 04 的流量逐时段有 2.26 TWh 超过运营中可用出力，超出部分去掉后是 4.99 TWh，这是下端；另一端是上限 7.6 TWh 加少量火电（`s5_pred.py`） |
| `no_new_xb` 总成本 | 上升 0–0.06 bn | 少出口 0–2 TWh，低出口段每 TWh 约值 0.03 bn（0.2046 bn / 7.25 TWh） |
| 一体化总成本 | 上升不超过 0.02 bn | 结构界只留 0.0213 bn。这次按逐时段看：补充 04 一体化的 3.61 TWh 里有 1.10 TWh 超过运营中可用出力，`LA2 1`、`LA2 4`、`LA2 5` 的峰值都高于新上限，所以不是 0 |
| B6 | 12.50–12.59 bn（补充 04 12.53） | 以上两项之差 |
| LA 受益 | 上升或基本不变，−0.13 到 −0.05 bn（补充 04 −0.123） | 对照情景里 LA 经专线卖的电不多于补充 04；吸取补充 04 的教训，下限留有余量 |
| TH 受益 | 基本不变，4.03–4.10 bn（补充 04 4.061） | 这一周 TH 的受益对专线几乎不敏感，不外推 |
| LA 水电出力 | 不变：径流 4.9、水库 6.2 TWh | 枯水周来水全部用上 |

### 21.5 第 180 项后的 365×24h 预测（筛查前登记）

参考了补充 04 冒烟和第 21.2 节的逐月来水，不是独立于冒烟的预测。第 11、15.5、17.4、19.5 节的原有预测不改。**365×24h 没有第 179、180 项之前的 v3 运行，"相对第 19.5 节"只能比区间，不能比数值。**

| 项 | 预测 | 依据 |
|---|---|---|
| `no_new_xb` 的 LA 净出口 | +12 到 +26 TWh（第 19.5 节 +15 到 +30） | 专线上界 {b1['line_bound_twh']:.1f} TWh，部分存量留在本地；在建水电只能经 APG 线路（可用约 900 MW）出口 |
| 专线合计流量 | 15–20 TWh；全年平均利用率 28–38 %，8–9 月接近 93 % 的上界，1–4 月不超过 10 % | 上界 {b1['line_bound_share_of_contract'] * 100:.0f} %，火电基本不运行；旱季专线只有运营中机组的来水 |
| B6 = V2 − V1 | 为正，9.7–14.0 bn；相对第 19.5 节区间上移不超过 0.4 bn | 雨季专线仍由运营中水电基本占满，收紧主要在 6–7、10–11 月和旱季，专线上界少 5.3 TWh |
| LA 受益 | 低于 v2 筛查的 +1.229 bn，−0.2 到 +0.9 bn；相对第 19.5 节上移 | 对照情景里 LA 经专线的出口变少 |
| TH 受益 | 0.7–2.7 bn，相对第 19.5 节上移（v2 筛查 +1.769 bn，不可直接比） | TH 在对照情景里买到的老挝电变少，互联的价值变大 |
| V3 − V2（存量与专线的价值） | 为正，1.0–5.0 bn；相对第 19.5 节下移不超过 0.4 bn | `no_new_xb` 成本上升，完全隔离不变 |

第 15.5 节中"相对 X1b 前"那一项仍**无法直接检验**，第 17.4 节的利用率按审阅决定以第 19.5 节的读法写明，第 180 项后的上界改为本节的约 40 %。筛查报告如实说明。
"""
open(p, "w", encoding="utf-8", newline="").write(s)


def patch(f, pairs):
    p = D + f; x = open(p, encoding="utf-8", newline="").read()
    for a, b in pairs:
        assert x.count(a) == 1, a[:70]
        x = x.replace(a, b)
    open(p, "w", encoding="utf-8", newline="").write(x)


patch("RUN_PLAN_SCREEN_V3.md", [
    ("网络登记见 `RUN_PLAN_V3.md` 第 19.1 节，预测见第 11、15.5、17.4、19.5 节。", "网络登记见 `RUN_PLAN_V3.md` 第 21.1 节，预测见第 11、15.5、17.4、19.5、21.5 节。"),
    ("全部含 X1b，专线为单向（补充 03），只输送存量电站出力（补充 04，第 179 项）。", "全部含 X1b，专线为单向（补充 03），只输送运营中存量电站的出力（补充 04、05，第 179、180 项）。"),
    ("v3 一体化 LP 比 v2 大 4.0 %（10,377,240 对 9,975,377 行）。", "v3 一体化 LP 比 v2 大 4.1 %（10,380,525 对 9,975,377 行）。"),
    ("干跑峰值见 `V3_REPORT_SUPPLEMENT04.md`。\n", "干跑峰值见 `V3_REPORT_SUPPLEMENT04.md`。\n\n**补充 05 核对（2026-11-03）：** 第 180 项每个时段再加 5 列、9 行，365×24h 一体化 +3,285 行（+0.03 %）。时限、规格、机时和费用仍不需要改；干跑峰值见 `V3_REPORT_SUPPLEMENT05.md`。\n"),
    ("第 179 项后专线年均利用率的结构上界约 50 %（`evidence/SOURCE_LINE_BOUND_V3.json`，只含水电、径流、风电），按这个上界读", "第 180 项后专线年均利用率的结构上界约 40 %（`evidence/SOURCE_LINE_BOUND_OP_V3.json`，只含运营中的水电、径流），按这个上界读"),
])
patch("V3_DEPLOY_FILES.md", [("## 1. 两边共用\n", "**补充 05 更新（2026-11-03）：** 第 180 项（源母线只放运营中机组）后网络再次重建，现行登记见 `RUN_PLAN_V3.md` 第 21 节，现行筛查包是 `work/p1_v3_20261102/screen_package_v3_op/`，`screen_package_v3/`、`screen_package_v3_oneway/`、`screen_package_v3_bound/` 已作废，保留不用。\n\n## 1. 两边共用\n")])
patch("V3_PROGRESS.md", [
    ("\n## 恢复点", "| 用户决定状态判据 | 原话\"用 GIPT Status 继续\"，判据取 GIPT 2026-09 `Status` | — |\n| 补充 05 代码、规则、测试 | 完成：只移运营中机组，2 个混合组件拆分，状态表，规则 `V3_RULES.md` 第 2.5 节 | `3cb20131` |\n| 补充 05 重建与登记 | 完成：7 个网络，静态与路径检查通过，逐组件比较通过，完全隔离逐字节相同；容量表与预测在 `RUN_PLAN_V3.md` 第 21 节 | 构建 `3cb20131`，登记本次提交 |\n\n## 恢复点"),
])
x = open(D + "V3_PROGRESS.md", encoding="utf-8", newline="").read().replace("|\n\n| 用户决定状态判据", "|\n| 用户决定状态判据")
i = x.index("补充 05 停在第 1 条之前"); k = x.index("## 计数")
x = x[:i] + "补充 05：运行 `bash /home/jin/v3/smoke_s5.sh --confirmed <确认时间>`（用户已答复，见 `RUN_PLAN_V3.md` 第 21.3 节），之后 `dry_s5.sh`、`pkg_s5.sh`、全量测试、`V3_REPORT_SUPPLEMENT05.md`。额度：本机 Gurobi 2 次，计算 1.5 小时，磁盘 15 GB。\n\n" + x[k:]
open(D + "V3_PROGRESS.md", "w", encoding="utf-8", newline="").write(x)
print("plan ok", s_.to_dict())
