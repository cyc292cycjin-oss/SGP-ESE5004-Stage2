# Gate4 决策同步（CONTINUE）

已执行本轮及新增道路决定，保留旧决策记录，不回填历史批准。

- Residential68.2/63.0、Services75.9/29.5、Industry561.0/185.6、Agriculture-and-Other27.8/8.8：`ASSEMBLY_V1_ACCEPTED_GROWTH_PROXY`。2022来源倍率应用于合格2019非电固定燃料；不是国家/燃料直接预测，也不产生部门电力Load。
- AEO8 Mtoe使用`ASSEMBLY_V1_MTOE_CONVENTION_11P63_TWH`；225Mtoe=2,616.75TWh。ASEAN10依已接受2019电力份额分配，TL独立区域增长外推。此约定不覆盖UNSD已有单位或冻结价格。
- 国内海运/航空合格2019义务恒定；国际bunker独立恒定。此前明确接受的17条国际bunker保留原精度（SG海运535.3418TWh）；原始更高精度差额≤50MWh单独登记。SG航空新增avgas源行639.6MWh进入修复后的基年账户。
- **本轮新增**道路非电倍率`374.9/145.2`，标签`ASSEMBLY_V1_ROAD_NON_ELECTRIC_TRANSPORT_GROWTH_PROXY`。只应用合格道路非电账户，2019/2022错年、全交通→道路代理及TL外推明确披露；重要外生假设，Phase5敏感性必需。
- 道路350.5315Mtoe保留历史与来源，但更新为`ROAD_TOTAL_REFERENCE_ONLY; Posting=false; EnforceExactTotal=false`。此项替代此前强制恢复完整道路数值分解的要求；不再次归一化燃料。
- Road EV及铁路电力仍在A*中；没有新增EV Load，不扣未知电力，不使用全交通0.2%作道路份额。
- 碳开关false，外部化石供应独立国家/数量非绑定，生物质仅已批准固定义务，地质封存无资产；均未改变。

来源：[AEO8](https://www.aseanenergy.org/publications/the-8th-asean-energy-outlook/)，C.2印刷181/PDF183、C.3印刷182/PDF184；道路比例印刷64/PDF66的BAS应用仍是人工近似。[INSEE](https://www.insee.fr/en/metadonnees/definition/c1355)支持toe定义。精确决策与哈希位于`research_inputs/assembly_v1/sources/GATE4_*DECISION*.json`。

参考差额仅以ASEAN10的**已合格子集**展示：当前非电道路数值260.437889TWh；相对350.5315Mtoe参考差额328.137872Mtoe（93.611522%）。大部分道路油/生物燃料账户因混合份额问题尚未合格，所以这不是完整道路对比，更不是EV量、unserved energy或能源守恒失败。真实网络尚未物化，MaterialisedNetworkRoadMWh=null。
