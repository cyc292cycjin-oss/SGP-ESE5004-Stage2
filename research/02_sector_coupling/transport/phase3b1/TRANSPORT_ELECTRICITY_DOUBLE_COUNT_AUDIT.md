# Transport electricity：父账户与转换输入

**存在可证明的重复计量路径，但尚不能从现有数据核定某份最终网络重复了多少交通电量。** A*已冻结为最终用户电力消费；现实历史road EV、rail及其他electric transport在同域最终电力账户中属于子项。当前实际输入经过Residential覆盖、AEO generation校准及损耗处理，尚未证明它就是该A*。不能把概念上的包含关系冒充数值闭合。

## 原代码实际做什么

- `U/scripts/build_base_energy_totals.py:203–222,246–260`抽取road electricity和electricity rail。
- `prepare_transport_data.py:172–180`非custom陆运代理以`road + rail − electric rail`为基数。这里的减electric rail是在**陆运能源代理内**排除电铁路，绝非从父AC Load中扣除历史电铁路。
- `prepare_sector_network.py:2311–2550,3696–3739`只增加陆运/铁路组件，没有执行父电力账户对应扣除。road electricity字段在该后续陆运链没有用于历史转移。
- `prepare_sector_network.py:3247–3410`的Residential处理会改写原AC，之后`:3452–3476`的0.97与低压接线也不是交通扣除。
- `final_asean_adjustment.py:83–87,177–233`对选定Load做增长校准：EV明确排除；rail因字符串缺逗号而没有被选中。generation目标无法证明最终全部electricity demand守恒，更不能作为Research最终用户A*。

因此当前既有风险包括重复、遗漏和重标定失真；不应只选其中一种并计算一个没有证据的“修正量”。原0.97仍NOT SCIENTIFICALLY ACCEPTED，不修。

## 拟议会计契约（推导，未实现）

在共同国家、年、计量点、节点和时刻上，令`h_B^X`为已获准转移的Buildings历史电热，`h_T^X`为已获准显式表示的交通历史用电；二者集合互斥。则：

`D_retained = A* − h_B^X − h_T^X`

`D_retained + h_B^X + h_T^X = A*`。

只转移明确识别且确实已包含的历史输入，恰好一次。未知历史电量不设零、不从残差构造、不扣负数后clip。若铁路保持embedded，`h_rail^X`不转移；若另列固定rail Load，则必须从对应父账户转移一次，不能父账户全保留再加铁路。

未来明确的mobility/service obligation由转换组件形成EV网侧充电或H₂供给用电；该未来用电不能同时预装进D_retained。若首基准仍固定某部分交通能耗，须注明这部分未表示技术替代，且不得再增加同一义务的转换需求。AEO final-electricity轨迹仍仅benchmark，其交通/制氢重叠未核前不作为固定总Load。

上述恒等式是基年转移验收，不表示未来总电量必须等于历史A*。未来direct与service增长须分别有可追踪定义。

## 三种主要重复路径

| 路径 | 证据/判断 | 所需最小闭合 |
|---|---|---|
| 父电力保留EV/rail，同时新增充电或铁路电Load | 构造函数无对应扣除；实际父账户包含量未闭合 | 按国家建立父子包含、基年历史电量和明确转移身份 |
| Land含非电rail，同时独立rail oil | land与rail均开启、custom=false且非电rail>0时成立的源码推断；教程land=false不触发，作者final删rail油 | 明确rail属于哪个账户一次；不要求细分每条线路 |
| A*未来电量已含同一H₂/FT生产，再添内生生产Link | 条件性风险，不能据固定H₂ Load单独断言重复 | 确定固定电力是否已预含转换；终端燃料义务和供给平衡分开 |

固定H₂需求+内生制氢是正常供需平衡。只有再重复同一终端需求或预装其转换电力才构成重复。EV电池端Load、charger网侧输入和有用交通服务也不能混为同一个计量端。

本轮产出契约和风险登记，不实施EV subtraction patch；具体量、profile与最终表示均待人审。
