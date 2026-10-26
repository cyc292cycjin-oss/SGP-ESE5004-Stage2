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
| F6.2 运行计划 / 运行脚本 | 完成 | `896828fd`、`5405e477` | `RUN_PLAN_DFX.md`（896828fd）；`scripts_project/dfx_batch.py`、`cloud_package_dfx/run_dfx.sh` / `preflight_dfx.sh` / `make_package_dfx.sh`、`BATCH3_REFERENCE_VALUES.json`、`tests/research/test_dfx_runner.py`（14 passed） |
| F6.3 包 v8 与干跑 | 完成（第二次构建） | （阶段 3 提交：证据） | 首次：干跑 `results_project/dfx_v3/dry_run_v8/`（完整 365×24h BUILD_ONLY：V1 LP 9.98M×4.48M，10.16 GiB；V2 9.63M×4.33M，9.96 GiB；截短 56；11 项拒绝 exit 2）与包（提交 5405e477，20 文件 148,208,096 B）→ 因 `dfx_batch.py` 导入副作用修复而重做：干跑 `dry_run_v8b/` + 包重建于修复提交（旧包保留为 `cloud_package_dfx_superseded_5405e477/`）；本机预检 guards/sha/networks/env/profile/code/tools OK（resources 本机失败属预期；licence 节未跑） |
| F6.1 全量测试 | 完成 | `17441b20` | **最终 702 passed / 67 skipped / 0 failed**（去除会话的 `results_project/s1` 链接、F0.3 测试范围修正后）。此前：第一次全量测试 32 个失败（第三批 / B4P 替身测试；原因 `dfx_batch.py` 首版在导入时改写 `m10_batch3_summary` 常数）→ 修复后受影响测试文件同进程重跑 + 全量测试重跑；`results_project/dfx_v3/tests/{affected,full}.log` |
| 阶段 1 报告 | 完成 | （阶段 3 提交） | `DFX_REPORT_PHASE1.md`（附录 A = `DFX_RULES.md` 原文）+ `DFX_EVIDENCE.json`；证据副本 `evidence/{smoke,dry_run,package,tests,leak_scan}` |
| 阶段 2 | 完成 | `5405e477` | `hpc_package_dfx/`（PROPOSED）+ `DFX_REPORT_PHASE2.md` |
| 阶段 3 | 完成 | `f73f5c06`、`17441b20`、`d9f8da84`、（P10 提交） | `PRE_AUTODL_CHECKLIST.md`：P1–P5、P7–P11 PASS，P6 PASS（有保留 R1：键名字面量只在 grep 模式 / 版本号误报，请用户确认）；`DFX_REPORT_PHASE3.md`；分支已推送（远端头 = 本地头）。R1 已由用户接受（2026-10-27）→ 检查单全部 PASS、可以租机。**已停下，等待用户租好 AutoDL、在会话中给出连接方式并说"授权阶段 4"** |

续跑说明：如本会话中断，从上表第一个"进行中 / 待做"步骤继续；已提交的内容以 git 历史为准；`results_project/dfx_v3/*/STATUS.txt` 记录各运行的进度。
