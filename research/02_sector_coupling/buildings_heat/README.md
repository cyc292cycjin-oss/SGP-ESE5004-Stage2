# Phase 3A-1 · Buildings + Heat audit

日期：2026-10-01。结论：**来源链已恢复到可审查程度；Buildings + Heat 科学基线不能直接接受。** 本轮没有修改模型、配置、数据或运行优化。

## 固定版本与四层证据

| 层 | 证据 | 本轮含义 |
|---|---|---|
| F：Framework | 固定源码的函数、规则、组件 | 说明可构建什么，不代表正式模型已保留或验证 |
| U：Frozen upstream | `a3616a68ee44592af6527ca9024a90f1956646ae`，默认配置与 ASEAN overlay | heat / residential / services 均 true；最终 `only_elec_network=true`，热组件会被移除；未运行新的完整 SC 网络 |
| T：Tutorial | `ce327bfae2abe5526d4c1976173f0f8d08366ba5` 的既有文件、网络审计记录 | 50 clusters、实际 48 个热节点、2013 年 6 天、3h；复用中间文件，不重算实验 |
| P：Paper | `5bacad702ccfed17ad19ab510fa710651e966f2c` 与作者网络 metadata | full-year 2013、100 clusters、3h；上述三个开关 true，但最终 only-electric 裁剪；不能当 full-SC 验证 |

[CONFIG_LAYERS.json](evidence/CONFIG_LAYERS.json) 保留逐层值。U 是已合并配置摘要，不冒充完成运行后的完整 effective config；T metadata 未保留的字段是 null，不猜补。P 来自前轮已提取作者包。原始证据位于 `research/00_model_audit`、`research/00_source_provenance`、`research/01_baseline_construction`，没有重写。

## 交付入口

1. [BUILDINGS_HEAT_SOURCE_TRACE.md](BUILDINGS_HEAT_SOURCE_TRACE.md)：年度量、曲线、空间分配、现有资产、集中供热与技术竞争。
2. [COOLING_ACCOUNTING_TRACE.md](COOLING_ACCOUNTING_TRACE.md)：制冷的实际位置及证据边界。
3. [HEAT_ASSUMPTION_REGISTER.csv](HEAT_ASSUMPTION_REGISTER.csv)：所有输入接受状态为 UNVERIFIED。
4. [BUILDINGS_FUEL_SHIFT_TRACE.md](BUILDINGS_FUEL_SHIFT_TRACE.md)：煤与油气生物质的外生处理。
5. [BUILDINGS_ELECTRICITY_DOUBLE_COUNT_AUDIT.md](BUILDINGS_ELECTRICITY_DOUBLE_COUNT_AUDIT.md)：A–J 核算与隔离验证。
6. [BUILDINGS_HEAT_DATA_GAPS.md](BUILDINGS_HEAT_DATA_GAPS.md)：剩余数据、工程、边界问题及责任划分。
7. [BUILDINGS_HEAT_ACCEPTANCE_STATUS.md](BUILDINGS_HEAT_ACCEPTANCE_STATUS.md)：逐项评估与最终 A–J 答案。

## 证据与复核

- [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json)：58 个固定 Git blob，含 SHA256；paper/current 分开保存。
- [UNSD_2019_BUILDINGS_ROWS.json](evidence/UNSD_2019_BUILDINGS_ROWS.json)：仅 11 国、2019 年、households/services 的 92 条原始记录，保留原单位、数量、国家、来源文件。
- [LOCAL_INPUT_HASHES.json](evidence/LOCAL_INPUT_HASHES.json)：读取的本地原始文件和教程中间文件哈希。
- [TUTORIAL_BUILDINGS_ANNUAL.json](evidence/TUTORIAL_BUILDINGS_ANNUAL.json)：既有 base / 2030 / 2040 / 2050 建筑列摘录。
- [ACCOUNTING_VALIDATION.json](evidence/ACCOUNTING_VALIDATION.json)：原函数隔离核算、原始数据对账、已完成教程曲线诊断。
- [PROFILE_SOURCE_RECOVERY.json](evidence/PROFILE_SOURCE_RECOVERY.json)：官方 PyPSA-Eur-Sec 历史 tag `v0.7.0` 解析到 `26a26b5b78b07d54d922e576220d07e7d89ae4e9`；不追 main。
- `history/`：参数引入、merge、blame、制冷关键词检索；检索中仅出现的交通 cooling 不属于建筑模块，本轮没有分析交通。

复核顺序：`collect_frozen_sources.py` → `extract_buildings_evidence.py` → `recover_profile_history.py` → `summarize_layers.py` → `validate_accounting.py`。前四者读取本地资料或固定历史公开文件；最后一个仅 AST 提取指定原函数，在合成夹具上执行，不载入 workflow main、不调用 solver。CSV 通过 `export_assumptions.mjs` / Artifact Tool 导出。路径写在脚本中，移交时需映射本地资料位置；证据 JSON 足以不依赖大文件审查本轮结论。

隔离检查不是 full-SC workflow readiness 测试。导入现有 PyPSA 环境时出现 PROJ 数据库警告；本轮数值核算未调用 GIS，数值断言全部通过；不据此宣称 GIS 环境验证通过。

## 状态约定

`SOURCE_RECOVERED` 指来源/代码事实可追溯；`ACCEPT_STRUCTURE` 只用于用户已冻结的科学原则或可继承的组件形式。`REJECT_DEFAULT` 是本审计“不直接用于 ASEAN baseline”的建议，不表示已经替用户删除或修改默认值。所有新输入仍为 **UNVERIFIED**，Human_Acceptance=PENDING。科学接受由用户与 ChatGPT 共同决定。

证据强度明确区分：**直接读取 / 隔离验证 / 解析推导 / 推断 / 建议验证**。本轮停止的是不具备证据的科学采用，不停止其他独立溯源。
