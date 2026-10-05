# Phase4 Gate4当前状态：精确映射、方向费用与闭合选择

**FULLSC_NETWORK_NOT_COMPLETE；Gate5=NO；solver_runs=0。**

恢复HEAD12f68e5f1981cbd9c337582863045234df699e23，本地/远程身份一致、起始工作树干净。

保留733源机组186586MW（含水电47182MW）、152账户/数组、1436Load、471外置固定账、1780价格层及100个FT VOM接线。生产两个开发NetCDF、未绑定配方、价格层、碳映射、registry与数组均与前轮逐字节相同。没有重建已完成资产，没有solver或新技术。

本轮真正恢复：301父项的321条GPD来源链接，逐父项容量22628.143MW全部相符。年龄为电厂可能加权年份，后续资格仍未闭合，新增生产容量/合格物理账户0。236个GEM缺年机组与6个未知状态机组保持，缺年已确认既有量5954.020MW；不重新索取229项已修复年份。

请求/文档修复：DSD证实1235为服务业、1232为农业。原请求CSV与实际查询本就覆盖ID服务业；前轮audit_fixed_price_residual手写用途反转已消除。当前reconstruct逐组生成10请求，全部已有回执，无新交易查询；没有掺混数值缺口关闭。

费用证明：13条DC/B2B全部精确等于原run的固定seed扰动；12条双向流量在PyPSA0.30.3产生带符号费用，反向可为负。340风光为冻结显式配置假设。没有擅自删除这些费用或变更科学身份；修正方案集中待审。

工程报告修复：KnownFixedCost在安装既有FOM目标hook后是PricedObjective的已含子项，不应再次相加。新报告字段KnownFixedCostIncludedInPricedObjective、KnownFixedCostToAddToPricedObjective及PendingFixedCostIncludedInPricedObjective明确关系；未构建目标时前两项为null，已核实包含时追加量0。带已知FOM却无法确认hook的传入目标被拒绝。未知固定价/物理CO2仍为null，FullSystemCostComplete和FullSystemEmissionsComplete为false。

水电70/58/12计数保留：7组770MW已有接受资源重分配候选；2组157MW有未分配参考资源的互斥数值候选；3组527MW无同类型区域源。全部未批准、未进入生产。15个NEC相关问题完成同范围对照；4个bunker不在FEC范围，其他11个未能整体闭合。

175项测试通过（19新+156保留回归），合成目标只建立表达式；源到数组与实际资产保留核验通过。

|维度|状态|
|---|---|
|开发物理结构|既有范围保持，未扩大|
|全输入覆盖|未完整；51物理目标待决仍保留|
|价格可用性|共同EUR2020规则保留；数值扰动/配置方法待选|
|全成本报告|false，未知固定价格外置，已知FOM不得重复加|
|物理排放报告|false，1595物理映射不等于全系统完整|
|政策资格|policy_enabled=false；200个SMR/SMR-CC权重null；1000→100Mt未变|

最终组装仍只能electric_base+未绑定carrier_fragment.json+合格数组；未导出完整网络。下一步只需审阅CONSOLIDATED_CLOSURE_CHOICES中的实际方法选择及精确原件请求。
