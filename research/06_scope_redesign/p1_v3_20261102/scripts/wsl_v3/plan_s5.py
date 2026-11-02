"""Supplement 02: run record after the smoke (sections 15.3-15.5 untouched)."""
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
p = D + "RUN_PLAN_V3.md"; s = open(p, encoding="utf-8", newline="").read()
assert "## 16." not in s
s = s.rstrip("\n") + """

## 16. 补充 02 运行记录（求解后追加，第 15 节未改）

用户 2026-11-03 确认 WLS 空闲、AnyConnect 已断开（WSL 时钟 2026-11-02 18:01 UTC）。提交 `9dc4c35e`，两次串行，18:02:33–18:17:57 UTC，间隔 331 s，额度 2 / 2，没有重试。

| 运行 | 终止状态 | 目标值（bn） | GATES_V6 | 峰值（GiB） |
|---|---|---:|---|---:|
| `integrated` | optimal | 328.9707 | `ACCEPTED_LAYER2` | 6.82 |
| `no_new_xb` | optimal | 341.3865 | `ACCEPTED_LAYER2` | 6.06 |

验收两次都通过。B6 12.4158 bn。第 15.3 节预告的闸门之外没有新增失败项。第 15.4 节的预测有三项落空（B6、`no_new_xb` 总成本、TH 受益的幅度），原文不改，详见 `V3_REPORT_SUPPLEMENT02.md` 第 3 节。第 15.5 节不改。

**顺序偏差：** 第 176 项全文未能在求解前提交，见 `V3_RULES.md` 第 10 节。
"""
open(p, "w", encoding="utf-8", newline="").write(s)
p = D + "V3_PROGRESS.md"; s = open(p, encoding="utf-8", newline="").read()
a = "| 补充 02 第 2.3 节第 2 项 冒烟 | 用户 2026-11-03 确认空闲、已断开；第 176 项全文未到，先求解，全文待补 | 本次提交 |\n"
b = "| 补充 02 第 2.3 节第 2 项 冒烟 | 完成：两次 optimal，验收通过，B6 12.42 bn；第 176 项全文未到，待补 | 求解 `9dc4c35e` |\n"
assert s.count(a) == 1; s = s.replace(a, b)
a = "补充 02：运行 `bash /home/jin/v3/smoke_s2.sh --confirmed <确认时间>`（输出 `results_project/v3/smoke_s2`），额度 Gurobi 0 / 2。之后筛查包"
b = "补充 02：冒烟完成（`results_project/v3/smoke_s2`），额度 Gurobi 2 / 2。接下来筛查包"
assert s.count(a) == 1; s = s.replace(a, b)
a = "补充 02 为 0 / 2。补充 02 新增上限：本机计算 4 小时，磁盘 30 GB；目前约 0.8 小时、4.2 GB。"
b = "补充 02 为 2 / 2。补充 02 新增上限：本机计算 4 小时，磁盘 30 GB；目前约 1.2 小时、7 GB。"
assert s.count(a) == 1; s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s); print("ok")
