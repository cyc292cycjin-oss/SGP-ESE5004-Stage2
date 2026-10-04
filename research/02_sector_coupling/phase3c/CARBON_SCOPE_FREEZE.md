# Carbon scope冻结：目标架构，不改正式约束

## Policy与reporting

**PolicyCO2_Power**保持原ASEAN power-system范围。DEC轨迹：2025=1000、2030=820、2035=640、2040=460、2045=280、2050=100 MtCO2/year；Baseline按原预算关闭语义。没有新国家配额、carbon intensity政策或全系统cap。

**ReportingCO2_FullSystem**报告实际建模的power、industry、transport、buildings fuels、shipping、aviation、agriculture及其他保留部门的物理CO2。Power事件在报告中出现一次；两个视图不能相加。缺失工业process排放不自动0，范围外生命周期/其他GHG不伪称已计入。

| 事件 | PolicyCO2_Power | ReportingCO2_FullSystem |
|---|---|---|
| 发电，为任意终端或转换供电 | 计入；EV/HP/电解/FT用途不豁免 | 同一物理事件一次 |
| 原paper供电H2/SMR及被保留geothermal等 | 保留原口径，不能只按化石Generator名字筛选 | 完整物理事件一次 |
| Buildings/Industry/Transport/Agriculture直接燃料燃烧 | 不因恢复sector自动并入Power cap | 按实际fuel与计量范围报告 |
| 国内/国际shipping与aviation | 同上 | 分domestic/bunker，不用失真的区域比例重建 |
| 工业非能源feedstock/过程排放 | 不自动并入 | 来源/碳去向可追踪，避免将全部oil视同立即燃烧 |
| 共享SMR/H2、CHP、capture/DAC/FT | 仅属于原power边界的守恒份额/信用 | 所有真实碳流一次，利用与永久封存分开 |

共享用途/CHP归属方法的实际映射须在Phase4共同接受并写成可测表达式；不得以任意比例或技术名称替代来源/用途，也不得为两账复制物理供给。这个实现决定已落在统一架构内，不再开新碳政策或Phase3D。

## 已有证据与必须处理的冲突

U `add_co2:1408–1500`建共同atmosphere及physical stored CO2；`add_co2_budget:3601–3662` / `prepare_network.add_co2limit`按co2_emissions建global constraint，没有power用途过滤。恢复非电部门会把其排放一起放进原cap：**SYSTEM_LEVEL_ENGINEERING_BLOCKER，交P4-06**。

已完成的Phase2键修复候选 `753ac81c23f8b9a1ca8ceed531d0630b56f6953d`恢复base_value消费与六年原限额；只证明key/value等价，不能证明scope等价。旧0.4→0.65 t微型演示与paper网络读取已留证，不重跑。

物理CO2与报告大气另有空间问题：co2_network=false依旧共用stored池；工业process emissions可共池捕集。国家内CCS/FT不能从外国共享物理碳池取料。U `solve_network.add_co2_sequestration_limit:939–952`汇总stored CO2末期库存；default的欧洲潜力/价格不能未经接受当作ASEAN或复制给每国。资源/时间尺度与信用的两个问题都须检查，不能把封存上限当Power预算。

## Phase4验收契约（本轮未运行）

1. Paper退化边界的排放表达式、六年绝对值及时间缩放与原参考一致，含其供电H2/SMR与非零carrier因子。
2. 固定电力调度，仅添加非电直接燃烧时Policy账不变、FullSystem正确增加；若新增用电改变发电，新增发电排放正常进入Policy。
3. 同一燃料不在源Generator、燃烧Link和报告负Load重复计；rail燃烧、工业煤能流/排放、农业保留燃料均有归属。
4. 物理CO2来源、capture、FT使用、燃烧回排、永久封存和跨期库存守恒；非电信用不可无依据抵Power；不共用跨国物理仓库。
5. 共享用途标签合计回到同一实际流；两情景使用相同原区域预算及scope，不复制成11个国家配额。

本轮只冻结目标架构；没有修改policy数值、constraint代码或重新执行solver。
