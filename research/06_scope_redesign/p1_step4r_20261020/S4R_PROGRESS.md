# S4R 进度文件（第 126、128 项：统一修正方案与门槛重设；只读、不实施、不求解）

- 指令 `S4R_CLAUDE_CODE_INSTRUCTION.md` SHA256 `f80da6fd…ceeb`，与 `S4R_INSTRUCTION_SHA256.txt` 一致（2026-10-20 核对）。
- 分支 `codex/s4r-unification-plan-20261020`（自 S4P 头 69b67a97），独立工作树 `/home/jin/wt_s4r_20261020`；draft PR 叠在 #42 上（待建）。
- 只读：不求解、不连云、不调用 Gurobi、不改生产代码 / 注册表 / 网络 / 结果。分析脚本在 `scripts/`。

## 子步骤

| 步 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| R0 | 核对 SHA、读资料、开分支与工作树、进度文件 | 进行中 | — | |
| R1 | 需求重新锚定（F4） | 待做 | — | 三类分解；主锚 / 对照；工业产量；路线；变体；`DEMAND_ANCHOR_COMPARISON.csv` |
| R2 | 可再生潜力（F1、F9） | 待做 | — | 布局参数对照；ESMAP / Zhong / iScience；`POTENTIAL_COMPARISON.csv` |
| R3 | LNG（F2、F12） | 待做 | — | GEM / GIIGNL；7,018 出处；2.5× 去留；`LNG_CAPACITY_COMPARISON.csv` |
| R4 | 生物质溢出（F5） | 待做 | — | PyPSA-Eur 做法；统一规则 |
| R5 | CO₂ 封存（F10） | 待做 | — | `CO2_STORAGE_UNIFIED.csv` |
| R6 | 成本与货币（F14、核电、F7 准备） | 待做 | — | `COST_CURRENCY_FIXES.csv`、`COUNTRY_WACC_SENSITIVITY_TABLE.csv` |
| R7 | "不互联"定义（F11） | 待做 | — | 注册表行草案 |
| R8 | 门槛重设（第 128 项） | 待做 | — | `GATES_V6.md` 先单独提交，再重评 `GATES_RETRO_COMPARISON.*` |
| R9 | 统一性核查表 | 待做 | — | `UNIFICATION_CHECKLIST.csv/.md` |
| R10 | 影响估算与实施计划 | 待做 | — | `IMPLEMENTATION_PLAN.md` |
| RR | `S4R_PLAN.md`、`REGISTRY_ROWS_PROPOSED.csv`、`S4R_EVIDENCE.json`、来源清单、PR | 待做 | — | |

## 续行点

R0 进行中：工作树已建，正在读取下载清单、S4Q 报告、第 124–128 项决定、PyPSA-Eur 代码副本与 V5 门槛定义。
