# DFX v3 进度（续跑点）

指令：`DFX_CLAUDE_CODE_INSTRUCTION.md` v3，SHA256 `b60da4c664c316c6bdbfe53f52908351a08b2eca94fdd7f7e735558f2685a6df`（核对一致，2026-10-26 21:33 SGT）。
分支 `codex/dfx-v3-20261026`（从 `codex/b4-prep-20261026` 本地头 `55ab07c0`），worktree `/home/jin/wt_dfx_v3_20261026`，中间结果 `results_project/dfx_v3/`（主检出），辅助脚本 `/home/jin/dfx3/`（镜像 `scripts/wsl_dfx3/`）。
本机 Gurobi 调用：2 / 2（本指令；F5.5 冒烟 2026-10-26 14:58 与 15:14 UTC，间隔 333 s；之后不得再调用）；暂停会话 0。本机计算用时与磁盘见各步。

| 步骤 | 状态 | 提交 | 说明 |
|---|---|---|---|
| 第 0 节 遗留检查 | 完成 | （本提交） | `SECTION0_LEFTOVERS.md`；无进程、无 Gurobi 调用；分支 / worktree / `/home/jin/dfx` 原样保留 |
| 基分支核对 | 完成 | | 11 个差异文件均与需求构建无关（`SECTION0_LEFTOVERS.md` 第 6 节） |
| F0 代码地图 | 完成 | （F1–F4 提交） | 追踪：v1 重建 ×2（69 s / 0.78 GB 各）、`--stop-before-solve` 与 `--split-stage build`（56 时段）、56 时段后处理链（violations / C1 / M12 / Owen / 账本重做 / GATES_V6 / stop-class）、数据链 → `results_project/dfx_v3/f0_trace/modules.jsonl`；`CODE_MAP.md`、`CODE_MAP_TABLE.csv`、`CODE_MAP_DATA.json` |
| DFX_RULES.md | 完成 | `834a0f19` | 在任何 v2 构建之前提交；`DFX_RULES_NUMBERS.json` = 原型数值 |
| F1–F4 | 完成 | （本提交） | 代码：`m08b_demand.py`（RAS、NEU、氨产量、NEU 气扣除）、`s3_0_industry.py`（氨替换）、`s2_layers.py` / `s2b_feedstock.py` / `d1_common.py`（HVC 范围）、`dfx_data.py`（新）、`d1_registry.py`、`m08b_data.py`（更正基表排除 dfx 片段）、`configs/research/baseline.yaml`；数据链重跑；注册表 2,194 → 2,280 行；测试 `test_dfx_demand.py`（新）+ `test_m08b_demand.py` 改 3 处；子集 126 passed / 9 skipped |
| F5.1–F5.4 构建 / 等价 / 复核 / 一阶预测 | 完成 | （本提交） | v2 四个网络在 `72083fde`（dirty 0）构建到 `results_project/dfx_v3/builds_v2/`（365×24h：一体化 `82928a4c…`、不互联 `5c75bfa0…`）；v1 同路径重建 = 登记网络（仅 meta 路径不同）；等价测试 4 个网络通过（差异只在负荷、过程排放源与随负荷增减的需求侧组件）；复核 `scripts/review/dfx_demand_review.py`：v1 7,147.6 → v2 7,628.6 TWh（+481.0），分解桥闭合残差 1.6e-10 TWh（修正 D1 表农业 gas 载体漏项 1.21 GWh 后）；一阶预测 ΔB6 +3.060 bn EUR（`DFX_FIRST_ORDER.md`）；`RUN_PLAN_DFX.md` 在任何 v2 求解前登记；子集 131 passed / 4 skipped |
| F5.5 本机冒烟（2 次 Gurobi） | 完成 | （F6 提交） | `scripts/wsl_dfx3/smoke_v2.sh` 于提交 `896828fd`（dirty 0）：56 时段截短 v2 一体化 optimal（620 s，6.99 GiB，目标 3.4066e11）→ 间隔 333 s → 不互联 optimal（727 s，5.52 GiB，3.5209e11）；违反量 / C1 / M12 / Owen / 批参照 / 重评 / GATES_V6（均 ACCEPTED_LAYER2，登记 SHA = 2920×3h 网络）/ 分级（accepted）/ B6 全部 exit 0；`results_project/dfx_v3/smoke_v2/SMOKE_SUMMARY.json`。**本机 Gurobi 调用 2 / 2 已用完** |
| F6 | 待做 | | |
| 阶段 1 报告 | 待做 | | |
| 阶段 2 | 待做 | | |
| 阶段 3 | 待做 | | |

续跑说明：如本会话中断，从上表第一个"进行中 / 待做"步骤继续；已提交的内容以 git 历史为准；`results_project/dfx_v3/*/STATUS.txt` 记录各运行的进度。
