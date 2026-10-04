# Buildings + Heat 原模型对齐

审计日期：2026-10-01。范围仅 Buildings/Heat；无优化求解、无数据替换。数据仍 UNVERIFIED，human confirmation=PENDING。

## 版本与证据层

| 层 | 固定身份 | 本文能够证明的内容 |
|---|---|---|
| Paper Reference（P） | `5bacad702ccfed17ad19ab510fa710651e966f2c` | 论文代码及既有结果 metadata；最终为 power case，不等于完整 Buildings/Heat 已验证 |
| Upstream SC Baseline（U） | `a3616a68ee44592af6527ca9024a90f1956646ae` | 框架函数与 default+ASEAN 合并配置；不是一个已完成的全年 Full-SC run |
| Tutorial（T） | `ce327bfae2abe5526d4c1976173f0f8d08366ba5` 归档及保留输入哈希 | 2019 base、2030/40/50 中间表与六天热曲线诊断；不称为 P 或 U 全年结果 |
| Research Model（R） | 固定 U 的研究工作树，未合并本轮候选 | 待共同冻结；没有 DATA ACCEPTED Buildings baseline |

来源：[四层配置实录](../buildings_heat/evidence/CONFIG_LAYERS.json)、[两个 SHA 文件清单与哈希](../buildings_heat/SOURCE_MANIFEST.json)。下列代码链接默认固定 U 快照；P 快照平行保存在 `../buildings_heat/source_snapshot/paper/`。P→U 建筑脚本有修改，不能用“同一框架”替代逐版本核对；BDEW 和 existing-heating 原文件未变。P/U/T metadata 的 `only_elec_network=true` 都意味着末端热网络裁剪。

## 原作者实现链

| 原实现 | 来源及转换 | 最终组件/用途 | 问题与处理 |
|---|---|---|---|
| UNSD annual R/S | 2019，households/services transaction；million kWh÷1000，TJ÷3600，质量/体积×硬编码因子 | base country TWh | **结构可继承**；热值、体积口径、缺失及部门定义待核实 |
| base heat | 仅 Heat/direct geothermal/direct solar thermal；按 config 0.6/0.4 | space/water 两列 | 不是全建筑 useful heat；统一比例 `ASEAN_VALIDATION_PENDING` |
| future R | fuel shares、0.9 转换、growth/efficiency defaults；混合 service-like 与 fixed fuel energy | 一部分固定 fuel Load，一部分剩余 heat Load | 原模型是混合式，不能直接称为全建筑燃料内生替代 |
| future S | 原列乘 growth×efficiency；electricity services space/water=0 | 固定 direct-electric/fuel Loads；仅小量 heat commodity 进入热网 | 缺完整服务业终端供热转换链；0 不代表实测电热为0 |
| 国家→节点 | annual×人口份额，UNCTAD 城市份额划 rural/urban | nodal totals | R/S 同权重，无建筑面积/用途验证 |
| temporal shape | ERA5→atlite degree-day daily；space×BDEW，water仅BDEW；归一化×年度量 | hourly heat MW，再按时间聚合 | 正 annual+零 shape→NaN；原消费者 fillna(0) 丢量，E2 |
| `add_heat` | 五类热系统；DH按 urban/current/potential/progress 分配、负荷×(1+loss) | heat Bus/Load；HP/boiler/CHP Link，solar Generator，TES Store/Link | 各分布式系统分R/S，central Load合并；不是全过程两个账户 |
| `add_residential` | 固定油/气/生物质 H+N；剩余 heat target Q；覆盖 AC 为居民电力 | Load；CO2 emission Load | 最后国家循环重写所有 heat，包括S/central，E1 |
| `add_services` | 新增 services electricity、固定燃料 | Load | direct electric 本身没有独立 cooling demand；用居民电形状缩放服务业亦待验证 |
| distribution/final adjustment | 终端移往low-voltage；末端可裁剪热网、再校准总电力 | low-voltage Bus/Link；剩余 power network | electric heat扣减注释；services不在总量重标集合，E3；过滤名称单复数E4 |

代码入口：[base `calc_sector`](../buildings_heat/source_snapshot/upstream/scripts/build_base_energy_totals.py) L43–201；[future](../buildings_heat/source_snapshot/upstream/scripts/prepare_energy_totals.py) L108–255；[heat preparation](../buildings_heat/source_snapshot/upstream/scripts/prepare_heat_data.py)；[sector network](../buildings_heat/source_snapshot/upstream/scripts/prepare_sector_network.py) `add_heat` L2614、`add_services` L3033、`add_residential` L3247；[final adjustment](../buildings_heat/source_snapshot/upstream/scripts/final_asean_adjustment.py) L19–229。

**原模式结论（直接代码证据）**：固定年度量/外生燃料迁移 + 固定燃料终端需求 + 局部 heat-service 供给优化。供热技术主要通过可扩张 Link 连接电、燃料与热 Bus；热泵实际用电来自 Link dispatch/COP，不是 `electricity residential space` 列的同义词。目标 fixed heat service + endogenous supply competition 可继承框架，但还需数据与会计桥接，不能把这个目标描述成当前已完成状态。

## Annual quantity 与 fuel 分类

92 条本地原始行覆盖11国；既有审计用 U 聚合函数重算 R/S 12列与 T base 表存储精度完全一致。此结论关闭计算链，不接受数据。R base heat 全为0，S仅泰国有 direct solar thermal 422.867 TJ，舍入后拆为0.0705/0.047 TWh；其余“0”不证明无采暖/热水。见[原始行](../buildings_heat/evidence/UNSD_2019_BUILDINGS_ROWS.json)、[计算验证](../buildings_heat/evidence/ACCOUNTING_VALIDATION.json)。

分类：A固定 final demand（heat另注明固定服务量）；B外生转电；C外生分到热用途；D可优化供给替代；E忽略；F口径不明。一个燃料可能分成多条路径，不能只给一个字母。

| Carrier | Residential 当前 DEFAULT | Services 当前 DEFAULT |
|---|---|---|
| electricity | A；加非热油品转电B及base煤转电B；其中电热/制冷子项F | A+base煤转电B；没有独立电热分项来源 |
| coal | B（1:1热值并入电力）；若开关false则E | 同左；没有 Buildings coal Load |
| gas | C分到热用途，但热与非热部分最后均为A；默认热/非热转电0 | A；不做居民式拆分 |
| biomass | C分到热用途但仍A；默认转电0；现有固定燃料不能被HP替代 | A |
| oil（含LPG等） | A固定剩余热/非热燃料；B非热转电；C热分配后只有被划入Q的部分可D | A |
| heat commodity | 固定服务Load+A的外生量，供给D；但供热口径F | 同左，数据仅少量直接热商品 |
| other | 本地92行均能落入六组；未单列商品是F，不填0；若原函数漏组则E | 同左 |

质量/体积燃料的 TWh 只是**复制模型转换结果**；HHV/LHV、燃料含水率和 Fuelwood 的体积因子仍需接受。没有把 final fuel consumption 当 useful heat。转换公式及 DEFAULT 的精确来源沿用[上轮 fuel trace](../buildings_heat/BUILDINGS_FUEL_SHIFT_TRACE.md)。

## 电力守恒与 CSV 阅读规则

[BUILDINGS_DEMAND_ACCOUNTING.csv](BUILDINGS_DEMAND_ACCOUNTING.csv) 有99行、45列：11个国家2019电力总账，22个2019 R/S原始账，66个2030/40/50教程中间账。TWh 是能量单位，**不消除 final energy 与 useful heat 的口径差别**。

`base_electricity_TWh` 在国家2019行专指 UNSD 全国 **Final energy consumption**，不是发电量/供电量，也不是 DemandCast/GEGIS 网络积分。`residual=base−raw R electricity−raw S electricity` 是分析者构造的残差，不是另一份实测部门数据。11国在1e−9 TWh容差内闭合、残差非负；R/S煤转电没有混入这个原始电力恒等式。国家行不能与同一国家部门行再求和。

空值意为未知/不适用；raw某燃料未报告≠0。`reported_final_energy_subtotal` 仅已报告商品按模型因子换算的小计；不是数据完备性证明。未来 `annual_total` 留空，因为不能把固定燃料、热服务、电力重复相加。`explicit_heat_related_electricity` 未观测，`endogenous_conversion_electricity` 未求解，均留空而非0；Q只记录在 `modeled_remaining_competitive_heat`。

冻结的会计目标是：

```
accepted direct electricity = validated residual + explicit direct sector electricity
metered electricity = direct electricity + actually represented historical electric end uses
future system electricity = accepted direct electricity + optimized conversion input + defined losses
```

从 historical meter 切到 explicit heat service，必须用同年同部门桥接表扣出**同一项**既有电热耗电。Heat service不能与电力相加叫“电力总量”。当前注释掉的 `electric_heat_supply` 来自默认份额，不是实测扣减量，不能简单取消注释。E3合成例：总量目标1、保留S=3，函数把所选AC改为1后总计4 TWh。见[E3证据](evidence/E3_ACCOUNTING_DEMONSTRATION.json)。这不是 ASEAN 数值预测。

## Cooling、Cooking、DH、既有设备

**Cooling**：冻结函数内没有独立制冷服务、chiller或冷储能负荷；官方SG终端调查支持制冷属于居民电力。故 `Cooling ⊂ Direct electricity` 结构可继承；但现有aggregate recalibration与电热扣减未闭合，不能证明当前11国网络已无重复。待会计桥接通过，才可写“Full-SC结果包含cooling electricity demand，但不包含cooling technology flexibility”。本轮没有Full-SC结果可作此宣称。

**Cooking**：本轮针对R/S入口、热准备、sector network的固定源码检索未发现独立模块；不新增。原燃料统计无end-use拆分，统一热份额有把烹饪或其他用途送入space/water的风险。AEO8与印尼对照见[候选源报告](BUILDINGS_ASEAN_DATA_CANDIDATES.md)。目前不能保证其影响很小，需共同决定燃料用途边界，不自行扩大研究范围。

**District heating**：当前份额表DEFAULT=0；config potential=.3/progress=1/loss=.15，因此0既有份额仍会生成DH。CSV potential列并非实际计算入口。人口城市份额不是热密度论证。结构测试在potential=0且current=0的**合成条件**下，R/S分布式热量完整保留、四类分布式HP仍在；中央Bus/Link依旧可能建立，因此“DH负荷份额为0”不等于完整移除中央技术。是否将DH作为首版共同边界不是模型结构必然要求；没有证据为11国逐一确认适用城市，本轮不改配置。详见[测试](evidence/E1_after.json)。

**Existing heating**：EC WP2/2012 EU28+3建筑设备、排除DH；ASEAN行缺失，DEFAULT空→0。[固定资产处理代码](../buildings_heat/source_snapshot/upstream/scripts/build_existing_heating_distribution.py)生成表；`add_existing_baseyear`的heat导入调用整段注释，当前不等于历史设备已进入网络。后续brownfield能继承此前优化建设的设备，与已有真实stock不同。建议表述“existing heating stock未显式表示”；是否接受building greenfield competition由用户决定，不强求伪造ASEAN brownfield。
