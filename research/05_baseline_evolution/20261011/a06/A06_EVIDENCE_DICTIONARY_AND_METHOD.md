# A-06 证据字典与只读复核方法

范围：源代码、已有回执、三份既有NetCDF的静态表与2920项权重向量。无PyPSA Network构造、LP组装、求解器导入、原生模型载入或AutoDL访问。未读大CSC和X/Pi/RC。作者2050的p_nom_opt/s_nom_opt只用于区分历史输入/结果，未复制到模型。

## 文件字典

| 文件 | 内容及边界 |
|---|---|
| A06_NETWORK_STATIC_READOUT.json | 三份NetCDF的GlobalConstraints、3套权重、carrier因子、存储成本字段按技术汇总；未存字段不擅自赋来源价格。大文件SHA引用既有已验索引 |
| A06_SOURCE_CODE_AND_SAFE_CONFIG.json | 固定commit、blob/SHA、真实行号摘录；仅安全白名单配置，无密钥；上游实际运行与SC能力分开。含历史决策原文，保留其时间语境 |
| A06_COST_OBJECTIVE_EVIDENCE.json | 最终V3 derivation、SHA匹配的effective ledger聚合、offset/FOM旧核算、生产meta及第一次不合格候选双账；未重读目标数组 |
| A06_AUTHOR2050_PROJECT_CLASSIFICATION.json | 15项已由A05国别判定的跨境项目、输入容量、输出容量、源CSV候选及UNKNOWN；另7国内DC不混计。源CSV匹配按名字/tag仅用于源码定位，不作为国别证据 |
| A06_RESOURCE_CARBON_BOUNDARIES.json | 特定CO₂/资源静态Store、Link、Generator及A05外部源清单；缺字段使用已索引PyPSA0.30.3默认，掩码null不当价格 |
| A06_PRIOR_ACCEPTANCE_AND_IDENTITY.json | Scheme A已核SHA回执、第二P2真实交接/终态核验；引用的旧AWAITING文字由当前G6-05暂停明确覆盖，不恢复执行 |
| BASELINE_CARBON_CONCLUSIONS.json / CAPACITY_SUPPLEMENT | 旧碳矩阵结论和Atmosphere局部逐项回读，原字节内容保留（JSON重排另有本轮文件SHA）；不重新跑全矩阵 |
| A06_EXTERNAL_EVIDENCE_INDEX.json | 本地原件路径、大小、SHA；区分复用大文件身份与本轮轻量文件哈希 |
| A06_VALIDATION_RECEIPT.json | 17项新证据一致性检查，非旧实验重跑，非可行性认证 |
| A06_EVIDENCE_INDEX.json | 最终本轮证据和方法脚本的SHA/大小；避免自引用hash |

## 确定性方法

`verification/extract_networks.py`读取已定位的2025、2050、当前三网络，缓存每个静态字段一次；读取snapshot权重，不读调度时序。`capture_sources.py`通过git show固定commit，白名单提取policy/cost/project字段，绝不输出完整配置。

`finalize_evidence.py`将静态表与既有A05国别结论、V3有效台账、固定源码连接；有效台账重新计算SHA必须为045034…，然后聚合，不信任V2继承摘要。`supplement.py`补充CO₂资源静态字段及特定代码。`compact_and_check.py`压缩重复大元数据并核17项一致性。

本轮执行使用本地Python3.11.13环境的netCDF4/numpy，仅以文件接口读取。当前生产成本/代码与旧档案都未重写。源码片段和报告的科学结论绑定F/P/U commit，不绑定随审计更新的HEAD。

复核可先只阅读JSON和运行下面的轻量包内校验器；无需访问AutoDL、下载大文件或重新运行提取链：

```
python verification/verify_a06_bundle.py <仓库或解压包根目录>
```

该脚本只对清单中的轻量文件核SHA、读取JSON、检查关键结论。原始提取方法附供复现；在既有证据已满足时不要求重跑。大文件身份继承A05 verified index，若文件被外部修改，应停下来重新核身份，不能仅按文件名信任。

## 证据等级与数量限制

VERIFIED、DERIVATION、RISK、UNKNOWN、PROPOSED按决策登记表解释。浮点min/max为静态摘要，不能比较不同资产总体后就声称同资产涨价。项目原始CSV映射不完整的条目保留UNKNOWN；作者额外封存hook有源码/配置但无本轮原生LP回读，不伪称已验证所有作者约束。

报告引用既有A03精确证书而不再扫描90,782,037项CSC；不从作者CO₂ GlobalConstraint缺一行推断未加载运行时hook；不把Gurobi状态用作新科学证明。

## Git与ZIP

独立分支 `audit/stage2-a06-policy-cost-resource-20261012`，起点A05已核commit `4e00897199d28c72b35f6cff550b30ba94337e06`；新PR以A05分支为base，差异仅A06和三份台账，不对PR #4/#5追加提交。PR保持草稿，不合并。

ZIP包含本轮Markdown、三份更新台账、必要A05轻量上下文、证据与方法；PACKAGE_MANIFEST列相对路径/大小/SHA/CRC，CRC_CHECK_RECORD记录实际解包读取校验；最终ZIP含该记录再校验，ZIP整体SHA记录于外置交付回执。文件清单与CRC记录自身hash由外置回执给出，避免递归自引用。

只包含md/json/py；排除NetCDF、矩阵、原始解向量、许可、token、私钥和云端凭据。工作在ZIP交付后停止。
