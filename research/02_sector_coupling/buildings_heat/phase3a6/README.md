# Phase3A6 交付入口

先读 [PHASE3A6_READINESS.md](PHASE3A6_READINESS.md)，再读电力边界候选和Malaysia原型。18项请求交付均在本目录根部。科学输入全部PENDING，报告中的verified仅表示源码/来源转录或计算检查已核验。

Material passport：academic-research-suite fact-check；研究工程证据审计，不是论文写作或正式实验。本轮使用PDF原页核对与spreadsheet来源账本；未使用代理并行工作。

## 阅读顺序

- 电力：ASEAN_ELECTRICITY_BOUNDARY_TRACE → AEO8_ELECTRICITY_SOURCE_TRACE → ELECTRICITY_LOSS_ACCOUNTING → FULLSC_ASTAR_CANDIDATES → BASE_FUTURE_ELECTRICITY_BOUNDARY。配套glossary与electrification scope CSV。
- Malaysia：MALAYSIA_ENDUSE_MAPPING → MALAYSIA_2016_2019_YEAR_BRIDGE → MALAYSIA_E3_ACCOUNTING_PROTOTYPE。配套source ledger、electric heating、device、useful candidates与closure CSV。
- 决策：PHASE3A6_DATA_GAPS、USER_INPUT_NEEDED_PHASE3A6、PHASE3A6_READINESS。

## 复核契约

`data/SOURCE_REGISTRY.json`是本轮使用来源的file/URL/hash登记；`data/raw/NEW_SOURCE_REGISTRY.json`保留初次旧水热器URL404，`SUPPLEMENT_REGISTRY.json`记录恢复后的新官方文件。旧阶段原件通过相对路径复用，交付zip包含依赖。原件版权仍属于发布机构，仅为项目审阅/复现保存，未推定开放再分发许可。

`build_prototype.py`读取原件与Phase3A5快照，生成JSON分析中间表；`export_tables.mjs`以artifact-tool生成7张UTF-8 CSV。CSV为静态可审计表，不含可交互Excel公式；推导公式、未知字段和来源列随表保存，重新计算由固定脚本完成。运行生成器只写本研究目录，不接入workflow。

`capture_evidence.py`负责定点PDF文字/图像检查；`inspect_losses_wsl.py`只读冻结Git身份与优化器API。快照和原PDF是依据，提取文本用于定位。数值断言与包校验由 `validate_delivery.py`、`package_delivery.py`完成。不要重跑先前阶段的finalizer，也不要把表内各种替代来源和父/子行直接相加。

当前依赖：Python pypdf/pypdfium2，Node @oai/artifact-tool；只读优化接口检查使用既有PyPSA0.30.3环境。没有安装新模型包。E1/E2/E4记录来自 `../phase3a4/BUILDINGS_FIX_INTEGRATION_REPORT.md`，不是本轮重复求解。

原始PDF/HTML和预览遵循已有不入Git惯例，进入hash清单和交付包；研究报告、源码证据、计算脚本、CSV及登记入Git。提交和包哈希由外部receipt记录，避免提交自引用。既有outputs/work目录未清理或整体入库。
