
### V3 DIAG（第 194 项：V3 全年 2920×3h 不可解诊断；本机，只到预处理或 IIS）— 2026-11-05

- **范围：** `V3_DIAG_INSTRUCTION.md` v1，SHA256 e6f4c06c…4d05，已核对一致。代码冻结在 `7d22dda1`（部署包 COMMIT）。分支 `codex/v3-diag-20261105`，worktree `/home/jin/wt_v3_diag`。网络直接读 `hpc_package_v3/networks/`，SHA256 4/4 与 HPC_PLAN 一致。没有重建网络，也没有改模型代码、配置、输入、档案、阈值或预测。
- **根因（窗口层面 VERIFIED，全年为 INFERENCE）：** 燃料舱净零约束 `research_bunker_co2_limit` 要求一个只有排放端口（82 个化石航煤计量，系数 0.2571 t/MWh）、没有移除端口的账户在最后时段水平 ≤ 0。这等价于所有计量流量恒为 0，是一条零松弛的强制约束。Gurobi 默认预处理在代换聚合加对偶约简后，对部分时段数和权重组合判定 INF_OR_UNBD。
  - 在 F1_M02、F1_M01、F2_M02 三个窗口上，只删这一行，或只把右端项放宽 1 t，或改写为"计量流量 = 0"，同一份 LP 的预处理都改为通过。
  - 删掉国家净零约束或年度燃气产量上限，都不能消除这个判定。
- **证据：**
  - **对照组**：C0（F1 前 56 时段，TRUNCATE）得到 ITERATION_LIMIT；诊断入口与运行器 TRUNCATE 写出的 problem.lp 逐字节相同。
  - **月窗口**：31 天的月份和 2 月（每时段权重 35.32 h、39.11 h）INF_OR_UNBD，30 天的月份（36.5 h）通过。1 月 1–30 日和 2–31 日都通过；各周窗口通过；原始 3 h 权重的周和月都通过。可见失败对权重非单调，取决于舍入。
  - **预处理参数敏感性**：`DualReductions=0`、`Aggregate=0`、`Presolve=1` 都让预处理通过，`NumericFocus=3` 仍失败。
  - **IIS**：在 30 分钟上限内未完成。
- **F3、F4（静态）：** bunker 结构与 F1、F2 完全相同，带同一条零松弛行。
- **修正（PROPOSED）：** 只改 `s4c_layers.install_bunker_net_zero` 一处，把最后时段水平行改为对账户排放端口链路的 `Link-p == 0`，约束名不变。可行域与最优解相同；右端项都为 0，所以按右端项分摊的结果不变，也不会把成本转移到任何国家（INFERENCE）。建议另行授权一次 56×3h 回归。365×24h 筛查不需要重跑。
- **闸门（PROPOSED）：** 建包时做静态检查（只有单向端口且右端项为 0 的账户约束必须写成显式零约束）；每个网络在 HPC 上做一次全尺寸预处理作业（约 48 核、300 GB、3 h）。另外给出全年 F1、F2 的 HPC 诊断作业建议，未提交。
- **额度：** Gurobi 35/40 次，墙钟合计 3,433 s，其中 IIS 1,810 s；本机计算约 1.9 h；磁盘新增 14.2 GB。
- **事故：**
  - 第 14 次调用（`DualReductions=0`）在 ordering 阶段被 OOM 终止，照实计数。
  - F1_M01 第一次构建期间改了 `build.sh`，日志被截断，已改名留档并重建。
- **交付：** `research/06_scope_redesign/p1_v3_diag_20261105/`，包括 `V3_DIAG_REPORT.md`、`V3_DIAG_EVIDENCE.json`、`evidence/`、`scripts/`、指令及其 SHA256。镜像在 `work/p1_v3_diag_20261105/`。
