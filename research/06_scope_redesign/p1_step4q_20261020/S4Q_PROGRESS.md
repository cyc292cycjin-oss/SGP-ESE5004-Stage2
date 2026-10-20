# S4Q 进度记录（防中断用；时间为 SGT；不含任何主机、端口、密码或许可内容）

指令 `S4Q_CLAUDE_CODE_INSTRUCTION.md`（v1），开始前核对 SHA256 = `c33f97e71dabd0a4cf159ddd636168c3cf6e3244ca8ad94deecb1d484504b75d`，与 `S4Q_INSTRUCTION_SHA256.txt` 及启动消息给出的值一致（VERIFIED，08:00）。模型 Opus 5.5。所有过程说明一律用中文。背景已读：`work/p1_step4o_20261019/S4O_REPORT.md` 全文（重点 §4、§5、§10、§11）。

## 用户授权原文（启动消息，原样记录）

> 请先阅读并执行 D:\ResearchWorkspaces\ASEAN\work\p1_step4q_20261020\S4Q_CLAUDE_CODE_INSTRUCTION.md。
> 开始前核对 SHA256 应为 c33f97e71dabd0a4cf159ddd636168c3cf6e3244ca8ad94deecb1d484504b75d，不一致就停下报告。
> 背景请读 work/p1_step4o_20261019/S4O_REPORT.md（§4、§5、§10、§11）。
> 授权：本机 6 次 56×3h 运行（1e-6 候选档案 × 两种线程 × 三个情景），各 30 分钟止损、不重试；不连云。另有一个 S4P 会话同时在做只读核查，请用独立的 git worktree 与分支。
> 所有过程说明、进度汇报和思考要点一律用中文输出。完成后写 S4Q_REPORT.md 并停止，等待审阅。

## 工作位置

- worktree：`/home/jin/wt_s4q_20261020`，分支 `codex/s4q-tol-calibration-20261020`，自 S4O 分支头 **0b681881** 开出（08:01）。S4P 会话用的是 `/home/jin/wt_s4p_20261020`（分支 `codex/s4p-country-audit-20261020`），两者互不触碰。
- 交付目录：仓库 `research/06_scope_redesign/p1_step4q_20261020/`；Windows 镜像 `work/p1_step4q_20261020/`。
- 本机运行目录（不进 git）：`/home/jin/s4q_local/`。

## 方案（开始前定下，执行中不改）

1. **S4Q-1：** `configs/research/baseline.yaml` 新增 `formal_barrier_1e6`（只改 `BarConvTol: 1.0e-6`）与 `formal_barrier_1e6_t16`（另加 `Threads: 16`），注释写明第 123 项、"单因素、两种路径"、非生产；缺省档案仍为 `formal_barrier`。单元测试 `tests/research/test_s4q_1.py` 逐键核对。
2. **运行流水线（S4O 版 `run_365x24h.sh`）的两处必要改动，缺省行为不变：**
   - 档案白名单加入这两个档案；
   - 新增 `FIXED_RUNS=on`（缺省 off）：只跑 `--runs` 列出的运行——不触发"一体化非最优且 C1 不通过即停止"，也不在不互联非最优时自动加跑 `disconnected_gap`。理由：S4Q-2 要求"6 次全部跑完再判定"，且授权恰为 6 次，自动诊断会成为第 7 次求解。
   - 测试：S4O 脚本测试全套（59 项）重跑到 S4Q 证据目录（不覆盖 S4O 历史结果），另写 S4Q 用例（新档案、`FIXED_RUNS`）。
3. **S4Q-2：** 类包目录 `/home/jin/s4q_local/pkg`（代码 = S4Q-1 提交的 `git archive`；三个网络 = S4M-1 2920×3h 构建的符号链接，与 S4M-2 回执的 SHA256 核对；构建成本表）；`TRUNCATE=56`、TimeLimit 1,750 s / 墙钟 1,800 s（30 分钟止损，与 S4O-3′ 相同）、`FIXED_RUNS=on`、`--runs integrated,disconnected,integrated_nze`；先 `formal_barrier_1e6`（Threads 8）三次，再 `formal_barrier_1e6_t16` 三次；相邻求解间隔 ≥ 330 s（档案之间由驱动脚本保证）。
4. **S4Q-3：** 判据按指令原文，不调整。C1 (b)(c) 的分国参照 = S4M-2 56×3h "不互联 − 一体化"差额：在影子目录（复制 `PRECISION.json`）用 `s4o_c1_precision.py regrade` 重评，运行结果不改。目标 / B16 / 分国差额 / 信息项复用 `s4n_c2_compare.py`（第 107 项的既有实现）；判据 4（NZE 各实体 total）另算。

## 步骤状态

| 步 | 内容 | 状态 | 时间（SGT） | 提交 / 说明 |
|---|---|---|---|---|
| S4Q-0 | 核对与背景、worktree | 完成 | 08:00–08:02 | SHA256 一致；worktree 与分支已建 |
| S4Q-1 | 候选档案、测试、流水线开关 | 进行中 | 08:02– | ① `baseline.yaml` 新增 `formal_barrier_1e6`、`formal_barrier_1e6_t16`（注释：第 123 项、单因素、两种路径、非生产；缺省仍 `formal_barrier`）；② `run_365x24h.sh`：白名单 + `FIXED_RUNS`（缺省 off）；③ `tests/research/test_s4q_1.py` 4 项通过；`tests/research` 全套在 worktree 中 483 通过 / 2 失败 / 63 跳过——基线 0b681881 在全新 worktree 中同为 2 失败 / 63 跳过（479 通过），失败与跳过源于 worktree 不含被忽略的输入文件（如 `research_inputs/finance_v5/COUNTRY_WACC_PUBLIC_SOURCES.csv`），与本次改动无关；483 = 479 + 4 |
| S4Q-2 | 6 次本机运行 | 未开始 | | |
| S4Q-3 | 判定 | 未开始 | | |
| S4Q-4 | 报告 | 未开始 | | |

## 续行点

S4Q-1 进行中：先改 `baseline.yaml` 与运行脚本，再写测试。
