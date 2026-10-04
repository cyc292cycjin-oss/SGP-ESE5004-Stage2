# Final energy → Useful heat：真实候选与边界

Material Passport: academic-research-suite / fact-check; Phase3A5 v1; 2026-10-02。VERIFIED OBSERVATION指原值、原件哈希及算术；科学适用性全部PENDING/UNVERIFIED。

**140条候选已填写，0条可直接作为完整有用热模型输入。** 共92条UNSD2019原始R/S记录、15条Malaysia官方end-use/历史比较记录、3条Singapore官方总量/份额记录、30条ERIA局地混合燃料记录。所有 `UsefulService` 和 `Efficiency_or_COP` 空白；没有自动使用DEA、未来模型效率或0.6。

## 已接受的计算规则

`Q_useful = F_final × EndUseShare × DeviceInputShare × historical Efficiency_or_COP`。

F为已经属于某用途的输入时，`FinalEnergyScope=end_use, EndUseShare=1`，仅表示范围恒等；不可再乘一次用途份额。燃料总量为`fuel_total`，缺用途份额即停止。设备占比必须是输入能量占比；保有量占比没有利用率/负载证据时不能代替。HHV/LHV、季节/额定性能、进水温度/热水服务边界、空间供暖交付点应共同记录。电力不涉及燃料热值，但热效率/COP的季节和服务边界仍需证据。

GWh→MWh的1000为单位前缀换算；ktoe与燃料质量/体积转换未获得本行认可口径时保留源单位。`HistoricalElectricHeating`字段沿用Phase3A4的MWh_el定义，因此MY住宅70ktoe没有强填该字段，商业1034.62GWh仅换算为1,034,620MWh_el。这不是有用热。

## 来源能支持什么

| 来源 | 已核实的候选值/范围 | 仍不能做什么 |
|---|---|---|
| Malaysia NEB2016 PDF95 Table42 | R电力：cooling327、water70、lighting233、cooking117、appliances1586ktoe，和为2333ktoe。gas cooking1、LPG cooking538、kerosene lighting3ktoe。 | 调查方法覆盖Peninsular；表值是否全国扩样需解释；设备效率与2019迁移未闭合。没有space列不等于零。|
| 同报告PDF103 Table47 | S water1034.62GWh；cooling16440.66、lighting8516.23、other13114.06GWh。 | 四项和39105.57，印刷总计39106.00，差0.43GWh；保持差额，不补给任何用途。other不能保证不含未分类space heat。|
| 同报告Table39–41 | R water2013=59、2014=61、2015=63.48ktoe；用途份额都约3%。 | 同一本书的多年份估计不等于多轮独立调查；不能据此接受2019不变。|
| Singapore NEA2017官方发布 | national households7295GWh；typical-home waterheater11%、AC24%。 | “typical home”与国家总量的分母/能量权重不同，未计算7295×11%；没有Services或历史效率。|
| ERIA2013 Table11 | 14个urban/rural条目的water、14个cooking及KH/SG两个微小space值，单位Mcal/household。 | 112户便利样本，混合燃料，时间口径未闭合；不能全国扩样、当作电热、年化或迁移2019。|
| UNSD2019原始导出 | 11国92条R/S燃料/电力总量，按国家/交易/年/单位唯一匹配原始文件。 | 不能从fuel total推断space/water/cooking；没有热值/含水率等时不用旧模型硬编码换算。|

原件及许可信息见 [source registry](data/raw/buildings/SOURCE_REGISTRY.json)；逐行定位、前阶段JSON精度差与原值匹配见 [source checks](data/processed/buildings/CANDIDATE_SOURCE_CHECKS.json)。原始导出比之前JSON多出的小数位本轮保留，属于取回源精度，不改模型数据。Malaysia cooking三个燃料格合计656ktoe、印刷合计655ktoe；可疑舍入/表源差异只登记，不调平。

Malaysia方法页PDF92：R样本2000户、Peninsular4区/10房型/53类电器；PDF98商业12类别、12州、5000premises调查工作，扩样及实施波次细节不足。所列2016是表格参考年，不自动等于调查实施年。相邻表加总的舍入差进一步说明需要原工作表或方法附录。

## 其他已知候选的处置

菲律宾DOE Compendium Table2的搜索索引恢复了2011为**六个月**回忆期这一关键脚注，2004为一年；2011 water3.4%/用户均值484kWh仅列为INDEX_ONLY。原PDF仍未取得，未进入数值input候选，也未乘2年化。2023 HECS技术说明可确认全国/区域调查框架，不能代替结果表。

Indonesia ESDM2019商业定义含water heating/cooking/AC，但没有足够用途数量。家庭定义排除私人车用燃料；这与现有UNSD住宅gasoline条目的范围仍冲突。UNSD2019住宅electricity104714GWh/LPG6610.02千吨，而ESDM2019住宅electricity103016GWh/LPG7447千吨，未自动择一或重分类。

Cambodia报告支持住宅/商业LPG有cooking用途，同时LPG也服务transport；仅凭fuel标签不能全归烹饪或热水。BELDA和越南局地研究可支持地区/时序方法候选，不能填全国电热量。BN/MM/TL目前保留可追溯final-energy候选，未作额外宽泛搜索。

## 表格阅读与账户保留

候选沿用原41字段，增6个审阅字段；所有行Status=UNVERIFIED、HumanConfirmationRecord=PENDING。父总量、用途、份额、历史比较、局地样本均标NON_ADDITIVE角色，不能把140行相加。154行矩阵完整覆盖11×R/S×7燃料组；`others`含混合燃料/太阳热等尚未映射项，**不是把它们都认定为其他实际燃料**。每用途的候选ID提供回溯，UNKNOWN保留未知。

Cooking：MY R electricity→DirectElectricity；gas/LPG→DirectFuel；其余无法证明燃料用途的行→Unclassified并保留原直接电/燃料账户。MY kerosene3ktoe是lighting，不是cooking。地方混合燃料cooking不能全部认定DirectFuel。各国完整cooking分区尚未完成。

Cooling：电制冷继续留在直接电力父账户F/B/C，不能从A*扣除或再添thermal Load。没有量化cooling份额时保留unpartitioned；本轮未创建任何Cooling Load。当前E3未实现，因此不能把“未新增模块”报告成真实全SC网络已无重复计算。
