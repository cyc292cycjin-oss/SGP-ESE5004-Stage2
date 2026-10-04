# Transport与共同H₂/燃料系统

**终端燃料需求多为外生，供给路径可内生。两者不能统称“内生交通脱碳”。** 对同一燃料Load配置生产Link属于正常供需平衡，不是重复计算。

| 路径 | 终端/转换角色 | 当前U与最终案例限制 |
|---|---|---|
| AC→H₂ Electrolysis | 可扩张生产，内生电力输入 | U默认production list包含；作者final也有该Link，但不证明供给交通 |
| gas→SMR/SMR CC→H₂ | 可扩张供给及共同CO₂账 | fossil-H₂上游排放不能因终端H₂无CO₂而消失 |
| H₂→Road FCEV Load | 外生share×能源代理/0.5 | DEC份额0；无燃料电池车辆投资竞争 |
| H₂→Shipping Load | 外生share与效率转换 | DEC份额0；可选液化不是默认开启 |
| H₂+CO₂+AC→FT oil | 可扩张合成供给，oil/CO₂/AC多端Link | oil可供航空/航运/其他用途；最终交通油Load被裁剪，FT保留不证明synthetic aviation存在 |
| H₂+AC→NH₃，NH₃→H₂ | 工业氨/裂解与共同H₂池 | 不是直接船用NH₃需求，不能据此新增氨船 |
| H₂→Sabatier gas；AC→helmeth gas | 共用合成气供给 | 不等于已表示天然气船/飞机 |
| Methanol / transport biofuel choice | 未发现直接构造 | 标ABSENT/DEFERRED；不由generic biomass存在推导SAF |

定位：`U/scripts/prepare_sector_network.py:344–380,420–425,506–524,651–684,1631–1680,1733–1785,2146–2235,2504–2518`；开关`config.default.yaml:787–790,979–1006`。

FT使用H₂输入、oil输出、负的CO₂-stored端和AC端，具有额外电输入；电解的用电仍在自身Link产生。液化Link采用H₂输入输出效率，缺少独立AC端，不能把其效率损耗直接报告为已明确建模的电制冷用电。各成本来自当前prepared cost table；来源版本沿既有v0.13.2/成本链登记，未因本审计更新DEA。

## 必须避免的三类混淆

1. 终端固定H₂需求与满足它的制氢是同一供需链；只有又把该制氢电力预装入固定A*，或再加同一H₂义务，才重复。
2. FT油与化石油在同一oil Bus可以由成本/碳约束决定供给，但这不是内生改变航空/航运终端技术份额，更不自动保证油品规格/掺混合规。
3. 全国direct fuel若仍包含运输油，新增shipping/aviation/ICE Load必须有一次性互斥转移，不能把两个账都完整保留。

未来Disconnected必须单独定义电网、H₂网络、燃料贸易/资源池的边界。无H₂管道不代表能源完全自给；共享commodity供给、外部燃料供应和碳存储不应因“国家独立”概念被擅自删除。本轮只列边界决定，不改H₂网络或实验配置。
