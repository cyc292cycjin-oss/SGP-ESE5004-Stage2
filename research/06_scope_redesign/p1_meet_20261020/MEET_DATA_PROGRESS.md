# MEET-D 进度文件（面谈材料附件 B「数据清单」底稿；只读，不求解）

- 指令 `MEET_DATA_CLAUDE_CODE_INSTRUCTION.md` SHA256 `e006d32f74ab390a0b2409242bd239ff99b0b0456f2a991af4977e8bf7ae3165`，与 `MEET_DATA_INSTRUCTION_SHA256.txt` 一致（2026-10-20 核对）。
- 只读：未求解、未连云、未调用 Gurobi、未改模型 / 配置 / 注册表 / 既有结果；未提交、未开分支；文件只写在本目录。结束时核对：仓库主检出 `git status` 与开始时相同（只有原有的 3 个未跟踪源文件与 `work/`），S4R 工作树干净，`work/` 下本目录以外无新文件。
- 资源：本机只读计算合计 < 5 分钟；临时文件（注册表只读导出副本、检查脚本）在会话临时目录，不属交付。

## 子步骤

| 步 | 内容 | 状态 | 说明 |
|---|---|---|---|
| D0 | 核对 SHA、定位仓库注册表最新版本 | 完成 | 见下 |
| D1 | 读资料（注册表、S4R、S4P、下载目录、决定 126 / 129） | 完成 | 注册表 1,962 行逐行归类（25 个数据类 + 3 个非数据类），无遗漏 |
| D2 | 统计（实算） | 完成 | `evidence/MEET_DATA_STATS.json` |
| D3 | 表 1–4 底稿 | 完成 | 表 1 25 行、表 2 34 行、表 3 35 行、表 4 42 行 |
| D4 | 不一致项与注册表缺口 | 完成 | 不一致项 9 项、缺口 7 项（只列出，不修正） |
| D5 | 生成 xlsx / md | 完成 | 见“交付” |

## D0 记录

- 注册表：仓库 `research_inputs/registry_v5/DATA_REGISTRY.csv`。S4O / S4P / S4Q / S4R 四个分支头上内容相同（SHA256 `46e234d79ec4fbc824c5c4e416591525bec11b46dbdbceb4d4512f2f31922e50`），最后修改于 `87e28e3b`（S4O 补充 01）。以最新分支 `codex/s4r-unification-plan-20261020` 头 `cefab870` 为准；生成脚本用 `git show` 只读读取并校验 SHA256。未使用 `work/` 或 `research/06_scope_redesign/p1_step2–4` 下的旧副本。
- `data_registry/`：仓库中无此目录；D 盘工作区 `data_registry/` 只有 `buildings_phase3a4/`（第三阶段建筑数据模板），与当前主算无关。

## 统计结果（实算，VERIFIED）

- 注册表 1,962 行、15 列；等级 A 263（13.4 %）/ B 1,220（62.2 %）/ C 479（24.4 %）。
- 状态：REGISTERED 1,071、REFERENCE_ONLY 534、SOURCE_ZERO 132、SENSITIVITY 128、DATA_PENDING 51、CANDIDATE_ONLY 35、ZERO_BY_DECISION 11。
- 主算输入（数据类 T01–T25 × 状态 REGISTERED / SOURCE_ZERO / ZERO_BY_DECISION）1,185 行：A 11.73 %、B 59.32 %、C 28.95 %；C 级 343 行中生物质 197 行。对照口径：含非数据类 1,214 行（A 11.45 / B 60.3 / C 28.25 %）；仅 REGISTERED 1,042 行（A 10.84 / B 59.5 / C 29.65 %）。
- 11 国完全同口径：S4R 核查表 19 类中 9 类（47.4 %；209 格标出 64 格，与 S4R 自报一致）；本清单表 1 的 25 类中现行 18 类（72.0 %）、修正后 17 类（68.0 %）。
- S4R 拟增 / 改注册表行 42 行：add 26、modify 15、列错位 1；非 add 而注册表无同名行 7 行。

## 不一致项（摘要；全文见 `DATA_INVENTORY.md` §I）

1. LNG 分国进口上限：注册表 `lng_import_cap_*` 按 2.5 × 存量（VN 133.33、ID 391.67、KH 0、PH 490.00 TWh/a），S4R 表中模型上限 VN 278.67、ID 422.33、KH 14.67、PH 510.00。
2. 海上风机型 / 尾流：注册表主变体已是 NREL 2020ATB 5.5 MW + 0.8855，S4R 把“NREL 5 MW、无尾流”写为现状。
3. GEM LNG 版本：注册表 2025-09，S4R 记 2025-08（数值一致）。
4. 航运密度栅格：`work/p2_data_intake/raw12/shipdensity_global.zip` 已在盘上，SHA256 `7d103de5…9248` 与注册表一致（本步只读核实）；注册表另一行仍为 DATA_PENDING，S4R 下载清单 A1 仍列为必需。
5–9. natura 栅格状态、成本层双“主算”、KH / TL 封存等级、REGISTRY_ROWS_PROPOSED 列错位与 modify 目标缺失、台账计数。

## 待用户决定 / 确认（本步不处理）

- 不一致项 4：A1 是否仍需下载（raw12 文件是否即同一数据集）。
- 不一致项 1、2：M08 写入注册表时，LNG 分国上限与海上风“现状”以哪一边为准。
- 不一致项 8：REGISTRY_ROWS_PROPOSED 的 7 行 action 需改为 add 或指明被修改的行。

## 交付（`work/p1_meet_20261020/`）

| 文件 | SHA256 | 说明 |
|---|---|---|
| `DATA_INVENTORY.xlsx` | `d0436436380d45e98858beaff72b92068f339b2ba442ec14a1534b9f775acfb6` | 5 张表：说明与统计（含不一致项、缺口）、表 1–4；列名中文，来源名保留原文。重新生成时文件内时间戳会变，哈希随之改变 |
| `DATA_INVENTORY.md` | `4199354ea0b93f05afc66135dcbcecd5ed14d98ba60bef3018452ad7d3891528` | 同内容，供审阅端阅读 |
| `evidence/MEET_DATA_STATS.json` | `5651c74f83b328220be6e92528055f07a0840b9573d635792cca638f0271b68f` | 实算统计 |
| `scripts/meet_data_inventory.py` | `430b5185f83d7992953c2d961b5fb4f199ae27fc00c5b22e10dc08d136892a0c` | 生成脚本（只读；WSL pypsa-earth 环境 `python -I`） |
| `MEET_DATA_PROGRESS.md` | — | 本文件 |

- 指令只要求上述文件写在本目录，因此未写台账条目、未打审阅 ZIP。

## 续行点

全部完成；停止，等待审阅。若需修改：改 `scripts/meet_data_inventory.py` 中的表格正文后重跑即可（统计与等级列自动重算）。
