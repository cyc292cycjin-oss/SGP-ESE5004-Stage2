# 本轮决策执行记录

新DecisionReference：`GATE4-20261005-CONSOLIDATED-BASELINE-CHOICES`。来源为当前用户“Apply Consolidated Baseline Choices + Activate Qualified Existing Stock”执行指令。前一交付HEAD为7c4b9dda；以下方法仅从本轮生效，未追溯为过去批准或实测事实。

|组|本轮方法|执行情况|
|---|---|---|
|A 技术寿命|ASSEMBLY_V1_FROZEN_TECHNOLOGY_LIFETIME_ASSUMPTION|11类寿命明确HUMAN_ACCEPTED；相容真实退役记录优先，未新增核电/规划存量。749台通过身份、年份与容量资格，188,040MW。煤、气、水电、地热保留寿命敏感性。|
|B 空间映射|ASSEMBLY_V1_CONSTRAINED_NODE_MAPPING_PROXY|2,516项候选转为本轮接受的代理；749台存续机组全部覆盖。6处拒绝项保留。不称作者原映射，不改拓扑，不跨国/原分区。|
|C 泰国同版更新|ASSEMBLY_V1_TH_ROAD_COHERENT_VINTAGE_UPDATE|六项同版MO/DL/AL/BD/ZG/ZD经包含关系去重，正式目标、数组和开发Load已更新。旧源文件与旧行保留，memo不单独过账。|
|D 铁路/NEC|ASSEMBLY_V1_RAIL_CONSTANT_2019；ASSEMBLY_V1_TRANSPORT_NEC_CONSTANT_2019；ASSEMBLY_V1_OTHER_NEC_CONSTANT_2019|仅合格基年账户恒定2019。4项铁路、13项NEC国家×用途×载能账户物化；PH铁路两个燃料子账户仍被源重叠阻断。|

Section3还授权采用来源明确的既有技术参数代理。四类火电使用冻结参考网既有输入效率及最早缓存2030电力成本表的FOM/VOM，标记SOURCE_QUALIFIED_ENGINEERING_PROXY，不伪称逐机组实测或人工逐个批准数值。没有使用2050新设备效率。原始成本分别保留EUR2020/EUR2023来源口径；没有新增币值重基转换。

`research_inputs/assembly_v1/sources/GATE4_CONSOLIDATED_BASELINE_DECISIONS.json`、寿命表和映射/性能合同记录授权链。原133目标和数组保持。EV embedded、既有增长、Mtoe、bunker、单年资产边界均未重问或改动。

生物燃料供给成本、物理CO2/碳来源和SMR混合用途归属不包含在本轮数值授权中。policy_enabled=false。No solver。

## 2026-10-05 本轮水电/碳资格决定

新DecisionReference：GATE4-20261005-HYDRO-PHYSICAL-POLICY-SEPARATION。实施同节点水电组代理和PHS6h；实际新增47182MW。物理/政策资格独立，未知政策权重null。此前增长、单位、EV、bunker、寿命、映射、MY/TH、铁路/NEC决定保持。固定生物账与统一真实价格年份仅候选，未自动批准。
