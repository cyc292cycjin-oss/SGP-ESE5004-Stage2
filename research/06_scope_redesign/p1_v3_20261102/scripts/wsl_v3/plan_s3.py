"""Supplement 02: progress file, deployment list."""
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
p = D + "V3_PROGRESS.md"; s = open(p, encoding="utf-8", newline="").read()
a = "| 全量测试 | 提交 `598e549e`：730 通过、58 跳过、3 失败（与 v3 无关，同上一轮） | 本次提交 |\n"
b = """| 全量测试 | 提交 `598e549e`：730 通过、58 跳过、3 失败（与 v3 无关，同上一轮） | `9033ed40` |
| 审阅决定 `V3_REVIEW_DECISIONS_SUPP01.md` | 已收，补充 02 | — |
| 补充 02 第 2.1 节 X1b | 完成：11 项全部运营且在网络中，全部计入；APG 955 MW 是七条 115 kV 线，不重复 | `f6d90e37`、`1ccd35e8`、`4df45b56` |
| 补充 02 第 2.3 节第 1 项 重建 | 完成：7 个网络，静态检查全过，HiGHS 路径检查走通 | 构建 `4df45b56` |
| 补充 02 第 2.2 节 规则与预测 | 完成，**第 176 项全文待用户提供** | 本次提交 |
| 补充 02 第 2.3 节第 2 项 冒烟 | **等用户确认 WLS 会话空闲、AnyConnect 已断开** | — |
"""
assert s.count(a) == 1; s = s.replace(a, b)
a = s[s.index("## 恢复点"):]
b = """## 恢复点

补充 02：运行 `bash /home/jin/v3/smoke_s2.sh --confirmed <确认时间>`（输出 `results_project/v3/smoke_s2`），额度 Gurobi 0 / 2。之后筛查包（`screen_package/make_package_v3.sh`，先跑 `/home/jin/v3/dry_s2.sh`），最后写 `V3_REPORT_SUPPLEMENT02.md`。第 176 项全文写入 `V3_RULES.md` 后才能求解。

## 计数

本机 Gurobi：阶段 3 第二轮 2 / 2；补充 01 为 4 / 4；补充 02 为 0 / 2。补充 02 新增上限：本机计算 4 小时，磁盘 30 GB；目前约 0.8 小时、4.2 GB。
"""
s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s)
p = D + "V3_DEPLOY_FILES.md"; s = open(p, encoding="utf-8", newline="").read()
a = "## 1. 两边共用\n"
b = """**补充 02 更新（2026-11-03）：** X1b 已实施，下面第 2、3 节的字节数和 SHA256 都是 X1b 之前的，已作废。现行登记值见 `RUN_PLAN_V3.md` 第 15.1 节和 `batch_def/`。AutoDL 筛查包改为 5 个网络，由 `screen_package/make_package_v3.sh` 打包，清单见 `V3_REPORT_SUPPLEMENT02.md`。HPC 的打包脚本和 v3 版 `RUN_PLAN_HPC.md` 仍未做，放到筛查之后。

## 1. 两边共用
"""
assert s.count(a) == 1; s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s); print("ok")
