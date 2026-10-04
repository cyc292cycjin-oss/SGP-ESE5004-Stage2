# Buildings 来源族审查

结构接受与数据接受分开。用户已明确的R/S分账、fixed service+endogenous supply、Cooling留在direct electricity记为 `ACCEPT_STRUCTURE`。下表的“建议接受来源族”**不是** `ACCEPT_SOURCE_FAMILY` 的人工决定；本轮该状态尚未授予任何新输入。所有数据 human acceptance=PENDING。

| 来源族 | 已证实/可继承部分 | 尚未关闭 | 本轮状态 |
|---|---|---|---|
| UNSD 2019 final energy | 官方跨国fuel/transaction框架；本地92行和11国电力总账有明确文件与hash | 2025导出≠官方2019发行版本；缺行≠0；印尼居民油品分类与国家统计不一致；HHV/LHV/体积热值 | 建议接受来源族，具体数据 `ASEAN_VALIDATION_PENDING` |
| 模型 `_helpers` 转换 | kWh↔TWh、TJ↔TWh可精确复算；fuel分组可追踪 | mass/volume统一因子不是国家实测热值，尤其Fuelwood | `ASEAN_VALIDATION_PENDING` |
| base space/water split | 固定外生服务结构可继承 | 0.6/0.4为继承默认，未恢复ASEAN统计依据；config和fuel CSV是两个入口 | `ASEAN_VALIDATION_PENDING` |
| fuel shares/growth/efficiency | 外生与内生链已拆开；每个列可追踪 | DEFAULT并非ASEAN；R/S不对称，部分燃料新增项无相同增长乘数；0.9不是COP | `ASEAN_VALIDATION_PENDING`，统一服务口径 `SCIENTIFIC_DECISION_REQUIRED` |
| BDEW | 与Eur-Sec v0.7.0固定数值相同；作为shape不决定年度量 | CSV生成版本/建筑类别不完整；热带和S/R用途验证缺失；热水四列常数1 | `ASEAN_VALIDATION_PENDING` |
| ERA5/atlite | 温度→degree-day路径可读；可用气象源族 | 实际研究cutout/version/hash尚未冻结；默认阈值15°C与真实用途关系待审 | 建议接受气象来源族；shape `ASEAN_VALIDATION_PENDING`；E2 `ENGINEERING_FIX_REQUIRED` |
| WorldPop/GADM/UNCTAD | 国家→节点人口份额及城市划分可复算 | 同人口权重不等于建筑面积/服务密度；UNCTAD live下载未锁版本；多时区只用首时区 | `ASEAN_VALIDATION_PENDING` |
| EC existing heat stock | 2012 EU28+3资料与代码明确 | 无ASEANstock；DEFAULT0及注释导入不能证明零设备 | 首版stock表征 `SCIENTIFIC_DECISION_REQUIRED` |
| DH默认 | 计算式和0.3/1/0.15进入位置明确 | 未发现统一ASEAN热密度/网络份额/损耗支持；0既有份额可生成新DH | `ASEAN_VALIDATION_PENDING`；是否纳入 `SCIENTIFIC_DECISION_REQUIRED` |
| AEO8 | 官方区域来源族，有独立R与commercial、终端用途讨论 | 10国不含TL；terminal detail为projection，不能当2019观测；需保留Nov2024勘误 | `DATA_UPDATE_CANDIDATE`（边界/交叉验证用途） |
| 国家平衡（ESDM、MME/ERIA） | 同基准年部门/燃料对照，可追原表 | ID/KH子集，不自动拼成11国；存在估计量、版本及部门差异 | `DATA_UPDATE_CANDIDATE` |
| NEA/ACE-IEA cooling、IEA end-use | 官方端用途证据/元数据，可验证结构定义 | SG样本并非全ASEAN；IEA付费数据未取得、11国覆盖未证实 | `DATA_UPDATE_CANDIDATE`，缺覆盖仍PENDING |

来源定位：[数据登记](BUILDINGS_DATA_REGISTRY.csv)、[冻结原始文件清单](../buildings_heat/SOURCE_MANIFEST.json)、[历史来源与BDEW追踪](../buildings_heat/BUILDINGS_HEAT_SOURCE_TRACE.md)、[新候选逐项对照](BUILDINGS_ASEAN_DATA_CANDIDATES.md)。

## 能关闭和不能关闭的缺口

**已关闭（证据）**：原作者base计算可复算；正年度量丢失机制可重现；R覆盖S/central及service命名错误可重现；官方候选能自行获取，用户不必重新找这些已保存的报告。

**未关闭（输入证据）**：11国同年R/S终端用途分解、既有电热扣减桥接、可比HHV/LHV/容量/用途口径、热带日形状。AEO8自己指出历史2022终端细分不能报告，因此不能以它补成2019观测表。

**共同研究决定**：国家异质来源能否混用；未识别燃料用途如何保留在账户中；是否接受stock未显式表示；第一版DH范围。选择不建独立cooking/cooling模块已冻结，不重复索要这一层授权。

没有可信ASEANstock并非无条件硬性数据blocker：若明确接受不显式表示历史设备，可不需要虚构stock；但该边界必须被记录和接受。缺少端用途与电力桥接则仍直接阻碍需求无重复和热量守恒。
