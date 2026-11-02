"""Supplement 03 items 2.2, 2.3: registration before the solve. Section 15.1 keeps its table with a note that it is superseded."""
import json
from pathlib import Path
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
d3 = json.loads(Path(D + "batch_def/BATCH_DEF_365x24h.json").read_text(encoding="utf-8")); d2 = json.loads(Path(D + "batch_def/BATCH_DEF_2920x3h.json").read_text(encoding="utf-8"))
sh = {**d3["registered_sha"], **d2["registered_sha"]}; by = {**d3["registered_bytes"], **d2["registered_bytes"]}
rows = "\n".join(f"| `{k}` | {by[k]:,} | `{sh[k]}` |" for k in ("integrated_2920_3h_unsolved.nc", "no_new_xb_2920_3h_unsolved.nc", "integrated_365_24h_unsolved.nc", "no_new_xb_365_24h_unsolved.nc", "disconnected_365_24h_unsolved.nc", "bridge_160_162_365_24h_unsolved.nc", "bridge_160_164_365_24h_unsolved.nc"))
p = D + "RUN_PLAN_V3.md"; s = open(p, encoding="utf-8", newline="").read()
a = "### 15.1 X1b 后的网络\n\n"
b = "### 15.1 X1b 后的网络\n\n**已被单向专线取代：** 本节的 SHA256 和 LP 规模是双向专线的，现行登记见第 17.1 节。\n\n"
assert s.count(a) == 1; s = s.replace(a, b); assert "## 17." not in s
s = s.rstrip("\n") + f"""

## 17. 补充 03 登记（求解前）

依据 `V3_REVIEW_DECISIONS_SUPP02.md` 第 2 节。第 3、4、5、10、11、15 节的原有内容不改（第 15.1 节只加了取代标注）。

### 17.1 单向专线后的网络

构建提交 `{d3['build_commit']}`，输出 `results_project/v3/builds_oneway`。规则见 `V3_RULES.md` 第 2.3 节。

| 文件 | 字节 | SHA256 |
|---|---:|---|
{rows}

完全隔离网络没有专线，与双向版本逐字节相同。

| LP | 列 | 行 | 非零 |
|---|---:|---:|---:|
| 一体化，56 时段 | 728,596 | 1,602,036 | 3,713,762 |
| `no_new_xb`，56 时段 | 707,242 | 1,554,454 | 3,563,528 |
| 一体化，365×24h | 4,690,594 | 10,371,765 | 24,234,012 |
| `no_new_xb`，365×24h | 4,553,365 | 10,064,623 | 23,258,439 |
| 完全隔离，365×24h | 4,536,210 | 10,021,188 | 23,146,749 |
| 修订桥 160–164，365×24h | 4,620,610 | 10,266,741 | 24,058,908 |
| 修订桥 160–162，365×24h | 4,699,649 | 10,474,990 | 24,449,657 |

### 17.2 运行与验收

脚本 `/home/jin/v3/smoke_s3.sh`，输出 `results_project/v3/smoke_s3`。档案 `formal_barrier_1e6_t16`，前 56 时段，TimeLimit 3,000 s，墙钟止损 3,600 s，串行，间隔 ≥ 330 s，不重试、不改参数。额度 2 次：一体化、`no_new_xb`。用户 2026-11-03 确认 WLS 空闲、AnyConnect 未连接。

验收同第 15.3 节。闸门预告用并集规则：A1_A2、A1_A2_S4B、A3、A3_S4B、B1、B3、B8，B8 只有 Transport，相对差 −4.1146e-05。

### 17.3 56 时段预测（INFERENCE，以第 16 节双向结果为基线；这一周是枯水期）

| 项 | 预测 | 依据 |
|---|---|---|
| 一体化总成本 | 上升，不超过 0.23 bn | 不会高于 X1b 前的 329.20 bn：单向比无专线宽松 |
| `no_new_xb` 总成本 | 上升，不超过 0.52 bn | 同上，不会高于 341.91 bn |
| B6 | 12.42–12.71 bn | 专线的调节收益主要在 `no_new_xb`，去掉后 B6 回升 |
| `no_new_xb` 的 LA–TH 进口 | 降到 3 TWh 以下 | 只剩 APG 线路可进口 |
| `no_new_xb` 的 LA–TH 出口 | 明显低于双向的 12.49 TWh | 枯水期 LA 没有富余水电，出口不再靠进口回补 |
| LA 受益 | −0.15 到 +0.10 bn | 介于双向 −0.11 和无专线 +0.04 附近 |

### 17.4 单向专线后的 365×24h 预测（筛查前登记）

参考了补充 02 的冒烟，并考虑了 LA 水电的季节分布，不是独立于冒烟的预测。第 11、15.5 节的原有预测不改。

| 项 | 预测 | 依据 |
|---|---|---|
| B6 = V2 − V1 | 为正，9.5–13.5 bn | 雨季 LA 以出口为主，单向约束不绑定；枯水期去掉调节收益，B6 比双向略高，0–0.5 bn |
| LA 受益 | 低于 v2 筛查的 +1.229 bn，−0.4 到 +0.7 bn | 专线留在对照情景，但 LA 不能再经专线进口 |
| TH 受益 | 低于无专线情形，0.6–2.5 bn（v2 筛查 +1.769 bn） | TH 在对照情景里仍能买到老挝雨季水电 |
| V3 − V2（存量与专线的价值） | 为正，1.5–5.5 bn | 单向使专线的价值略低于第 15.5 节的 2–6 bn |
| 专线利用 | 7–10 月接近满载；全年平均 40–70 %；LA–TH 专线电量全部是出口 | LA 水电资源 7–9 月 11–18 GW，单向 |

第 15.5 节中 B6"相对 X1b 前"那一项**无法直接检验**（审阅决定不加不含专线的运行），筛查报告如实说明。
"""
open(p, "w", encoding="utf-8", newline="").write(s)
p = D + "V3_PROGRESS.md"; s = open(p, encoding="utf-8", newline="").read()
a = "## 恢复点"
b = """| 审阅决定 `V3_REVIEW_DECISIONS_SUPP02.md` | 已收，补充 03：专线改单向；第 176 项全文已写入 | `93cdecbc` |
| 补充 03 重建与登记 | 完成：7 个网络，静态与路径检查通过，完全隔离逐字节相同 | 构建 `93cdecbc`，登记本次提交 |

## 恢复点"""
assert s.count(a) == 1; s = s.replace(a, b)
i = s.index("补充 02 完成，等审阅。"); j = s.index("## 计数")
s = s[:i] + "补充 03：运行 `bash /home/jin/v3/smoke_s3.sh --confirmed <确认时间>`，之后 `dry_s3.sh`、`pkg_s3.sh`、全量测试、`V3_REPORT_SUPPLEMENT03.md`。\n\n" + s[j:]
a = "补充 02 本机计算约 1.8 小时 / 4 小时，磁盘约 9.6 GB / 30 GB。"
b = a + "补充 03 为 0 / 2，上限本机计算 2 小时、磁盘 20 GB。"
assert s.count(a) == 1; s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s); print("ok")
