# Phase4 Gate4 — 剩余来源闭合与联合诊断网络

**FULLSC_NETWORK_NOT_COMPLETE；Gate5=NO；solver_runs=0。** 当前状态以CURRENT_PHYSICAL_READINESS.json、DIAGNOSTIC_NETWORK_MANIFEST.json、SELECTED_ASSET_SURVIVAL_2050.json、SELECTED_INTEGRATION_CONTRACT.json及当前registry/allocation为准。旧blocker、水电候选表保留历史，不能作为当前计数入口。

## 实际变化

|项目|进入本轮|本轮交付|
|---|---:|---:|
|合格源机组/批次|745|745|
|实际既有容量MW|187400.4|187400.4|
|已接入水电MW|47952|47952|
|合格需求账户/数组|152|153|
|开发/诊断Load|1436|1437|
|原来源组合待决|28|22|
|全部待决物理目标|46|40|
|待决原水电组/MW|5/684|5/684|
|外置固定账|471|471|
|实际物理碳事件|1597|1598|
|SMR/SMR-CC政策权重null|200|200|

MM LPG29千吨与TL LPG0.92千吨都来自冻结原文件，原交易为“Consumption by other consumers not elsewhere specified”。官方UNdata LP交易1234与冻结DSD1234支持该别名映射。修复交易身份后，MM OtherNEC油账户增加380770MWh，TL新增OtherNEC油账户12079.6MWh；2050使用此前已批准的constant2019。两行共392849.6MWh，非残差补数，原脚注（TL为1）、行号与hash保留。MM国内海运及TL居民/服务/农业油、铁路父账、国内海运六项空组合依既有“限定商品来源FEC已由互斥用途耗尽”规则解除机械阻断。国内闭合未用于排除国际bunker。

原152个合格账户均保留；151组数组逐元素不变，MM OtherNEC重新分配，TL新生成一组。目标与数组manifest已绑定新registry。原已接入745源记录、全部基础组件/输入时序、投资/损耗/容量及既有运维与上一交付逐字段比较通过；新增实际容量0MW。

GPD仅针对条件存续子集做身份核查，并保留原418MW重复证据。新恢复EAC原监管报告，确认Stung Atay120MW、Stung Tatay246MW已由GEM表示，新增366MW重复疑点关闭。它们没有被标为退休或再次接入。原2656.09MW待核子集尚余2290.09MW：水电1615.09、气电330、煤电345。Avion官方资料明确为开式循环，不能采用冻结CCGT标签；其他混合身份/状态问题保留。原表与新证据均可追溯，未替换容量、年份或新增技术参数。

## 联合诊断网络

`research_2050_diagnostic_partial_unsolved.nc`已实际导出并回读。输入为当前electric_base、未绑定JSON载能配方及合格数组；未使用含Load的开发片段NetCDF。

- artifact_role=DIAGNOSTIC_PARTIAL_UNSOLVED；fullsc_network_complete=false；input_coverage_complete=false。
- solver_allowed=false；scientific_results_allowed=false；policy_enabled=false；Gate5=false。
- 153账户一次绑定、年度积分/国家归属、端点/组件唯一性、原有存量、非电载能隔离、电力跨境分类、固定账和碳事件检查通过。
- 母线结构上的供给可达性通过；这是必要图结构条件，不是容量、逐时运行或联合多输入可行性证明。
- required constraint hooks保留并通过拒绝规则；没有安装优化变量，没有执行模型约束，更没有求解。
- 所有组件静态字段、输入时序、时间权重及meta进行导出前后比较。仅将缺失的可选字符串标签规范为NetCDF空字符串；数值缺失和JSON null不变。
- 完整构网入口保持原门禁，实际调用仍返回阻断且不生成完整网络。研究优化hook显式拒绝诊断网络。

此次跨模块发现的具体工程问题是可选字符串标签NaN在NetCDF中变为空字符串；已明确规范其序列化表示。时间索引的缓存freq在回读后不保留，校验仍逐点比较2013全年3h时间与权重。没有通过放宽实际数值、国家边界或缺失输入资格使门禁通过。

## 分离资格

六类固定商品471项继续独占原义务，未知价与物理CO2为null外置；完整网重新验证资格仍是后续必需步骤。Animal waste不继承这项证明。价格层1780项字节不变，FT100项VOM、13条连接零扰动、340风光显式费用保留。PricedObjective为null，未比较任何目标值；FullSystemCostComplete=false、FullSystemEmissionsComplete=false。KnownFixedCost的既有FOM若日后进入目标，只计一次。

1598项物理事件不等于全系统排放已知；200项SMR/SMR-CC政策权重仍null。政策关闭，未改变1000→100Mt假设。

## 仍需审阅

40项待决物理目标为22个来源组合与18个掺混影响账户的映射，不是40份新文件。具体原件/一次性选择见[RESIDUAL_DECISIONS_WITH_IMPACT.md](RESIDUAL_DECISIONS_WITH_IMPACT.md)。GEM缺年4092.52MW与GPD缺年15477.503MW保留分组，30条候选关联不构成可相加库存；128条1861.5MW上界证明未改动。5组684MW原水电继续独立待决。

## 运行证据

本轮实际运行58项定向/保留性测试，详见evidence/diagnostic/CURRENT_TEST_COUNTS.json及交付validation_logs；诊断成功以实际NetCDF回读与COMBINED_NETWORK_STATIC_CHECKS为依据。首次失败日志保留，不标成PASS。构网代码版本`5739aea3401f6f5715251ab6336e4f6c304c3be7`；来源修复、身份核验、诊断工程分别提交，未新增科学方法。

NO SOLVER；不进入Gate5；没有系统成本或互联收益结论。
