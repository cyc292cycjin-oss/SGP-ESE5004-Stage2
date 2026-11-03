# V3 HPC 正式运行包——进度（台账 V14）

- 指令：`V3_HPC_PACKAGE_INSTRUCTION.md`，SHA256 `29dc0b0fafd0731e57cf85d054eaebc8a44ebaa10f4446dcfbbe0a8ba3b3ade1`，与 `V3_HPC_PACKAGE_SHA256.txt` 一致（2026-11-04 00:25 SGT 核对）。
- 开始条件（用户 2026-11-04 授权的补充）：V27 主体已结束（`V3_REPORT_SUPPLEMENT07.md` 第 8 节已推送，头提交 `5e372e5d`），第 8.4 节由另一个会话补写，视为满足。
- 工作位置：新 worktree `/home/jin/wt_v3_hpc`，分支 `codex/v3-hpc-20261104`（自 `5e372e5d`）；不进入 `/home/jin/wt_v3_20261102`、`/home/jin/v3s/`，不碰 `work/p1_v3_20261102/cloud_results/`。会话脚本 `/home/jin/v3h/`（镜像 `scripts/wsl_v3h/`），结果 `results_project/v3hpc/`（主检出）。
- 复制到 `work/p1_v3_20261102/`：本会话新建的文件随时复制；`RUN_PLAN_V3.md`、`V3_RULES.md` 等共用文件等 `V3_PROGRESS.md` 末尾出现 V27 会话的关机记录后再复制。
- 用户 2026-11-04 的决定：(1) S-A 按登记定义 η = 1（"S-A 单价为全成本，已含船用燃料与运营费用，货损不再另计，避免重复计算"），核对时允许船运链路的 `marginal_cost` 与 `efficiency` 两个字段不同；(2) 构建路径字符串在构建前登记为来源差异。冒烟直接开始（WLS 空闲、AnyConnect 已断开）。

| 步骤 | 状态 | 提交 |
|---|---|---|
| 0 准备 | worktree、忽略输入（`results_project` 链接主检出，6 个忽略文件复制）；`5e372e5d` 试构建：与 `1bddacb7…` 全部变量逐位相同，元数据只差构建路径 | — |
| 1 规则与小修 | `V3_RULES.md` 第 2.3 节末、第 3.3 节、第 8.3 节、第 10 节第 4、7 条、第 12 节；S-A 主值（`baseline.yaml`）；注册表等级；载体份额缺键报错；`DIRECT` 单一来源；四个玩具网络测试；`BATCH_DEF_2920x3h.json` 注记 | `a1ef782b` |
| 2 构建 F1–F4 与核对 | 构建 `a1ef782b`（约 4 分钟）；核对全部通过（`evidence/hpc/F_REBUILD_CHECK.json`）；静态检查两根全过；F1 `8b5fd663…`、F2 `e2837e4a…`、F3 `c4eb7c44…`、F4 `0bbe235e…`；登记 `RUN_PLAN_V3.md` 第 24 节（含冒烟计划、闸门预告、S-A 事先估计）；第 12.3 节计数笔误（810 → 270）核对后更正 | `a4607714`（已推送） |
| 3 本机冒烟（2 次） | 2026-11-04 01:24–01:42 SGT，额度 2 / 2：一体化 329.7056、`no_new_xb` 342.2687 bn，都 optimal、C1 111、`ACCEPTED_LAYER2`；B6 12.5631（S-B 12.5665，−0.0034）；失败闸门都在预告内；记录 `RUN_PLAN_V3.md` 第 25 节 | 本次提交 |
| 4 预测 | `RUN_PLAN_V3.md` 第 26 节（两参照并列与结构差异） | 本次提交 |
| 5 `RUN_PLAN_HPC_V3.md` | 写成；PROPOSED：TimeLimit 1,296,000 s、walltime 376 / 378 h、进程 1 超时 7,200 s、批级 48 h；参考迭代 350 / 250；运行器四运行扩展、启动锁、PROPOSED 拒绝；定义文件 `batch_def/BATCH_DEF_2920x3h_v3hpc.json` | 本次提交 |
| 6 部署包、操作指南、干跑、预检、泄露扫描 | 待做 | — |
| 7 报告、推送、复制、停下 | 待做 | — |

恢复点：第 24 节提交后启动冒烟 `bash /home/jin/v3h/smoke_h.sh --confirmed <时间>`（输出 `results_project/v3hpc/smoke_hpc`；目录已有回执则拒绝，不重跑）。计数：本机 Gurobi 0 / 2；本机计算约 0.6 小时 / 4 小时（构建 4 分钟、静态检查、两次核对约 25 分钟含一次卡死后重跑）；磁盘新增约 0.5 GB / 40 GB。
