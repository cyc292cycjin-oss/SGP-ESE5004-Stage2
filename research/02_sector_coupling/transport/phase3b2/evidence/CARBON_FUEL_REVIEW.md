# Phase3B-2：双碳账与固定燃料义务有界复核

本文件仅支持本轮Transport收口与Phase4组装。**用户已冻结模态选择；这里不重新提出交通技术方案，不修改正式碳约束，不运行模型。** 核查基于Phase3B1保留的源码、原始行提取和网络静态证据；没有新增数据或数值接受。新合同是设计要求，不等于冻结U源码已经实现双账。

固定身份：P `5bacad702ccfed17ad19ab510fa710651e966f2c`；U `a3616a68ee44592af6527ca9024a90f1956646ae`；V `50a73d8f531132c5459174a55cac412d5f684462`。下文`U/...`均指`../../phase3b1/evidence/source/U/...`的冻结行号。

## 1. 合同结论

分别建立：

- **PolicyCO2_Power**：原电力案例边界的区域绝对CO2轨迹。DEC2025/2030/2035/2040/2045/2050依次1000/820/640/460/280/100 MtCO2/年；不是新增全系统碳上限，也不向每国复制此上限。Baseline保持原预算关闭语义。
- **ReportingCO2_FullSystem**：所建模系统内各排放、捕集、碳去向的一次性物理报告账，覆盖电力、直接交通燃烧及其被显式建模的燃料供给。国内与国际bunker分开列示；不附加新的统一cap。

**全系统报告账包含电力排放事件，不能再把PolicyCO2_Power加到ReportingCO2_FullSystem得到“总排放”。** 两者是同一批事件的政策视图与完整报告视图，不是两个互斥排放量。

**为EV、rail embedded用电、电解、FT及其他转换供电的发电排放仍进入Power政策账。** 终端用途是Transport，不改变这部分发电属于电力系统的事实。只有直接交通燃烧及明确归属于非电终端的燃料供给排放为报告项，不因恢复Transport自动塞入原电力cap。不能把所有“交通相关”排放都排除出Power账。

证据边界：上述两账与模态处理来自本轮用户冻结要求；原碳轨迹与作者电力案例含供电H2/SMR链，来自已保存的`phase3b1/evidence/prior/research/01_baseline_construction/CARBON_EQUIVALENCE_TEST.md`及`PAPER_CARBON_ACCOUNTING.json`；本轮没有重跑旧测试。

## 2. 每类能源流的碳账去向

| 能源流/过程 | 物理排放来源 | PolicyCO2_Power | ReportingCO2_FullSystem | 最小约束 |
|---|---|---|---|---|
| Road EV与嵌入rail electricity | 供电端发电及原电力转换链 | 计入对应发电事件，与电力其他用途同口径 | 同一事件一次 | 不能又按电网平均因子向交通总账重复加一遍 |
| Road residual fuel | 经接受的实际燃料燃烧 | 不自动纳入原power cap | 直接燃烧计一次 | 与Road/direct fuel转移互斥；不能无依据把所有原始gas/biomass都改为oil |
| Rail embedded fuel | retained direct-fuel账户中的铁路燃料燃烧 | 报告项，不因rail而纳入 | 必须保留；embedded不是零排放 | 不另加rail fuel Load，但保留该燃料份额在直接燃料排放中 |
| Domestic shipping | 固定国内燃料义务燃烧 | 报告项 | 国内shipping行一次 | 不能同时完整保留在普通direct fuel与独立shipping账 |
| International shipping bunker | 单列国际海运供油义务燃烧 | 报告项 | 单列bunker行一次 | 不自动归作国内最终消费，不外推航线/船旗责任 |
| Domestic aviation | 国内固定kerosene/fuel义务燃烧 | 报告项 | 国内aviation行一次 | 保留原始commodity覆盖边界 |
| International aviation bunker | 单列国际航空bunker燃烧 | 报告项 | 单列bunker行一次 | 不自动并入国内最终消费 |
| 电解供FT所需H2 | 电解AC输入所引起的发电排放 | 计入供电排放 | 供电事件一次 | 电解无新的燃烧CO2项；不把同一用电预装进A* |
| SMR/SMR CC供H2 | 天然气转化排放和capture | 服务电力转换链的可追溯份额仍计入；非电份额不可整批灌入 | 全部显式物理排放/捕集一次 | 原论文已有SMR链不可整类从Power账剔除 |
| FT及其辅助电力 | H2/CO2/AC多输入与下游油品燃烧 | FT供电排放仍计入；下游Transport直接燃烧为报告项 | 碳输入、燃烧回排及供给事件闭合 | 合成油并非自动“零排放油” |
| DAC/点源捕集、储存、循环 | CO2从原来源转移/吸收/封存/再排 | 原power边界允许的信用保持可追溯；不得把非电信用任意挪来抵power cap | 按实际物理碳流报告 | 同一捕集量不能重复减排；利用不是永久封存 |

报告范围是**实际建模的系统**。外部进口燃料的未建模开采、运输等生命周期排放不得凭空添加，也不得宣称已完整计算。报告应标出这些范围外项目；不要把当前CO2模型擅自升级为完整温室气体/CO2e核算。

## 3. 现有源码为何不能直接当双账实现

已核实：

- `U/scripts/prepare_sector_network.py:1426–1446`建立`co2_emissions=-1`的共同`co2 atmosphere` Bus/非循环Store。它没有按power/transport区分。
- 发电燃烧转换为多端Link，在`:3809–3832`排入该大气Bus，并把对应燃料carrier因子置零避免燃料与大气双计。供电SMR/SMR CC同样经`:506–524`进入共同碳账。
- Road oil`:2520–2548`、shipping`:1807–1827`、aviation`:1608–1628`创建直接燃烧的大气负Load。其数量来自需求，不能一边保留旧负Load、一边新建报告排放后再把二者求和。
- `add_co2_budget:3626–3662`调用`prepare_network.py:149–156`的`add_co2limit`；消费`carrier_attribute=co2_emissions`，无power边界选择器。因此把Full-SC共同大气Store直接绑定原cap构成`SYSTEM_LEVEL_BLOCKER`。
- 关闭H2管道或CO2管道不会分离排放范围。复制共同大气总量并更名为Power账也不解决问题。

旧/新配置键问题独立保留：U ASEAN override是`co2.budget.co2base_value`（`config.asean.yaml:171–182`），当前消费是`base_value`（`:3642`）；旧顶层迁移不等于混合键自动正确。Phase4必须复用已记录的键和值等价性要求，不改六个年度限额。**数值限额相同不证明统计范围相同。**

## 4. 共享H2、SMR与CO2信用的最小工程合同

不重新开启Transport模态讨论；将下列内容作为Phase4统一能源账实现条件：

1. 每个燃料/排放/捕集事件有唯一ID、物理单位、时间权重、来源组件、上游碳来源和目的用途标签。系统报告只计一次；Policy视图只取符合原power范围的事件/份额。
2. 共享H2池可能同时服务发电和FT等非电用途。不能凭`carrier='SMR'`把全部SMR排放划给power，也不能为满足“Transport report-only”把全部SMR移走。Phase4需要守恒的用途流量标签或等效项目层线性账；内部转移不创造额外需求、产能或排放。不得未经说明用任意固定比例切分共享产量。
3. 对电解和FT的**电力来源**不做“交通豁免”：发电端排放仍在Power账。共享SMR等非电转化来源的归属与这一供电规则是两件事。
4. FT消耗stored CO2（`:344–380`），DAC从atmosphere转移至stored CO2并消耗AC与热（`:2988–3029`）。Transport燃烧回排、CO2利用和永久封存必须能分别核对。点源捕集送去燃料后再燃烧，不应被两个账各当一次永久负排放。
5. 不能在未实施归属前允许共享carbon pool把“非电减排信用”自由抵扣原power cap。若原power-reference样本包含特定capture/SMR机制，Phase4需在退化为paper电力边界时复现其表达式，再验证新增非电义务不会悄悄扩大/缩小政策范围。这是等价性验收，不是新碳政策。
6. 不把政策账和报告账各自建成一套无关联的真实燃料系统。两账须使用同一实际调度流；账面标签不得复制能源供给。

**有限的跨部门连接提示：** 当前`add_dac`只从`urban central heat`或`services urban decentral heat`母线生成DAC（`:3003–3005,3016–3029`）。Buildings第一版不强制显式热服务后，Phase4应确认被保留FT选项仍有合法、带成本的CO2来源及DAC所需热供给，或明确其实际可用性；不能给FT免费CO2、凭空添加Buildings热需求，或把“FT组件存在”写成“FT已具有可行供给链”。这是组装依赖检查，不需要恢复Buildings/Transport深挖。

## 5. Rail embedded仍要补齐报告碳账

`U/scripts/prepare_sector_network.py:3696–3740`只建rail oil/electric Loads，无rail燃烧Link或大气负Load。`:3831–3832`的油carrier置零后，普通油Generator→rail油Load可绕过碳账。

已保存`phase3b1/evidence/CARBON_LEDGER_OBSERVATION.json`对样本SHA256 `4b406321f2cc7c0170e2b48d20cdbddc16e9ffb16e2f37cabc97cb9d8788c8ae`确认：oil/gas/H2因子均0、co2因子−1；48油Generator；无rail命名Link；完整大气Load列表无rail。与构造器合并可确认样本的铁路油耗遗漏结构。样本只有`lv_limit`，没有活动CO2Limit；**不是已求解DEC超限结果**。

新第一版rail=EMBEDDED：不再新建独立rail能源Load，但retained direct electricity/direct fuel必须能证明含该能耗一次；rail燃料燃烧进入retained direct-fuel报告事件。禁止保留旧rail Load再保留完整direct账户，也禁止删rail Load后连应保留的能耗和排放一并删去。来源缺值不能当作零；不能因无独立rail组件而漏记FT油中的循环碳回排。

## 6. Domestic / international源语义与固定义务

用户已决定四个独立账户；这关闭了“是否并入国内”这一边界讨论。来源允许恢复的是**交易账户**，不是乘客/货物出行需求或船旗、航空公司责任。

| 新账户 | 冻结源交易筛选 | 原始/输出单位、年份 | 保留的解释边界 |
|---|---|---|---|
| DomesticShippingFuel | `Consumption by domestic navigation` | 2019观测；原始单位逐行保留，转换TWh/年 | navigation匹配商品总和；不是tonne-km |
| InternationalShippingBunkerFuel | `International marine bunkers` | 同上 | 单列bunker交易；不自动并入普通国内最终消费 |
| DomesticAviationFuel | `Consumption by domestic aviation`且`Kerosene-type Jet Fuel` | 同上 | 此过滤不含所有可能航空燃料，不能伪称完整航空服务 |
| InternationalAviationBunker | `International aviation bunkers`且同一jet fuel商品 | 同上 | 单列国际航空交易；非国内义务、非航线分摊 |

源行：`U/scripts/build_base_energy_totals.py:262–292`；country/year过滤`:450–456`；质量、TJ与电量转换`:108–132`；系数`_helpers.py:1837–1907`。现有缓存`UNdata_Export_20250502_*`的文件名日期是导出线索，**不是2019观测变成2025**。Phase3B1的`CACHED_DEMAND_EVIDENCE.json`保存原始行、文件hash、单位和footnote，已有107/121非空base单元与当前缓存一致；14空单元不接受为零。

代码只能证实上面四类交易不同；不能证实任意外部“national final energy”父总量是否已经含它们。因此Phase4输入清单需对国内两项做direct-fuel互斥转移/包含性记录；国际两项作为独立bunker义务，避免再从国内父账户无依据扣减或添加。原统计归属国家不等于研究已经分配国际减排责任；第一版保留报告国账户标签即可，不做国家分配经济学。

上游`add_shipping:1709–1711`和`add_aviation:1569–1571`把国内+国际先合并。新合同必须保留四账户ID，即使共用同一oil供应Bus也不能丢掉账户身份。原`international_bunkers=false`只切排放，不删燃料需求，不能拿这个flag替代新账户规则。

原false分支`:1616–1620,1815–1819`是`I × (Σq_c) × (Σr_c)`，非逐国`I × Σ(q_c r_c)`。Phase4应直接按分开的国内/国际燃料账户算燃烧报告，各算一次；不继承这个比例重建错误。这里是源码代数结论，本轮不产生校正后的国家排放量。

未来年份的增长/效率来自`prepare_energy_totals.py:63–109,272–296`；缓存CAGR无ASEAN行，落入DEFAULT；末尾fillna(0)会吞缺值。这些数值不会因为四账户语义冻结而自动获科学确认。Phase4按“accepted quantity/version + explicit missing status”消费，不能再静默继承未确认默认预测或空值变零。

## 7. 固定燃料义务与内生合成供给不能重复

冻结选择：Road residual fuel固定/记账；四类Shipping/Aviation燃料义务固定；FT为显式供应选项。Direct shipping H2、Road FCEV、marine NH3/methanol均deferred。

- 油品终端义务由化石油供应或已有FT路径满足。供给竞争不等于飞机/船舶技术竞争，也不改变终端固定义务的计量基准。
- `FT:344–380`使用H2输入、oil输出、CO2存储输入和独立AC输入；`H2 Electrolysis:420–425,651–684`产生所需H2的AC输入。两类输入均由物理Link流量产生，不预装进固定A*。
- 不得再为同一FT运输义务增加固定“所需H2 Load”，否则FT实际H2消耗与额外H2终端义务会重复。也不得把全部FT电耗预置为固定Load后再让Link耗电。
- **独立固定H2需求+满足它的内生产氢本身不是重复。** 本轮禁止的是同一运输服务已由FT义务表示，又加一次预计算H2/电力义务。检查对象是account/service ID与流量，不是见到H2 Load就全部删除。
- 同一油Bus下的化石/FT供应无需新增需求；物理燃料守恒和报告碳循环都必须核对。油品规格、掺混、船/飞机细分是第一版限制，不阻塞最低基准，也不被宣称已验证。

## 8. 年度与简单时序：接受简化，但不声称完全无影响

当前航空`:1590–1605`、航运`:1733–1739,1790–1804`把年TWh乘1e6/8760变成静态MW。可作为第一版简单分配形状的来源，不是实测航班/船舶时序。

Phase4最低检查是每个country、year、domestic/international账户：`Σ_node, t physical_weight[t] × fuel_load[node,t] = 该模拟权重对应的年燃料义务`。若权重代表全年即核对全年MWh；若代表部分年度，必须明确年度缩放，不可同时套两遍8760/Nyears。港口/机场节点权重每国非负、有限、和为1；国家有义务但无可分配节点时应失败并保留原数量，不得NaN→0。

**同年度总燃料不保证相同成本、峰值或互联收益。** 平坦燃料消费与有成本/有容量限制的油/H2储存、FT最小负荷（default0.9）以及电解时序会共同影响供电配置。因此本轮接受用户允许的简单时序作为透明基准，不证明其与精细行为模型“年度系统价值完全等价”。保留此限制即可，无须开新Transport敏感性阶段。合成燃料所需电力由生产调度内生形成，不能因为燃料Load平坦而把制氢/FT电力也固定平坦。

## 9. 交给Phase4的最小验收要求

以下是工程实现/集成验收，不是新Transport研究轮次，也不是本轮已通过的新测试：

| ID | Phase4必须满足 | 可有界验证的性质 |
|---|---|---|
| CF-01 | 保留四个年度燃料义务及原始ID；country/unit/year匹配，missing不被补0 | 源数量不变；按国家/模式/国内国际汇总对账 |
| CF-02 | EV、电解、FT电耗exactly-once；rail能源嵌入direct账户一次 | 预置A*与转换义务互斥；删除独立rail组件不丢能耗 |
| CF-03 | 物理全系统碳报告与Power政策视图分离 | 只增非电燃烧时，固定同一电力调度的Power账不变；全系统报告增加正确燃烧量 |
| CF-04 | EV/FT诱发发电仍在Power cap | 新增发电排放进入Power；不能靠终端用途标签获得豁免 |
| CF-05 | 共享H2/SMR/FT/capture按守恒用途计账 | 原power退化案例预算表达一致；相同碳流/信用不重复；运输燃料循环闭合 |
| CF-06 | Rail燃料排放跟随retained direct fuel，而非依赖独立rail Load | 已知rail遗漏结构消失；不能以zero oil factor遗漏燃烧 |
| CF-07 | 国内/国际燃烧分别按燃料量报告，不继承bunker比例错误 | 分区之和等于总燃烧；与节点/国家分组次序无关 |
| CF-08 | 年/节点/时段燃料守恒；FT合法CO2与辅助能源来源可达 | 无非有限权重/负数量/静默丢量；同一数量只年化一次 |

验证政策范围时“增加非电燃烧不改变Power账”须**固定电力调度进行会计比较**；若新增Transport使发电量变化，Power排放随发电变化完全符合原政策，不能把它判成范围污染。无需正式Integrated/Disconnected求解来检查上述结构与等式。

结论：Transport模态与双账概念合同可随本轮收口；现有U不是已实现该合同的Future Research Model。剩余CF-01–08属于Phase4最低组装条件，不应再拆成Phase3B-3/B-4交通深挖。这里不声明正式求解准备完成，也不替任何未确认输入赋值。
