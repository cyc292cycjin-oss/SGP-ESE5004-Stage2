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
| C2 | `scripts_project/m12_rhs_audit.py` + 365×24h 只构建 LP | 未开始 | — |
| C3 | 第三、四批运行脚本接入 | 未开始 | — |
| C4.3 | S4N 一体化 + S4O 不互联流程跑通 | 未开始 | — |
| 交付 | `M12_REPORT.md`、台账、draft PR | 未开始 | — |

## 接续点

（每个子步提交后更新。）
