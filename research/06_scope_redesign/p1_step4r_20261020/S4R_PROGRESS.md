# S4R 进度文件（第 126、128 项：统一修正方案与门槛重设；只读、不实施、不求解）

- 指令 `S4R_CLAUDE_CODE_INSTRUCTION.md` SHA256 `f80da6fd…ceeb`，与 `S4R_INSTRUCTION_SHA256.txt` 一致（2026-10-20 核对）。
- 分支 `codex/s4r-unification-plan-20261020`（自 S4P 头 69b67a97），独立工作树 `/home/jin/wt_s4r_20261020`；draft PR 叠在 #42 上。
- 只读：未求解、未连云、未调用 Gurobi、未改生产代码 / 注册表 / 网络 / 结果。分析脚本在 `scripts/`（只读导出与已下载文件）。
- 资源：本机计算合计 < 10 分钟；下载仅用户已放入 `p1_s4r_downloads_20261020/` 的文件（Copernicus 栅格 zip 未解压、未使用）；持久临时目录 `/home/jin/s4r_tmp/`（约 60 MB 文本 / 表格抽取，可删）。

## 子步骤

| 步 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| R0 | 核对 SHA、读资料、开分支与工作树、进度文件 | 完成 | 4fbddf28 | |
| R1 | 需求重新锚定（F4） | 完成 | 4fbddf28 | `DEMAND_ANCHOR_COMPARISON.csv/.md`、`evidence/R1_SUMMARY.json`；方案在 `S4R_PLAN.md` §2 |
| R2 | 可再生潜力（F1、F9） | 完成 | 4fbddf28 | `POTENTIAL_COMPARISON.csv/.md`、`evidence/SOLARGIS_ESMAP_2020_ASEAN11.csv`、`evidence/R2_POTENTIALS.json`；F9 观测 CF DATA_PENDING |
| R3 | LNG（F2、F12） | 完成 | 4fbddf28 | `LNG_CAPACITY_COMPARISON.csv/.md`、`evidence/GEM_GGIT_LNG_IMPORT_TERMINALS_2025-09_ASEAN11.csv`、`evidence/R3_LNG.json`；7,018 来源 DATA_PENDING |
| R4 | 生物质溢出（F5） | 完成 | 收尾提交 | 文字方案 `S4R_PLAN.md` §5 |
| R5 | CO₂ 封存（F10） | 完成 | 4fbddf28 | `CO2_STORAGE_UNIFIED.csv/.md` |
| R6 | 成本与货币（F14、核电、F7 准备） | 完成 | 4fbddf28 | `COST_CURRENCY_FIXES.csv/.md`、`COUNTRY_WACC_SENSITIVITY_TABLE.csv/.md` |
| R7 | "不互联"定义（F11） | 完成 | 收尾提交 | 文字方案 `S4R_PLAN.md` §8；注册表行草案在 `REGISTRY_ROWS_PROPOSED.csv` |
| R8 | 门槛重设（第 128 项） | 完成 | d45955ea（定义）；收尾提交（重评） | `GATES_V6.md` + `GATES_V6_SHA256.txt` 先单独提交；之后 `scripts/s4r_r8_retro.py` 只读导出指标重评 20 个历史运行 → `GATES_RETRO_COMPARISON.csv/.md`；未因重评结果修改定义 |
| R9 | 统一性核查表 | 完成 | 收尾提交 | `UNIFICATION_CHECKLIST.csv/.md`（`scripts/s4r_r9_checklist.py`） |
| R10 | 影响估算与实施计划 | 完成 | 收尾提交 | `IMPLEMENTATION_PLAN.md`；影响表在 `S4R_PLAN.md` §11.1 |
| RR | `S4R_PLAN.md`、`REGISTRY_ROWS_PROPOSED.csv`、`USER_DOWNLOAD_LIST.md`、`EXTERNAL_SOURCES_S4R.md`、`S4R_EVIDENCE.json`、PR | 完成 | 收尾提交 | 提交 SHA 与 PR 链接见下节 |

## 提交与 PR

- 4fbddf28：R0 + R1 / R2 / R3 / R5 / R6 对照表与脚本。
- d45955ea：仅 `GATES_V6.md` 与其 SHA256（`5c0aa8b8ed322b75a63879fccfc19559606a0ad743ecafee3addfcbfe04fd7f9`），先于重评。
- 收尾提交与 PR：见本文件末尾"收尾记录"（提交后补写）。

## 续行点

全部子步骤完成；待审阅。若需续行：先读 `S4R_PLAN.md` 摘要与 §11 两张清单，再按 `IMPLEMENTATION_PLAN.md` M08 顺序在新分支实施（需用户逐项决定）。

## 收尾记录

- 收尾提交 d0c299a9（方案、重评、核查表、实施计划、注册表行、来源、证据、进度）；draft PR #43：https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/43（base `codex/s4p-country-audit-20261020`）。
- 台账条目 `evidence/LEDGER_ENTRY_S4R.md` 追加到 `research/STAGE2_PROJECT_LEDGER.md`；PR 正文 `evidence/PR_BODY_S4R.md`。
- `S4R_EVIDENCE.json` 的输出哈希在本记录与台账追加之前生成（`S4R_PROGRESS.md` 的哈希对应收尾前版本）。
- 状态：全部交付完成，停止，等待审阅。

## 补充 01（第 129 项，2026-10-20）

- `S4R_SUPPLEMENT_01.md` SHA256 `c533c960…4984`，与 `S4R_SUPPLEMENT_01_SHA256.txt` 一致（核对后执行）。仍只读：未求解、未连云、未调用 Gurobi、未改生产代码与注册表。

| 节 | 内容 | 状态 | 产出 |
|---|---|---|---|
| §1 | R1.3 产量规则 11 国同一（min(增长, 人均, 规划上限)；规划只作上限）；基年 2024（worldsteel WSIF 2025；USGS MCS 2025 ID / VN，其余 USGS 年鉴 DATA_PENDING 过渡值）；弹性 0.5 与饱和 1.0 / 0.6 登记为假设（C 级，敏感性 0.3–0.8、0.6–1.2 / 0.4–0.8） | 完成 | `scripts/s4r_r1_demand_anchor.py`、`DEMAND_ANCHOR_COMPARISON.csv/.md` §4、`S4R_PLAN.md` §2.3；VN 水泥 107.0、钢 40.7（原 70 撤销） |
| §2 | 只锚活动量：基础负荷 = ATS 国家电力 × 建筑 + 农业份额（11 国 1,032 → 966 TWh，全部非负；居民校验 428 vs 386 TWh）；工业电力内生；交通服务量锚（模型 / 锚 1.1–3.2） | 完成 | 同上 §2–3；`IMPLEMENTATION_PLAN.md` M08-5 改写 |
| §3 | R2 主算只改密度（× 1.109，不重算栅格）；开阔林转上界敏感性；比值分解（密度 6–18 %，保护区 ≤ 17–84 %，林地 + 其他 ≥ 33–71 %）；触发规则；下载清单分组（Copernicus / WDPA / GEBCO / EEZ 已在作者缓存，原第 1 项撤销；航运密度为主算必需 A1） | 完成 | `scripts/s4r_r2_potentials.py`、`POTENTIAL_COMPARISON.csv/.md`、`IMPLEMENTATION_PLAN.md` M08-7 与 §2.1、`USER_DOWNLOAD_LIST.md` |
| §4 | 保持 k = 10；`GATES_V6.md` 未改（SHA256 不变） | 完成 | `GATES_V6_NOTES.md`（新建）；`S4R_PLAN.md` §9 |
| §5 | VN 封存上限下调后的船运交互（130 Mt/a 改道，+1.9–2.0 bn/情景；不互联 VN 船运约 225 Mt/a；若船运算互联 +5.5 bn） | 完成 | `S4R_PLAN.md` §8；注册表行 `co2_storage_vn_shipping_interaction` |
| §6 | 面谈清单合并为 9 项；用户待办精简为 2 项 | 完成 | `S4R_PLAN.md` §11.2–11.3 |
| §7 | 交付文件更新、`REGISTRY_ROWS_PROPOSED.csv`（31 → 42 行）、`UNIFICATION_CHECKLIST`（209 格，64 标出）、`EXTERNAL_SOURCES_S4R.md`（+12 条）、`S4R_EVIDENCE.json` 重生成 | 完成 | 提交与 PR #43 正文更新见"收尾记录（补充 01）" |

- 本机计算 < 5 分钟；检索：Bleischwitz 2018、Pauliuk 2013、van Ruijven 2016、Global Cement、worldsteel 人均表、USGS MCS 2025（pypdf 解析）、World Bank WDI API；USGS 年鉴章节四种 URL 404、worldsteel SSY 2024 PDF 404（登记 DATA_PENDING）。
