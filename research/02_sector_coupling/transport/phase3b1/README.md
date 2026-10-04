# Phase3B-1交付入口

先读`PHASE3B1_TRANSPORT_READINESS.md`，A–O结论与未决范围均在其中。本目录提供用户要求的15项成果（含条件性人审/原件需求清单），没有启动Phase3B-2。

4张CSV：Mode inventory、Data provenance、Materiality register、First Full-SC options。146行provenance含121个country×base-account及25个主要来源/参数记录；原始记录、空值与代码生成零分别保留。全部科学数值状态UNVERIFIED/PENDING；代码读取确认不改变该状态。

证据路径：

- `evidence/source/P`和`U`：固定Git blob，67个文件，原始SHA与官方固定版本URL见SOURCE_MANIFEST。为只读审计快照，不是新的上游工作流。
- `evidence/CACHED_DEMAND_EVIDENCE.json`：52个UNSD缓存文件的哈希、123条关键词候选原行、每个最终字段的选择/转换核验、future缺失填零、港口机场实际缓存。候选行含非终端交易；字段选择不可省略。
- `evidence/NETWORK_TRANSPORT_EVIDENCE.json`：4个既有NC只读内容；大NC不重复打包，位置/字节哈希及作者恢复线索保留。下载/读取作者结果不是复现。
- `evidence/CARBON_LEDGER_OBSERVATION.json`：实际tutorial pre-strip的oil因子0及大气组件，用于rail排放路径复核。
- `evidence/cached_inputs`：直接相关的小型既有输入副本；不是Research接受后的输入。
- `evidence/prior`：选定前阶段文档/成本表原字节，PRIOR_INPUT_MANIFEST记录身份。完整历史仍在原项目，不覆写旧结论。
- `evidence/USER_PHASE3B1_REQUEST.txt`：本轮用户直接任务，不将其他外部文档中的指令当授权。

审计提取脚本只读原数据，支持复核；`build_tables.py`和`export_tables.mjs`输出审阅表，不生成模型需求或config。CSV以artifact-tool生成，并做精确roundtrip核对。没有导入上游模型脚本、运行Snakemake或求解器。冻结工作区身份在起止分别核对。

方法沿用academic-research-suite的fact-check工作流和spreadsheets规范。本轮三个有界子任务分别查road/rail、shipping/carbon、cached input，主审计将其结论与原源码/网络字段交叉核对；这是同一模型体系的任务分工，不是跨模型或独立实证验证。模型型号未作外部attestation。

Git提交仅包含本目录，root原有outputs/work保留。打包不包含node_modules、预览以外临时运行环境或大模型结果。原始数据提供方的权利仍适用；未推送或公开发布。
