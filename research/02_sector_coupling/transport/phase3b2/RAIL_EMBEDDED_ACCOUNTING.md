# Rail embedded accounting

**表示冻结：EMBEDDED。数值包含关系：尚未通过。** 不新增铁路技术竞争、rail electrification路径或铁路专用电/油Load。

| 账户 | 必须保留在哪里 | 去重条件 |
|---|---|---|
| Rail electricity | 同年完整A*内一次 | 证明包含后不再创建独立rail电Load；不从A*另扣rail |
| Rail liquid/other fuel | generic direct-fuel父账户内一次，保留rail子标签 | 先证实父账包含，再禁用/转移独立rail油Load |
| Rail combustion | retained direct-fuel全系统报告账 | 按真实燃料身份计一次，即便无rail组件 |

新road parent是road-only，不含rail。U `build_base_energy_totals.py:203–222,246–260`原本按不同交易抽取；旧`prepare_transport_data.py:172–180`才把非电rail并入land代理。不能让rail先混入新road又保留一次direct fuel；也不能取消旧合并后把rail丢掉。

U `prepare_sector_network.py:3696–3740`分别新建rail电/油Load，不证明已经从任何父账户扣除。当前缓存有rail空值、空集零值；来源已知者也未自动获研究接受。rail总量可能含diesel、biodiesel、电，不可把非电全部无标签化作化石oil。

实际父燃料账尚不存在或不能证明包含时，**不得机械设置rail=false并宣称embedded完成**。最小组装做法是建立透明的父子清单，把源rail子项纳入direct-fuel一次；它是同一义务的合并表示，不是额外需求。旧网络转移须保存前后国家/载体/年度总量与组件ID。

碳遗漏已具结构证据：旧rail fuel构造器无燃烧回排；保留tutorial pre-strip样本oil carrier因子0，rail油Load能绕过大气账。embedded后必须由direct-fuel报告事件承担其燃烧，不能因为无独立rail Load就忽略。参见[碳合同](TRANSPORT_CARBON_ACCOUNTING_CONTRACT.md)。

本轮只冻结上述表示和验收条件，没有删实际rail组件。源/缓存定位见[evidence/ROAD_RAIL_REVIEW.md](evidence/ROAD_RAIL_REVIEW.md)。
