"""Supplement 01 step 5: run record appended to RUN_PLAN_V3.md (sections 3, 4, 5, 10, 11 untouched), progress file."""
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
p = D + "RUN_PLAN_V3.md"; s = open(p, encoding="utf-8", newline="").read()
assert "## 14." not in s
s = s.rstrip("\n") + """

## 14. 补充 01 运行记录（求解后追加，第 10、11 节未改）

用户 2026-11-02 原话"已断开，可以求解"（WSL 时钟约 15:35 UTC）。启动前 WSL 到 `token.gurobi.com:443`、`github.com:443`、`1.1.1.1:443` 的 TCP 全通，无求解和 pytest 进程。提交 `7e3603c2`，四次串行，15:35:53–16:12:23 UTC，额度 4 / 4，没有重试。

| 运行 | 终止状态 | 目标值（bn） | GATES_V6 | 峰值（GiB） |
|---|---|---:|---|---:|
| `integrated` | optimal | 329.1975 | `ACCEPTED_LAYER2` | 7.22 |
| `no_new_xb` | suboptimal | 341.9075 | `ACCEPTED_LAYER2` | 5.71 |
| `integrated_flat` | optimal | 339.4751 | `ACCEPTED_LAYER2` | 7.16 |
| `no_new_xb_flat` | optimal | 352.6281 | `ACCEPTED_LAYER2` | 6.04 |

第 10.3 节的验收两次都通过。B6 12.7100 bn；flat 13.1530 bn。EV 效应（flat − E2）：总成本 +10.2776、+10.7207 bn，B6 +0.4431 bn。v3 flat − v2 一体化 −1.1869 bn。

第 10.3 节的事先说明漏了两项：E2 一体化的 B1、A3_S4B 不通过，是我的遗漏，原文不改，详见 `V3_REPORT_SUPPLEMENT01.md` 第 2.3 节。第 10.4 节的预测有一项略超范围（EV 效应一体化 10.28 bn，预测 5–10 bn），原文不改。
"""
open(p, "w", encoding="utf-8", newline="").write(s)
p = D + "V3_PROGRESS.md"; s = open(p, encoding="utf-8", newline="").read()
a = "| 补充 01 第 3 步 | **等用户确认 WLS 会话空闲、AnyConnect 已断开** | — |\n"
b = "| 补充 01 第 3 步 | 用户确认已断开、可以求解 | — |\n| 补充 01 第 4 步 | 完成：四次冒烟，验收通过，`no_new_xb` E2 suboptimal 按 C1 与 GATES_V6 通过 | 求解 `7e3603c2` |\n| 补充 01 第 5 步 | 完成：`V3_REPORT_SUPPLEMENT01.md`，运行记录 `RUN_PLAN_V3.md` 第 14 节 | 本次提交 |\n"
assert s.count(a) == 1; s = s.replace(a, b)
a = s[s.index("## 恢复点"):]
b = """## 恢复点

补充 01 完成，等审阅。之后的第一件事是 X1b（`V3_RULES.md` 第 2.2 节，筛查前必须完成，需另行授权），再重做网络、定义文件登记值、打包脚本和 v3 版 `RUN_PLAN_HPC.md`。

## 计数

本机 Gurobi：阶段 3 第二轮 2 / 2（第一轮 2 次未取得令牌，不计入）；补充 01 为 4 / 4。本机计算约 3.9 小时 / 6 小时，磁盘约 7.1 GB / 40 GB。
"""
s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s); print("ok")
