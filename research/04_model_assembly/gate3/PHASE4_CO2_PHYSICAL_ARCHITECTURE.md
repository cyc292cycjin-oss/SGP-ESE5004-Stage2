# 物理 CO2 与报告大气隔离

上游 `add_co2:1409–1543` 在 co2_network=false 时仍使用共同 co2 stored pool；不同国家的 capture、FT 与储存可以通过该物理池相连。开关 false 不能证明没有跨国 CO2 协同。新方案不通过开启跨国 pipeline 消除这个问题。

三类账户：

| 对象 | 物理角色 | Research 归属 |
|---|---|---|
| ReportingCO2 atmosphere | 环境/报告账；DAC 可从环境取碳 | ALLOWED_ACCOUNTING_GLOBAL，policy carrier factor=0 |
| co2 captured | 捕集后可供本地 FT 等使用的原料 | 国家/节点独立；须另有来源追踪 |
| co2 sequestered | 永久地质库存 | 国家/节点独立、不可回取、不允许供 FT/vent |

捕集池可流向当地地质库；地质 Store 使用 e_nom_extendable=true、e_nom_max=接受容量、e_initial=0、e_cyclic=false，保留 capital_cost 的投资成本含义。显式 `Store-p <= 0` 阻止回取。不能把原每吨容量成本默改成吞吐边际费用。

上游 `solve_network:939–954` 的末期总库存 <=200 Mt 是另一个资源限制，且默认潜力带欧洲 TODO；它既不是 Power 碳预算，也不是各国200 Mt。本轮不采用或分配这个值。

FT 的 H2、captured CO2、电力输入与油输出全部属同一国家。多端口输入为负 efficiency2/3，测试检查符号与 p_min_pu>=0。地质库存不进入 FT。共同 atmosphere 不能用于点源捕集的跨国搬运；环境移除须显式 accepted DAC/origin 语义，不自动创建 DAC。

工业 process emissions 共同池失去国别/来源，不能沿用后再宣称隔离。必须在已接受的工业输入与映射上重建，当前 deferred。物理隔离不等于已完成混合 CO2/oil 池的来源核算，真实流归属仍是 blocker。
