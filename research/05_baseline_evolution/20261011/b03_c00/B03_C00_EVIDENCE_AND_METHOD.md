# 证据字典与复核方法

本轮不重新读取CSC、X/Pi/RC或NetCDF；不重跑A/B阶段的15项/全量扫描。输入是已接受报告、固定Git对象、轻量JSON、第一次原生小回执。只新增参数/身份引用与协议一致性检查。

| 文件 | 来源和用途 |
|---|---|
| SOURCE_BINDING.json | B01/B02父commit下15份已有证据的SHA/大小，Scheme A跨分支绑定 |
| FIRST_RUN_EFFECTIVE_MODEL_PARAMETERS.json | 首次实际154个数值参数的逐字节副本；已核BACKUP_INDEX，不包含许可字符串 |
| FIRST_RUN_REFERENCE_BINDING.json | 5份原生小文件的SHA与备份索引对应；含历史RAW状态/属性；不是新运行授权 |
| FIRST_RUN_RESOURCE_REFERENCE.json | 历史资源采样和保护值；不能当实时资源或WLS核查 |
| V4_APPROVED_HISTORICAL_REFERENCE.json | 原V4逐字节副本，保留旧维数和状态；日版必须新增身份绑定，不覆盖 |
| FIRST_COORDINATE_RULE_SOURCE / HISTORICAL_SCALE_SELECTION | 固定源码完整行号摘录与SHA，揭示旧Q/形状假设；不是运行该代码的许可 |
| B03_FINAL_RISK_CLASSIFICATION.json | 12项最终风险状态、既有证据与未来处理线 |
| C00_PROTOCOL_DESIGN.json | PROPOSED且execution_authorized=false；日历/参数/资源/预算机器定义 |
| DESIGN_VALIDATION_RECEIPT.json | 新设计静态一致性及小型Fraction演示，不能当新模型验收 |
| B03_C00_EVIDENCE_INDEX.json | 本轮固定输入/输出轻量文件SHA；包清单另给最终台账commit和全包CRC |

已证事实取自原件，推导采用明确前提；未来检查均标为未执行。无需访问网络文献或当前云端来再次研究参数。科学源、旧结果、Scheme A/V3/V4/P2及消费标记完全保留。ZIP不含原始NetCDF、大向量、矩阵或授权可执行入口。历史元数据中的公共路径仅为证据位置，不附许可或凭据。

复核命令（只检查设计文件）：在审计仓库中使用Python3运行 `research/05_baseline_evolution/20261011/b03_c00/verification/verify_design.py`。无参数，按脚本相对路径读取少量JSON，不连接云端、不加载模型。JSON证据索引和ZIP清单提供准确SHA链，历史来源可用固定commit读取，不要求合并PR。
