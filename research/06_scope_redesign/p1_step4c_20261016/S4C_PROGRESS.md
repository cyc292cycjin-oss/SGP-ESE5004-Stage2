# S4C 进度记录（防中断用；每个子步骤提交后更新）

指令 `S4C_CLAUDE_CODE_INSTRUCTION.md`（v1，2026-10-16 21:50 SGT），开始前核对 SHA256 = `e1bad922b036bcb425cb9b77853e5cc4f9ca771c59c90da1a23321b89a1dcdd3`，与 `S4C_INSTRUCTION_SHA256.txt` 一致（2026-10-16，VERIFIED）。模型 Opus 5.5 xhigh。

分支 `codex/s4c-allocation-fixes-20261016`，自 S4B 最终提交 819ade64 开出（已核实 = PR #26 的 headRefOid `819ade64b79114c97cf49e5af16b43c42dddf356`）；draft PR 叠在 #26 上（基分支 `codex/s4b-fixes-calibration-20261016`）。
仓库 `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`；交付目录 `research/06_scope_redesign/p1_step4c_20261016/`，镜像 `D:\ResearchWorkspaces\ASEAN\work\p1_step4c_20261016\`。
求解环境：`/home/jin/miniforge3/envs/pypsa-earth/bin/python`，`PYTHONHASHSEED=0`，Gurobi 12.0.3（`GRB_LICENSE_FILE=/home/jin/gurobi.lic` 只读引用）；止损：56×3h 单次 30 分钟、非最优即停不重试（例外：S4C-5 的 B 档 crossover 诊断，S4C-6 不互联主算非最优时停下报告后跑诊断）。
资源（第 7 条）：只允许两类下载——(1) CO₂ 船运与海外封存成本公开文献（第 89 项）；(2) 分国融资成本公开数据或报告（第 90 项）；总量 ≤ 300 MB，单个 > 50 MB 先报告；其他下载、本机单次计算 > 1 h 或 > 约 8 GiB、任何云端操作，先报告。
决策清单原文：本机（D:\ 工作区与 WSL 仓库）未找到决策清单文件；按指令逐项摘要执行（与 S4B 相同情形）。

## 子步骤状态

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| S4C-0 | 化石燃料价格改 STEPS（第 85 项）；小项（第 86 项）；折现率（第 90 项） | 完成 | 见下一提交（S4C-0） | `research.fuels.price_scenario: steps`（气 27.07、油 35.32、煤 8.86 EUR2020/MWh；NZE 13.67/11.62/5.17 低价敏感性；CPS 可选）；构建时断言三燃料同一情景且网络价格 = 登记值（`s4c_layers.check_fuel_prices`）；褐煤保持成本层 6.62（WEO 无褐煤价）；BtL 投资 × 效率 113,726（PyPSA-Eur 4230–4231 行，S4B 写的 4227–4228 更正）；4 个 gate4 测试改断言已接受状态；折现率盘点（成本层 0.07，屋顶光伏等 8 行 0.04，存量无年金）；`research.finance.wacc_mode: uniform`，`country_specific` 只实现（IEA 资本成本观察站分国值为名义税后本币，11 国模型实际值全部 DATA_PENDING）；三个构建静态 PASS（各 43 s、0.69 GiB）；`tests/research` 439 通过 / 0 失败 |
| 补充 01 | 走廊海底份额与走廊成本（台账 L18，第 16 项），作为 S4C-1 第 5 条 | 未开始 | — | 补充 SHA256 `e0bc1743…a8340a` 核对一致（2026-10-16 约 22:00） |
| S4C-1 | 风光候选成本改用第 50 项成本层；全组件成本审计（第 82 项） | 未开始 | — | |
| S4C-2 | 水电入流诊断与重新归一（第 83 项） | 未开始 | — | |
| S4C-3 | 国际燃料舱归属（第 88 项） | 未开始 | — | |
| S4C-4 | 东盟外 CO₂ 封存选项（第 89 项） | 未开始 | — | |
| S4C-5 | 基尔霍夫行归一化与求解设置对比（第 84 项） | 未开始 | — | |
| S4C-6 | 冒烟与云端部署包（只准备） | 未开始 | — | |
| 交付 | S4C_REPORT.md、S4C_EVIDENCE.json、DOWNLOAD_LIST.csv | 未开始 | — | |

## 续行点

S4C-0 完成并提交；下一步 S4C-1（风光候选成本 → 第 50 项成本层；全组件审计；补充 01 走廊海底份额作为第 5 条）。

## 用户中途指示

1. 2026-10-16 约 22:00 SGT：追加 `S4C_SUPPLEMENT_01.md`（走廊海底份额与走廊成本，台账 L18，落实第 16 项），先核对 SHA256 与 `S4C_SUPPLEMENT_01_SHA256.txt`（e0bc1743…a8340a）一致——已核对一致（VERIFIED）；作为 S4C-1 第 5 条执行；海底份额结果不合理或形状不足以判定时停下报告。

## 下载登记（第 7 条，第 2 类：分国融资成本）

| 文件 | 来源 | 字节 | SHA256 | 取得时间（UTC） |
|---|---|---|---|---|
| `IEA_CoC_Observatory_dashboard_2025.html` | https://www.iea.org/reports/cost-of-capital-observatory/dashboard-2 | 305,280 | 942a5613…59d3a | 2026-10-16T13:57:17Z |
| `IEA_commentary_SEA_cost_of_capital_20251008.html` | https://www.iea.org/commentaries/high-cost-of-capital-and-limited-project-pipeline-hinder-clean-energy-investment-in-southeast-asia | 270,294 | a9ae6970…38a9f1d | 2026-10-16T13:57:17Z |
| IRENA 2023《The cost of financing for renewable power》PDF | irena.org（HTTP 403）、apren.pt 镜像（404） | — | 未取得 | 2026-10-16 |

累计下载 0.58 MB（上限 300 MB）。
