# V3 HPC 正式运行包报告（台账 V14）

- **指令：** `work/p1_v3_20261102/V3_HPC_PACKAGE_INSTRUCTION.md`，SHA256 `29dc0b0fafd0731e57cf85d054eaebc8a44ebaa10f4446dcfbbe0a8ba3b3ade1`，与同目录 `V3_HPC_PACKAGE_SHA256.txt` 一致（2026-11-04 00:25 SGT 核对）。
- **开始条件（用户 2026-11-04 授权的补充）：** V27 主体已结束（`V3_REPORT_SUPPLEMENT07.md` 第 8 节已推送，头提交 `5e372e5d`），第 8.4 节由另一个会话补写，视为满足。为避免两个会话在同一分支提交，本次在新 worktree `/home/jin/wt_v3_hpc`、自 `5e372e5d` 开出的新分支 `codex/v3-hpc-20261104` 上工作；未进入 `/home/jin/wt_v3_20261102`、`/home/jin/v3s/`，未碰 `work/p1_v3_20261102/cloud_results/`。
- **用户在本会话的决定：** (1) S-A 按登记定义 η = 1，原话"S-A 单价为全成本，已含船用燃料与运营费用，货损不再另计，避免重复计算"，核对时允许船运链路的 `marginal_cost` 与 `efficiency` 两个字段不同；(2) 网络元数据里的构建 worktree 路径在构建前登记为来源差异；(3) 冒烟直接开始（WLS 空闲、AnyConnect 已断开）。
- **证据等级：** VERIFIED（读了数组、回执、闸门文件）、EXACT（逐位或有理数核验）、INFERENCE（机制解释与外推）、PROPOSED（未执行、待决定）。
- **计算记账：** 本机 Gurobi **2 / 2**（两次冒烟）；HPC、AutoDL 未连接，未上传。其余见第 9 节。

（报告正文待打包、干跑与泄露扫描完成后补全。）
