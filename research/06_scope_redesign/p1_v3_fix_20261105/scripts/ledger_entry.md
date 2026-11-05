
### V3.1 FIX（第 195 项：燃料舱约束修正与重新打包；本机，Gurobi 4 / 6）— 2026-11-05

- **范围：** `V3_FIX_INSTRUCTION.md` v1，SHA256 f8ba88a2…a5aa，已核对一致；开始条件由用户确认。分支 `codex/v3-fix-20261105`（自部署包提交 `7d22dda1`），worktree `/home/jin/wt_v3_fix`。网络、成本、档案、时限、walltime、资源、验收阈值、预测、Owen 规则都没有改。
- **修正（`ae849e1e`）：** `s4c_layers.install_bunker_net_zero` 由"账户末时段水平 ≤ 0"的零松弛行改为"每条计量链路每个时段 `Link-p` = 0"，约束名不变；`validate_bunker_account` 对等价性前提逐项断言（系数 > 0 含时变、无移除端口、计量 `p_min_pu ≥ 0` 含时变、账户初值 0 / 非循环 / 无损耗、权重 > 0）。四个网络全年实测全部满足（82 个端口，系数 0.2571）。
- **下游：** Owen 分摊的任何参与者都不依赖原标量对偶（右端项 0）；Owen 审计行所有者仍为 BUNKER，C1 与违反量表保持原名称规则；`NODAL_PRICES.csv` 与 `nodal_prices_summary.csv` 中 `co2 bunkers ASEAN` 行（原为燃料舱 CO₂ 影子价格，新写法下恒为 0）置 NaN 并加说明，没有构造替代量。
- **静态零松弛检查（新 `zero_slack_check.py`，打包闸门）：** F1–F4 全部通过——11 国净零行都有移除端口；7 行封存上限为正；LA、MM、SG、TL 封存上限 0 但没有封存账户；19 行年度产量上限为正；燃料舱为显式逐变量形式，覆盖 82 × 全部时段。
- **本机验证（VERIFIED）：** 失败窗口 F1_M01、F2_M02 在新代码上预处理通过（诊断时 INF_OR_UNBD），LP 行恰好多 82 × 时段数 − 1。56×3h 回归按 HPC 冒烟作业体本机演练（运行器 split 路径）：`SMOKE_RESULT:PASS`，目标相对差 2.45e-9 / 5.83e-10，12 个参与者 Owen 受益符号不变、最大差 17,757 EUR，各国台账最大差 14,288 EUR，B6 差 609 EUR；迭代多 20–23 %、work units 多 19–41 %（不改登记值，第 15 节须知）。
- **测试：** 新测试 22 项；全量 @64aea2e3 855 通过 / 5 失败（4 项 = V14 基线；1 项 `test_dfx_demand::test_f0` 由新文件触发，已修，`13ebce95`）；bash 4.2 替身测试 43 项通过；最终提交上的全量见报告第 7.1 节。
- **v3.1 包：** `work/p1_v3_20261102/hpc_package_v3_1/`，COMMIT `d3b9a3bc`，`SHA256SUMS` 的 SHA256 `b8216361…be1ee`，49 个文件 374.5 MB，一致性 60 / 60，运行目录 `runs/batch5` / `runs/smoke56_v31`，上传到新目录 `/hpctmp/$USER/hpr31/`（v3 的 `hpr3/runs/batch4` 停批记录不动）；干跑 bash 5 与 4.2 都通过；`RUN_PLAN_HPC_V3.md` 第 15 节与 v3.1 操作指南在任何 v3.1 HPC 求解之前提交；可选脚本 `hpc_v31/fullsize_presolve.sh`（未运行）。
- **交付：** `research/06_scope_redesign/p1_v3_fix_20261105/`（报告 `V3_REPORT_FIX.md`、证据、脚本、指令及其 SHA256），镜像 `work/p1_v3_fix_20261105/`；最终状态见 `work/p1_v3_20261102/V3_HPC_PROGRESS.md` 最后一行。不连 HPC、云、VPN，未上传。
