# Road EV与A*：exactly-once契约

## 基年转移

A*定义为完整终端电力父账户。设h_EV为经来源证实、确已包含在同country/year/计量点A*内、将由显式EV表示的历史电量。则：

`Direct_base = A*_base − h_Buildings_explicit − h_EV`

`Direct_base + h_Buildings_explicit + h_EV = A*_base`。

Rail继续embedded，不额外扣h_rail、不另加独立rail电Load。Buildings的已冻结处理保持其自身契约，不能重复扣除。每笔转移记录parent_id、service/account_id、source年度、量、单位、包含证据、目标组件ID；同一笔最多转移一次。Direct不能负值。

**真实数据状态：PENDING。** 11国缓存road electricity=0来自未命中Electricity-road原行的空集求和，不能证明h_EV=0。旧保存网络AC又经历Residential重写、损耗乘数和后续校准，名字相同不证明就是本研究A*。[上一轮排重证据](../phase3b1/TRANSPORT_ELECTRICITY_DOUBLE_COUNT_AUDIT.md)与[本轮复核](evidence/ROAD_RAIL_REVIEW.md)保留这些证据限度。

## 未来目标年

`EV_y = R_y × sE_y`。未来Direct_y须排除同一EV目标服务；不能让历史EV随Direct增长后，再加入完整EV_y。基年h_EV只用于基年转移，不能用未来EV_y直接扣历史A*。AEO8 gross generation不作为新增需求约束，final-electricity曲线不自动变成完整未来固定Load。

因此“exactly once”规范已成立，但未接受年度父子账和未实际组装前，不声称11国已验证。

## 固定充电形状与deferred flexibility

首版采用明确计量于网侧终端输入的固定EV电Load。令节点份额a_n≥0、同国Σa_n=1；非负外生形状q_t，代表小时权重w_t；定义：

`P_EV[n,t] = E_EV,c × a_n × q_t / Σ_t(w_t q_t)`。

全年代表权重下Σ_n,t w_t P=E_EV,c（MWh）。形状分母须有限且>0。曲线可用被接受的简单固定形状，不从未经接受车辆数推断充电容量。当前European traffic shape仅是候选代理，并非ASEAN观测。

U `prepare_sector_network.py:2471–2502`的v2g=false、bev_dsm=false能在新网络构建时不创建逆向V2G Link与EV Store。因此两项可defer，不需要研究smart charging。旧charger仍有车数×0.011MW×share容量及availability限制、旧q仍有量纲错误：只关两个开关不是整体修复。

若保留正向charger，其无储能、唯一出路为固定负荷时满足η p_charge=q_battery，不能移峰；必须将网侧E换成q_battery=η P_EV，不能把网侧E当电池侧后再除η。首版直接网侧Load无需额外接受charger效率或车数参数。

Phase4验收：旧road代理链退出；无EV Store/V2G；没有车数导致的隐含峰值约束；同一service_id没有父账和显式账双保留；年度电量守恒。调整config不会自动清除旧保存网络组件。本轮未组装或求解。
