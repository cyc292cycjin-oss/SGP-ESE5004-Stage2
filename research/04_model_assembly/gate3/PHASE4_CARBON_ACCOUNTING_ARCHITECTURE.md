# PolicyCO2_Power 与 ReportingCO2_FullSystem

两个视图读取同一物理碳事件，不相加。前者保留原 Power 政策范围，后者记录全部实际纳入的模型内 CO2；本轮没有新 FullSystem cap，也没有补生命周期或其他温室气体。

| 事件 | Policy | FullSystem |
|---|---:|---:|
| +1 t Power（不论电力最终供哪一部门） | +1 | +1 |
| +1 t Buildings/Road/Industry/Agriculture 直接燃烧 | 0 | +1 |
| +1 t 国内 shipping/aviation 或国际 bunker | 0 | +1，并保留各自账户 |
| 物理 capture transfer / FT transfer / geological storage | 无额外排放或第二份负信用 | 内部转移0；另记库存 |

事件必须有唯一 EventID、CarbonBatchID+Stage、country、sector、origin、已接受的归属。重复父/子分摊、重复事件/阶段、未接受系数、缺失国家与内部储存负信用均报错。共享 SMR/CHP 可使用合计为1的人类接受份额，程序不选择实际份额，也不再次分摊已分配事件。

合成守恒证明：1 t 化石碳捕集0.6且永久储存0.6 → 大气0.4；若0.6经 FT 后在交通回排 → 总大气1，Power仅原0.4；DAC吸收1并再释放1 → 净0，不能再把封存或FT标为额外信用。BIOGENIC 不虚构生命周期吸收。被捕集不等于永久减排，临时库存与永久库分别记账。

该 lineage helper 需要输入碳已沿来源追踪，不是解后自动识别算法。真实混合 fossil/FT oil、shared H2/CHP、DAC/vent 的用途与信用尚未接受，不能声称完整数值账已就绪。`MIXED_UNRESOLVED` 不允许负信用抵 Power cap。合成接受标记仅用于测试，未写入数据台账。

首版未来 Integrated/Disconnected 仍共享同一 ASEAN Power 政策约束，Disconnected 不自动等于11个彼此独立求解的问题；不能机械复制区域预算给每国。仅跨国 AC/DC 电力边是未来干预，当前未实施。
