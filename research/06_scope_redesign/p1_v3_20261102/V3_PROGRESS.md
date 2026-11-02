# V3 进度

分支 `codex/v3-20261102`（自 `0a20aefd`），worktree `/home/jin/wt_v3_20261102`，会话脚本 `/home/jin/v3/`（镜像 `scripts/wsl_v3/`），中间结果 `results_project/v3/`（主检出）。

| 步骤 | 状态 | 提交 |
|---|---|---|
| 第 0 节：SHA256、基点、分支、进程检查 | 完成 | 分支起点 `0a20aefd` |
| 阶段 1：代码定位、数据盘点、设计、报告 | 完成，审阅通过 | `b6de71c4` |
| 审阅决定 `V3_REVIEW_DECISIONS_PHASE1.md`（SHA256 `5bc090fe…`） | 已收 | 副本在本目录 |
| 阶段 2：工业、节点、EV 输入 | 完成 | `6a5b10a2` |
| 阶段 2：需求表、差异表、测试、注册表 v3、`V3_RULES.md` | 完成，六项测试全过 | `4c4dd137`、`84d56c93` |
| 阶段 3：网络代码、静态检查脚本、单元测试 | 完成 | `85095e7a` |
| 阶段 3：构建四个网络、静态检查、LP 规模 | 完成，`all_structural_passed` | 网络 `85095e7a`，检查 `19b6eaf4` |
| `RUN_PLAN_V3.md` | 完成 | `19b6eaf4`、`67c84596`、`dd47744b`、`88fdbd95` |
| HiGHS 8 时段路径检查 | 完成，两情景全链路走通 | `dd47744b` |
| 既有测试 | 最终 721 通过、58 跳过、3 失败（与 v3 无关） | `023a378a` |
| 冒烟第一轮 | 未进入求解（WSL 外连中断），用户决定不计入额度 | `e68c5668` |
| 冒烟第二轮 | 完成，五条验收通过；`no_new_xb` suboptimal 按 (a)(b) | 求解 `88fdbd95` |
| `V3_REPORT_PHASE3.md` | 完成 | 本次提交 |

| 审阅决定 `V3_REVIEW_DECISIONS_PHASE3.md` | 已收，补充 01 共 5 步 | — |
| 补充 01 第 1 步 X1 | 用户选 APG existing，现网不换值；X1b 已登记未实施 | `ce3fd5f7`、`7faeb8fa` |
| flat 对照网络 | 完成，差异只在 EV 层 | 构建 `7faeb8fa` |
| 补充 01 第 2 步（决定 3–8） | 完成：档案、验收、预测、附注、VPN、运行器、测试、干跑 | 本次提交 |
| 补充 01 第 3 步 | **等用户确认 WLS 会话空闲、AnyConnect 已断开** | — |

## 恢复点

第 3 步：得到确认后运行 `bash /home/jin/v3/smoke_s1.sh --confirmed <确认时间>`（输出 `results_project/v3/smoke_s1`），补充额度 Gurobi 0 / 4。之后写 `V3_REPORT_SUPPLEMENT01.md`。

## 计数

本机 Gurobi：阶段 3 第二轮 2 / 2（第一轮 2 次未取得令牌，不计入）；补充 01 为 0 / 4。本机计算约 3.2 小时 / 6 小时，磁盘约 4.2 GB / 40 GB。
