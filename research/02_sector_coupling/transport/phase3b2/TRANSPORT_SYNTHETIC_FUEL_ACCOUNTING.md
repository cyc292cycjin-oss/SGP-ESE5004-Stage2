# Synthetic fuel / H2 / electricity

**冻结：已有FT为显式供给选项。** 不新增技术，不设置新的固定“FT所需H2”终端义务，不将制燃料用电预装进A*。

U `prepare_sector_network.py:344–380`的FT Link从H2 bus取能、向oil bus供给，同时取stored CO2和AC；`:420–425,651–684`的电解路径再从AC制H2。SMR/SMR CC为已有H2供应可能性（`:506–524`），不能因写“synthetic”就断言实际一定用可再生电解氢。

## 账户关系

固定的四类shipping/aviation燃料义务 → oil供需平衡 → 化石供应/既有FT供给；FT实际流量 → H2与CO2输入、直接AC输入；电解实际流量 → 其AC输入。各Link效率、成本、容量口径沿既有技术链，采用数值仍须走数据确认；本轮不更新DEA、成本或效率。

固定需求与满足它的内生供给是正常物理平衡，不是双计。以下才是重复：同一fuel service另加预计算H2 Load，同时保留FT H2输入；或同一制氢/FT电量预装A*同时保留转换Link电耗。检查需以service/account ID与实际流量为单位，不是简单删所有H2 Load。

## 源码能力与可用链路

FT组件存在不证明首版组装一定可供给燃料。Phase4须验证H2、合法且带成本的CO2、辅助电/热与实际网络连通性。U DAC `:2988–3029`仅选择urban central heat/services urban decentral heat母线；Buildings第一版不强制显式heat后，不能默认DAC自动可用，不能给FT免费CO2或凭空添加热需求。这是组装依赖，非重开Buildings/Transport研究。

直接航运H2、FCEV、marine NH3/methanol仍DEFERRED。油品质量/掺混未细分是聚合限制，不能写成已验证SAF比例或可再生燃料产量。FT产出与化石供应的竞争结果需未来正式、已批准模型才能判断。

## 碳与时序

全系统物理报告跟踪CO2来源、捕集、利用、储存和燃烧回排。FT利用碳不是永久封存，点源碳不能在捕集和合成油两端各领一次减排信用。供电排放继续Power policy；共享SMR/捕集信用需符合[碳合同](TRANSPORT_CARBON_ACCOUNTING_CONTRACT.md)。

年度fuel Load可简单分配，但FT最小负荷、油/H2储能和电解可用性影响生产时序与系统价值；不能因年度量固定声称成本/互联收益完全不受形状影响。本轮不设计或执行敏感性实验。
