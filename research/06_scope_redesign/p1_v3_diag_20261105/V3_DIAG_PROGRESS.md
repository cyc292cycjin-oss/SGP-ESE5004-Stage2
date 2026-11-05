# V3 DIAG 进度（决策清单第 194 项）

指令：`V3_DIAG_INSTRUCTION.md` v1，SHA256 `e6f4c06c7ee4dfd41d3e7834b01b8a3c1d0d61c964233494616bb1e2edfe4d05`，与 `V3_DIAG_SHA256.txt` 一致，2026-11-05 15:32 SGT 核对。

- **开始条件**：用户于 2026-11-05 15:33 SGT 确认 AnyConnect 已断开，本机与 AutoDL 均无其他 Gurobi 进程。
- **本机资源**：WSL 内存上限 11 GB（free 显示 10 GiB），另有 4 GB swap；16 个逻辑核；物理内存 15.7 GB。
- **代码位置**：worktree `/home/jin/wt_v3_diag`，分支 `codex/v3-diag-20261105`，起点 `7d22dda112a3c18ed57e8c061d95e51915980417`，即部署包的 COMMIT。
- **运行与证据**：运行目录在主检出的 `results_project/v3diag/`（git 忽略，共 14.2 GB）；证据在 `evidence/`；Gurobi 调用账本是 `evidence/GUROBI_CALLS.csv`，共 35 次；过程状态记在 `evidence/DIAG_STATUS.txt`。

| 步骤 | 状态 | 说明 |
|---|---|---|
| 预检 | 完成 | WSL 到 token.gurobi.com:443 的 TCP 连通；无 Gurobi 进程；AnyConnect 网卡为 Disabled |
| 网络 SHA256 | 完成 | 4/4 与 `pbs/HPC_PLAN.txt` 一致 |
| 1 对照组 | 完成 | C0 得到 ITERATION_LIMIT；诊断入口与运行器 TRUNCATE 写出的 problem.lp 逐字节相同 |
| 2 按月窗口 | 完成 | 31 天的月份和 2 月 INF_OR_UNBD，30 天的月份通过 |
| 3 缩小 / IIS | 完成（IIS 未得到） | 失败随窗口长度和权重变化，与具体日期无关；IIS 在 30 分钟内未完成；删除过滤确认必要行是 `research_bunker_co2_limit` |
| 4 全年累计约束 | 完成（分支未触发） | 两种口径右端项相同；全年本机内存不够，给出 HPC 诊断作业建议（PROPOSED） |
| 5 F2 / F3 / F4 | 完成 | F2 是同一原因（VERIFIED）；F3、F4 的 bunker 结构与 F1 相同（静态检查） |
| 6–8 解释、修正方案、闸门 | 完成 | 见报告第 8–10 节，均为 PROPOSED |
| 报告、提交、推送 | 完成 | 证据提交 `26b7845cb9826d3f0ce78734be47e7f8049580dd` 已推送到 origin `codex/v3-diag-20261105`（含台账条目）；收尾提交只更新本文件和报告第 14 节 |

**状态：DONE，已停止。** 等待审阅端与 Fable 审查（第 194 项）。未创建 PR。Gurobi 剩余 5 次未用。
