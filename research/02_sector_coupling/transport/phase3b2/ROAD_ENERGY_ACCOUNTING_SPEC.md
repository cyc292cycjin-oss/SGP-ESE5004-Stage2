# Road aggregate final-energy accounting

## 定义与恒等式（本轮规范／分析推导）

对国家c和目标年y，统一使用MWh/year、同一最终用户计量端：

| 输入/变量 | 定义 | 检查 |
|---|---|---|
| RoadTotalFinalEnergy，R | 同年道路最终能耗总量，不含rail或供能转换损耗 | 来源、年份、单位、覆盖已接受；R≥0 |
| RoadElectricShare，sE | 该R内最终电能份额 | 0≤sE≤1；不是车辆或里程份额 |
| RoadFuelShare，sF | 1−sE，首版无直接FCEV | 与R同一final-energy分母 |
| EVFinalElectricity，E | R×sE，最终用户充电输入电量 | A*计量点一致；非电池牵引输出 |
| ResidualRoadFuel，F | R×sF = Σ_k F_k | 分别保留oil/gas/biomass/other及碳标签 |

`R = E + Σ_k F_k`。TWh→MWh仅乘10^6。不能把useful traction与final energy相加；没有km输入就不构造passenger-km、tonne-km或vehicle-km。

这是一个**联合外生最终能耗情景**：R和sE须共同描述目标年。恒等式不意味着一MWh燃油与一MWh电力提供等量运输服务；固定历史R后改变share不会自动给出正确的电气化效率收益。未来互联对照只要求双方使用相同已接受R/sE/F_k，不要求新增车辆服务模型。

## 与当前源码的关系（直接证据）

U `prepare_transport_data_input.py:115–140`从CO2百分比构造无量纲“平均效率”；`prepare_transport_data.py:128–180`将其与标作kWh/km的0.2组合。该链不能支持本规范的物理能量定义。旧DEC share又在`prepare_sector_network.py:2430–2453`同时缩放需求与车数；因此不得将DEC_2030=0.2等值直接改名为已接受的energy share。

`prepare_energy_totals.py:260–270`的上游total-road预测已有share/效率混合处理。选新R前必须核对，不能重复计入效率收益。本轮不给任何新R或sE数值，不修改旧CSV或生产函数。

**状态：替代accounting方法已定义；原road转换工程错误尚未关闭。** 首版assembly应绕开旧CO2-share/车数代理链，按本规范消费外生已接受能量账；本轮只做shipping工程候选，不声称road代码已修。

## 残余燃料身份

U `build_base_energy_totals.py:203–222`有road electricity/gas/biomass/oil分类。保留2019缓存中ID、MM、MY、TH的gas与ID、MY、PH、TH、VN的biomass为正，足以否定“总road全为liquid fossil”的默认假定。未来CSV子项因列对齐后fillna(0)出现的零不是燃料消失证据。[国别源复核](evidence/ACCOUNT_SOURCE_REVIEW.md)保留原值与来源。

最小数值接口可接受一个同年非负燃料份额向量b_k，Σb_k=1，令F_k=F b_k；或接受已知固定非油燃料量，油量作为余项并要求非负。两者均需共同确认数值，不能剪裁负值或将gas/bio自动换成oil。本轮不会新增车辆技术竞争。

## Phase4实施验收（尚未执行）

逐country/year检查R、sE、F_k完整且有限、同口径，恒等式在声明的舍入公差内通过。源数据舍入应保留差额，不能自动调节某个燃料平账。输出须携带source/hash/原单位/热值口径/转换/用户接受记录。Integrated与Disconnected输入散列相同。缺任何关键值即停止该国账户生成；不创造零值绕过。

补充证据与精确源码定位见 [ROAD_RAIL_REVIEW.md](evidence/ROAD_RAIL_REVIEW.md)。
