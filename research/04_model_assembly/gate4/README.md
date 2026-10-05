# Gate4 — 固定账外置、EUR2020价格层与剩余物理闭合

**FULLSC_NETWORK_NOT_COMPLETE；Gate5=NO；solver_runs=0。**

恢复基准ec681b86c7b1b2ac29b9af28a5f468c1fb3ec942，工作树与远程一致。本轮新决定GATE4-20261006-FIXED-ACCOUNTS-EUR2020只批准固定账方法与共同价格年；没有把未知参数批准为零。

已验证保留733个源机组、186586MW，其中水电47182MW；152项合格需求、152组数组、1436个开发Load。registry和数组字节hash与前轮相同。物理端口、效率、容量、时序、已有资源组、碳系数保持。1595项物理碳映射与前轮相同；200项SMR/SMR-CC政策权重保持null，policy_enabled=false，1000→100Mt轨迹未改。

六类商品的471个固定资源记录通过当前实际开发网及electric_base+未绑定JSON配方+一次需求绑定的重验。未知价格与物理CO2因子外置为Q×unknown，CSV空白字段明确表示null。物理义务不变，不是免费供应，不新增大气零排放事件。Animal waste未物化，单独待决。

**更正前轮币值年结论：**前轮仅追踪costs→processed，遗漏technology-data在生成costs前已进行的EUR2020转换。v0.13.2最终编译阶段对investment/VOM/fuel进行真实币值调整，但保留原currency_year元数据；746条货币记录已为EUR2020，本轮严格保留原处理值。AEO8追加值也在EUR2020。488条FOM百分比不平减，534条货币FOM从统一投资基数计算一次。只有biomass boiler的pelletizing cost在2030/2050两个库记录需要新增2019→2020平减；该技术未在本研究网物化，不激活它。

ECB同一官方年度EA20固定组成GDP平减序列已下载原件和元数据。价格层保留原文件、已执行转换及模型侧基年。10条非EUR记录属于5个未启用技术，尚缺FX精确桥接；活动网络另有340个风光配置边际成本及13条DC/B2B输入边际费用缺明确真实币值年/数值正则化定义。它们保持原值并标PENDING_BEFORE_SOLVE，不阻断无求解物理开发。

独立工程修复：100个FT Link此前未接入冻结表中已知VOM。本轮按EUR/MWh_FT输出口径乘效率写入Link输入侧marginal_cost；未改价格数值或技术学习假设。这项修复与价格平减分列。

水电计数由表自动复算：70组、58组合格、12组待决，待决16机组/1454MW。本轮新增水电接入0。12组全部可回溯原父项及168小时缓存输入，但没有恢复唯一相容的全年资源归属；不能铺满全年。9组有同国/同原区域AC分区的参考候选，3组无此类型候选。候选已有资源是否分配逐项记录，未复制来水、未移动机组、未自动重新分摊。

156项测试通过；实际资产回读、固定账重验、需求单次绑定与原成果保留通过。两个.nc仍是开发资产。完整输入门禁仍有51个物理账户待决，不能导出完整研究基准。

|资格维度|当前状态|
|---|---|
|物理结构|已建开发范围通过；全模型仍不完整|
|输入覆盖|未闭合；33来源组合/51账户为关联集合|
|价格可用性|已知成本源层EUR2020；配置边际费用资格未闭合|
|全成本报告|false；未知固定价另账|
|物理排放报告完整性|false；未知固定排放另账及未覆盖需求|
|政策约束资格|关闭；200个归属待决，启用时拒绝|

重点文件：EXTERNAL_PENDING_FIXED_ACCOUNTS.csv、MODEL_COSTS_EUR2020.csv、PRICE_REBASE_PROVENANCE.csv、RESIDUAL_PHYSICAL_DECISIONS.csv、FIXED_ACCOUNT_QUALIFICATION_TESTS.md、PRICE_REBASE_TESTS.md。
