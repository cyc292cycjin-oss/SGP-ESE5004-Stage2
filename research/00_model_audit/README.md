# SGP ESE5004 Stage2：A1–A4只读审计交付

2026-09-30；模型固定提交`ce327bfae2abe5526d4c1976173f0f8d08366ba5`。最终版本位于 `C:/Users/20122/Documents/ChatGPT/ASEAN/research/00_model_audit`。本轮读取原机既有数据与结果，没有启动求解、改参数、修复模型或删除历史资产。

## 先读这五项发现

| 发现 | 证据与含义 |
|---|---|
| 当前教程不等于完整SC基准 | sector开关后还有only_elec_network裁剪；终态只剩4类电力Load，其中工业为零。需先确认完整SC边界和有效需求 |
| 论文案例范围已核实 | 本地2026 IOP论文§3.1是电力系统，其他部门仅计电力需求；完整sector coupling列为后续工作。框架可用性不代表论文已做完整SC |
| 工业需求输入有严重缺口 | 三年节点工业表每年480个数据单元格全部为空，最终工业电力需求为零；不能补数或直接正式运行 |
| 当前baseline无CO2Limit，预算键有冲突 | co2base_value=1e9与函数消费base_value=limit并存；不能直接声称当前启用1000→100 Mt路径 |
| DEA资料找到但版本未对齐 | 用户本地Renewable Fuels标August2026/sheet80 AEC；模型来源字段指sheet86。成本还含AEO8覆盖和非DEA来源，不能自动更新 |

上述为直接文件/源码读取。需求不守恒的可能原因和互联如何影响部门配置为有边界的推断；国家预算/切片与目录结构为未执行方案。

## 八项交付

1. [MODEL_INPUT_MAP.md](MODEL_INPUT_MAP.md)：数据源→转换→模型入口，成本实例与数据缺口。
2. [SECTOR_COUPLING_MAP.md](SECTOR_COUPLING_MAP.md)：框架/当前配置/教程终态/论文范围，以及实际组件、需求和成本。
3. [MODIFICATION_MAP.md](MODIFICATION_MAP.md)：config/data/workflow/source分类、科学影响和可复现性。
4. [CARBON_IMPLEMENTATION_NOTE.md](CARBON_IMPLEMENTATION_NOTE.md)：当前碳实现、键冲突、standalone可比性选项。
5. [DATA_LEDGER.csv](DATA_LEDGER.csv)：10,139条记录，28列；全部UNVERIFIED/PENDING；Final_Value、Verified_By为空。
6. [REPO_STRUCTURE_PROPOSAL.md](REPO_STRUCTURE_PROPOSAL.md)：实际仓库分布和目标研究层，未搬迁母模型。
7. [REPRODUCIBILITY_RULES.md](REPRODUCIBILITY_RULES.md)：Git/config/input hash/环境/正式run manifest规则；另附未执行模板。
8. [USER_INPUT_NEEDED.md](USER_INPUT_NEEDED.md)：已找到资料与真正仍需补充/共同决定的项目。

台账10,139条不是10,139个已验证参数。它含成本记录、派生系数、配置、需求单元格（含缺失）和来源文件/输入族记录。原文值、模型编译值、派生值分列；未验证的原始字段留空。大型气象/GIS及电厂等仍有输入族级登记，不能把本轮称为全量原始数据验收。

## 证据与复核方法

- `AUDIT_RUNTIME_EVIDENCE.json`：三个既有教程结果hash、最终组件/负荷、权重、碳配置和约束。原模型提取前后git status为空。
- `INPUT_INVENTORY.json`：有界输入清单和2030已存在前处理阶段对照；大型文件空hash附原因。
- `USER_SOURCE_INVENTORY.json`：用户DEA工作簿元数据/hash/表名及限定候选论文首页；没有改原文件。
- `PAPER_EVIDENCE.json`：已找到IOP论文的本地路径、hash与提取文本；关键定位PDF第5–6页及第15页。
- `LEDGER_VALIDATION.json`、`DELIVERY_VALIDATION.json`：记录数量、状态、工业缺失诊断及交付格式/副本哈希验证。
- `input_snapshot/`：原机小型输入的字节副本，用于双方查看；不作为新的模型输入源。
- `extract_audit.py`、`inspect_input_inventory.py`为只读原机提取；`build_ledger.py`→`export_ledger.mjs`从证据构建CSV；`validate_delivery.py`验证交付。它们不调用Snakemake/优化器。

复核优先读取已有证据，不重复执行模型。原机提取依赖现有WSL环境，表格导出使用本机bundled runtime；路径均在脚本/证据中明确。复现提取时输出必须指向新的审计目录，不能覆盖已人工编辑确认的台账。JSON中的Infinity/-Infinity/NaN以字符串保存，分别表示无穷上限/下限/缺失，不是0。

## 现在能否推进实验设计

**可以开展有待决项的设计讨论；不能冻结并启动正式实验。**优先共同确认carbon baseline含义、完整SC部门边界、工业需求原表、版本对齐和共享资源/外部商品边界。需求守恒、拓扑损失和配置键冲突需要后续独立评审/修复。本轮没有估计国家benefits/losses，目录提案与manifest只是设计。

Git状态要分开解释：原模型与审计源码副本未改；当前Documents工作目录在本轮开始已有untracked outputs/work，未删除或代为提交。最终审计包为新增研究产物；其归档身份由Git提交和包内文件hash清单记录。
