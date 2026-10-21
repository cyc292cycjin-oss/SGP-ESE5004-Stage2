# M12 进度（随进度更新）

- 指令：`M12_CLAUDE_CODE_INSTRUCTION.md` v1，SHA256 `4e0b05486e171b00922d9ac23c691802b4a375a40c4cb49b9165a3dac1183793`（与 `M12_INSTRUCTION_SHA256.txt` 一致，2026-10-21 核对）。
- 边界：不求解模型网络、不调用 Gurobi（含许可检查）、不连云；单元测试只用 scipy / HiGHS 解玩具 LP；不改模型、配置、网络与既有结果，只新增分析代码与文档。
- 工作树：`/home/jin/wt_m12_20261021`，分支 `codex/m12-allocation-20261021`（自 M08a 头 `820c2cae`，PR #45）。M08b 会话在另一 worktree（分支 `codex/m08b-demand-20261021`）并行。
- 被忽略输入：`research_inputs/finance_v5/{COUNTRY_WACC_PUBLIC_SOURCES,DISCOUNT_RATE_IN_USE}.csv` 已从 `/home/jin/wt_m080_20261020` 复制。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| 0 | 核对 SHA256、开 worktree、探查账本 / 导出 / 约束结构 | 完成 | — |
| C1（通用部分）+ C4.1–2 | `m12_allocation.py` 通用函数（所有者编码与 α、对偶形式 y'b、市场结算形式、核心 / 去一国 / SCRB / 比例规则）；`tests/research/test_m12_allocation.py` 玩具 3 国 LP（scipy HiGHS，7 passed） | 完成 | 见 git log |
| C1（网络部分） | `run`（复用 `s4d_ledger` 所有者规则；逐走廊组件成本与两端对偶结算；α 0 / 0.5 / 1、按长度、区间；B16；与现行账本逐实体对账；S4P 规则 (ii)(iii) 同比例对照）、`benefit`（受益 + 5 种比例权重）、`loo`（c′(i)、C1 (b) 阈值、不可分成本、SCRB）；冒烟网络测试（8 passed） | 完成 | 见 git log |
| C4.3（部分） | S4N 试点一体化 + S4O-6 不互联：B16 7.2e-9 / 6.5e-7；α 0.5 与账本偏差 ≤ 1.5e-5 EUR；与 S4P ASPECT8 表最大偏差 1.5e-13 bn；B6 69.243 bn；Owen 受益为负仅燃料舱（−1.215 bn） | 完成 | 见 git log |
| C2 | `m12_rhs_audit.py`：只构建 LP（`l23_violation_analysis.build_model`），逐族按右端项所有者分类、耦合行检测、Owen 对偶形式 y'b（导出数组或行对偶 + 驻点重建溢流列 RC）、市场形式 − 对偶形式的精确分解、去一国右端项比对。365×24h 一体化 9,017,345 行、构建 33–42 s、峰值 8.05 GiB；非零右端项无主 0 / 无法归属 0；唯一耦合 = 齐次 KVL；对偶形式闭合 −6e-5 bn；**市场形式 − Owen = KVL 回路转移（VN +0.26、LA −0.26 bn）**；11 国去一国结构检查全部通过（24 时段截断；VN 另在 365×24h） | 完成 | 见 git log |
| C3 | `m08a_run_batch.sh`：每个运行 C1 之后、GATES_V6 验收之前执行 `m12_allocation.py run --register` 与（有导出数组且 `M12_DUAL=1` 时）`m12_rhs_audit.py audit --register-dir`；level2 在 `batch_reference`（重评）之后、formal 在两情景都通过之后执行 `benefit`；`OUT/<tag>_minus<CC>/` 存在时执行 `loo`；钩子测试 + M08a 原测试 12 passed | 完成 | 见 git log |
| C4.3 | S4N 一体化 + S4O-6 不互联：受益对照补 Owen 对偶形式（VN 51.852 / LA 2.482 bn，市场形式 51.595 / 2.738） | 完成 | 见 git log |
| 证据补充 | 对偶形式 α 区间、玩具证据、全量测试 544 / 64 / 0（头 dbb63113） | 完成 | dd7d2efe |
| 交付 | `M12_REPORT.md`、台账 M12 条目、draft PR、审阅 ZIP | 完成 | 见 git log / PR |

## 接续点

全部子步已完成，按指令停止，等待审阅。工具脚本（WSL）：`/home/jin/m12_commit.sh`（镜像 + 提交，消息 `/home/jin/m12_msg.txt`）、`/home/jin/m12_c43.sh`（C4.3）、`/home/jin/m12_c2.sh`（C2：STEP=smoke | smoke_nc | full365 | dis365 | variants | loo365 | loo24）、`/home/jin/m12_loo_recompare.sh`、`/home/jin/m12_full_tests.sh`；去一国变体网络在 `/home/jin/m12_local/variants/`（未提交）。待决定事项见 `M12_REPORT.md` 第 6 节。
