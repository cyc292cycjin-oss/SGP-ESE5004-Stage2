# Shipping：国内燃料与国际bunker两个固定义务

## 来源与账户

| 账户 | 原始统计交易身份 | 第一版表示 |
|---|---|---|
| DomesticShippingFuel[c,y,k] | 国内navigation消费；必须覆盖已核实的by/in标签 | 固定终端燃料，证明与domestic direct-fuel父账互斥 |
| InternationalShippingBunkerFuel[c,y,k] | International marine bunkers | 独立国际bunker固定义务，不自动并入国内final energy |

当前缓存基年2019；UNdata_Export_20250502文件名为导出线索，非观测年。原始单位/commodity/footnote逐行保留，U `build_base_energy_totals.py:108–132,278–292,450–456`过滤转换到TWh/year。燃料转换见U `_helpers.py:1837–1907`；热值/HHV-LHV及正式采用仍待确认。不是tonne-km或船舶活动。

[44项国别原值](evidence/COUNTRY_ACCOUNT_OBSERVATIONS.json)保留11国四类燃料账户。shipping的BN/LA/TL国内与国际共6格空缺，不能补零。KH等空集零也不是物理零。SG国际海运缓存535.3418 TWh是bunker义务观察，不能当普通国内用能或预先全部转成电力。

## 已定位的静默丢量入口

U `build_base_energy_totals.py:287–291`只选`Consumption by domestic navigation`。已保留的柴油原行使用`Consumption in domestic navigation`，四国未进入缓存国内总量：KH 58.442、ID 719.982、PH 539.6、SG 76 thousand metric tons。原文件hash `1c2952a5f87bfcdb0eef1af6b6c774e741a99e5b72c5ced91a585d6efe9be50a`，行15124/43709/74182/82779。精确原行/单位/诊断换算见[源复核](evidence/ACCOUNT_SOURCE_REVIEW.md)。

这是直接原行与代码对照，不是新增数据猜测。诊断正能量不等于已接受的新国家总量；本轮不改筛选器、不改CSV。Phase4输入接受时须按原始交易/商品去重重建国家账，不能把所有keyword行相加。该缺口与缺失国家量合并为一个年度源账门槛。

## 固定需求、内生供给

终端fuel义务固定；化石油及现有FT供给可竞争。不新增直接H2船、NH3/methanol船或船型选择。两个账户可共用油Bus，但保留不同ID和报告行；国内已有父fuel账户须作exactly-once转移，国际不无依据从国内父账扣减。

U目前先将国内+国际相加构造shipping Load。独立分配候选内部保留两列年度账并分别验证守恒，但兼容旧构造器仍输出合计oil Load，**不等于正式Research Model已实现两个独立终端账户**。Phase4可采用两个命名Load，或一份物理Load配可核对的两个账本子项，不能两种物理需求同时加。

## 空间、时间、碳

优先现有ports/coastal节点；缓存10个有港口国家的fraction各和为1，LA无港口。实际节点所属国仍须校验。有正需求而无有效港口需明确失败或使用另行接受的country节点分配，不能补造港口或悄悄变零。

使用固定年度义务加简单归一时序，Σ节点/时段物理权重×MW=国家年MWh。候选修复的测试范围与局限见[工程报告](TRANSPORT_ENGINEERING_FIX_REPORT.md)。港口权重归一不等于完整网络年度守恒。

直接燃烧入FullSystem报告，保留domestic/international两类；供FT的发电排放仍入Power cap。旧international_bunkers=false并不删除国际燃料且比例公式存在多国乘和错误，不用它代替双账合同。本轮不修carbon。

未来CAGR采用DEFAULT的旧2030/2040/2050值仍UNVERIFIED；本轮没有选择新年份或增长路径。
