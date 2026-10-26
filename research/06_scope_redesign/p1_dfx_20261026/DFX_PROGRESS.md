# DFX v3 进度（续跑点）

指令：`DFX_CLAUDE_CODE_INSTRUCTION.md` v3，SHA256 `b60da4c664c316c6bdbfe53f52908351a08b2eca94fdd7f7e735558f2685a6df`（核对一致，2026-10-26 21:33 SGT）。
分支 `codex/dfx-v3-20261026`（从 `codex/b4-prep-20261026` 本地头 `55ab07c0`），worktree `/home/jin/wt_dfx_v3_20261026`，中间结果 `results_project/dfx_v3/`（主检出），辅助脚本 `/home/jin/dfx3/`（镜像 `scripts/wsl_dfx3/`）。
本机 Gurobi 调用：0 / 2（本指令）；暂停会话 0。本机计算用时与磁盘见各步。

| 步骤 | 状态 | 提交 | 说明 |
|---|---|---|---|
| 第 0 节 遗留检查 | 完成 | （本提交） | `SECTION0_LEFTOVERS.md`；无进程、无 Gurobi 调用；分支 / worktree / `/home/jin/dfx` 原样保留 |
| 基分支核对 | 完成 | | 11 个差异文件均与需求构建无关（`SECTION0_LEFTOVERS.md` 第 6 节） |
| F0 代码地图 | 完成 | （F1–F4 提交） | 追踪：v1 重建 ×2（69 s / 0.78 GB 各）、`--stop-before-solve` 与 `--split-stage build`（56 时段）、56 时段后处理链（violations / C1 / M12 / Owen / 账本重做 / GATES_V6 / stop-class）、数据链 → `results_project/dfx_v3/f0_trace/modules.jsonl`；`CODE_MAP.md`、`CODE_MAP_TABLE.csv`、`CODE_MAP_DATA.json` |
| DFX_RULES.md | 完成 | `834a0f19` | 在任何 v2 构建之前提交；`DFX_RULES_NUMBERS.json` = 原型数值 |
| F1–F4 | 完成 | （本提交） | 代码：`m08b_demand.py`（RAS、NEU、氨产量、NEU 气扣除）、`s3_0_industry.py`（氨替换）、`s2_layers.py` / `s2b_feedstock.py` / `d1_common.py`（HVC 范围）、`dfx_data.py`（新）、`d1_registry.py`、`m08b_data.py`（更正基表排除 dfx 片段）、`configs/research/baseline.yaml`；数据链重跑；注册表 2,194 → 2,280 行；测试 `test_dfx_demand.py`（新）+ `test_m08b_demand.py` 改 3 处；子集 126 passed / 9 skipped |
| F5 | 待做 | | |
| F6 | 待做 | | |
| 阶段 1 报告 | 待做 | | |
| 阶段 2 | 待做 | | |
| 阶段 3 | 待做 | | |

续跑说明：如本会话中断，从上表第一个"进行中 / 待做"步骤继续；已提交的内容以 git 历史为准；`results_project/dfx_v3/*/STATUS.txt` 记录各运行的进度。
