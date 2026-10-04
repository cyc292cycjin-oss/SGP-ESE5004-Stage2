# Transport carbon：范围冲突与漏记必须分开

**保留Full-SC交通后，现有共同大气账与原power-sector absolute trajectory会发生范围冲突；另有铁路油耗漏记及bunker排放加权问题。** 三者都影响系统级结论。本轮不修、不新增碳政策，也不把上游默认账追认为研究已冻结政策。

## 已核实的记账机制

`U/scripts/prepare_sector_network.py:1408–1446`建立`co2` carrier（factor=−1）及共享`co2 atmosphere` Bus和非循环Store。发电燃烧被转换为多端Link排放到该Bus，fuel carrier因素可能置零防止二次计算（`:3809–3832`）。

| 交通路径 | 直接/间接CO₂通路 | 限制 |
|---|---|---|
| Road ICE | oil固定Load+大气负Load，注入CO₂（:2520–2548） | 外生份额和能源代理的错误也会传入排放量 |
| Shipping oil | 大气负Load（:1807–1827） | bunker选择公式、节点油量缺值尚未闭合 |
| Aviation oil | 大气负Load（:1608–1628） | 同一bunker加权问题；不是只按名字判断kerosene无排放 |
| H₂终端 | 无直接CO₂；SMR/SMR CC等上游排放进入同一大气/储存账（:506–524） | H₂并非自动零碳 |
| FT synthetic oil | FT消耗stored CO₂；油品燃烧回排；DAC/capture参与净账（:344–380） | 共享燃料/捕集信用归属及完整循环必须闭合 |
| Rail oil | 只有直接oil Load，没有专属燃烧Link或大气负Load（:3696–3739） | 当oil carrier factor=0时，存在漏记 |

现有教程pre-strip直接观察：oil/gas/H₂ carrier的co2_emissions均0；co2为−1；48个oil供应Generator、48个rail oil Load；无rail命名Link，无rail大气Load。结合构造器可确认**该样本铁路油耗绕过燃烧排放账的结构路径**。该教程只有lv_limit，无活动CO2Limit，因此不是“已求解DEC违反上限”的结果。证据：`CARBON_LEDGER_OBSERVATION.json`和`NETWORK_TRANSPORT_EVIDENCE.json`。原始co₂ Load的加权单位为tCO₂，不能当MWh。

## Bunker false分支的代数问题

需求先合计domestic+international；false不移除国际燃料。令q_c为各国总燃料需求，r_c为domestic/total，I为排放因子。`:1616–1620,1815–1819`的表达式是：

`I × (Σq_c) × (Σr_c)`

而逐国国内义务应对应：

`I × Σ(q_c × r_c)`。

两者一般不等。这里是源码代数推导；缺值、港口分配与求和会进一步影响实际数值，未据此制造一个新的校正排放量。P也有此逻辑，不是U独有漂移。

## 原power cap不能自动扩到交通

`add_co2_budget`调用`prepare_network.add_co2limit`，GlobalConstraint的carrier_attribute为co2_emissions，没有power-sector选择器。若恢复非电需求，同一限额会约束更广的大气账；同时遗漏rail油又可能少计另一部分。禁用H₂/CO₂管道不会解决账本范围。

研究沿用的原DEC绝对轨迹为2025/2030/2035/2040/2045/2050：1000/820/640/460/280/100 MtCO₂/年；来源与已有等价性测试见Phase2 `CARBON_EQUIVALENCE_TEST.md`，未重跑。原power case还含其保留的供电H₂/燃料转换链，不能简化成仅coal/gas Generator。

版本问题独立保留：P读旧`co2_budget.co2base_value`；U读`co2.budget.base_value`，但ASEAN override仍有混合键`co2.budget.co2base_value`。旧顶层迁移不等于混合键已迁移。已知Phase2修复证据不能冒充当前冻结U源码已经修改。Baseline预算enable=false；DEC scenario打开预算后须检查实际消费键。见`U/configs/config.asean.yaml:171–182`、`U/scripts/prepare_sector_network.py:3626–3662`。

后续最小门槛：清楚区分原power ledger和完整SC报告账；界定共享H₂/FT/捕集信用；修复或解释bunker加权及rail漏记；所有比较侧使用相同政策和记账范围。这里列验收要求，未选择新的分摊政策、国家配额或执行修复。
