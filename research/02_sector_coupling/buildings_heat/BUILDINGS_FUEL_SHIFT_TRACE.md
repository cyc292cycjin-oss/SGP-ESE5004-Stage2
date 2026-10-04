# Buildings fuel shifting

F/U/T/P 版本定义见 [README](README.md)。本表描述冻结代码与默认值，**所有值仍 UNVERIFIED，未执行修订**。

## 外生处理与内生替代

| Fuel | Base preprocessing（F/U） | Future preparation（F/U） | Optimization 构网（F/U，裁剪前） |
|---|---|---|---|
| Coal | `sector.coal.shift_to_elec=true`：households/services 的 coal 类热值直接并入 electricity TWh，按1:1能量记账；false 时该部门 coal 被忽略 | 并入后的 electricity 随其默认增长/效率处理 | 没有对应的 Buildings 固定 coal Load 或该部分煤供热技术选择；不要与发电燃煤混淆 |
| Oil | 分组 oil fuels（包含 LPG、kerosene 等），记录最终燃料 TWh | 居民按热份额、热电气化份额、非热电气化份额拆分；services 没有同样拆分，按原列增长/效率缩放 | 居民 nonheat oil + remaining heat oil 作为固定 oil Load；服务 oil 固定 Load，配显式 CO2 Load |
| Gas | Natural gas (including LNG) 分组为最终燃料 | 居民 75% 热份额，DEFAULT热/非热电气化均0；services 直接缩放 | fixed residential/services gas Loads；另有 gas boiler 可供剩余 heat Load，二者并存 |
| Biomass | 多种 biomass fuels 分组 | 居民 DEFAULT热份额75%、热/非热电气化均0；services 直接缩放 | fixed residential/services biomass Loads；urban central 可有新建 biomass CHP，不能替代所有已固定的建筑 biomass consumption |
| Electricity | raw household/service Electricity + 可选coal conversion | 居民额外加入被转成电的“非热”燃料部分；没有 end-use 分解 | residential 覆盖 AC Load；services 新加 Load；两者均不是已识别的 nonthermal-only electricity |
| Heat commodity | Heat / direct geothermal / direct solar thermal | 共用0.6/0.4拆分；居民后续合并推算热，服务主要保留此少量来源 | `add_heat` 建服务负荷，然后 `add_residential` 覆盖所有 heat；见核算审计 |

源码入口：[base L137–201](source_snapshot/upstream/scripts/build_base_energy_totals.py)、[future L108–255、291–296](source_snapshot/upstream/scripts/prepare_energy_totals.py)、[residential L3247–3411 与 services L3033–3140](source_snapshot/upstream/scripts/prepare_sector_network.py)。不是同名 `oil.shift_to_elec` / `gas.shift_to_elec` config：油气生物质主要入口是 `data/demand/fuel_shares.csv`。这一区别关系到今后能否只改 config 重现实验。

## DEFAULT 数值与可追溯性

`fuel_shares.csv` 只有 DEFAULT/MA/NA/US，无 ASEAN；各国先填 DEFAULT 再计算。

| 字段 | DEFAULT | 范围 |
|---|---:|---|
| oil residential heat share | 0.6667 | 居民油消费中假定热用途 |
| biomass / gas residential heat share | 0.75 / 0.75 | 居民燃料中假定热用途 |
| oil / biomass / gas to elec heat share | 0.5 / 0 / 0 | 热用途外生转电份额 |
| oil / biomass / gas to elec share | 0.5 / 0 / 0 | 非热用途外生转电份额 |
| space to water heat share | 0.6 | 居民拆出的热量中 space 份额 |
| sector.efficiency_heat_oil_to_elec 等三项 | 0.9 | 仅部分转电热量乘此因子，不是优化器求得的 COP |

[fuel blame](history/fuel_blame.txt) 将列/结构追溯到 2023-08 的 Earth-Sec demand workflow，将当前 DEFAULT 行定位到 `f3e260cf5b91295ec8261077a817d5425f6d2636`（2025-04-18）。DEFAULT 与 MA 当前行相同；不能据此断言这些数有经验证的 Morocco 或 Europe 来源。**分类 DEFAULT_WITHOUT_ASEAN_EVIDENCE**，未恢复原统计依据。

## 数学口径（解析推导）

令住宅燃料 f 的 base final energy 为 F_f，热份额 h_f，热转电份额 e_f，非热转电份额 z_f，转换因子 η_f，增长与效率乘数合记 m。冻结脚本的关键量为：

```
候选转电热量 Q_e = base heat commodity + Σ F_f h_f e_f η_f
剩余固定热燃料 H_f = F_f h_f (1-e_f) m_heat,f
剩余固定非热燃料 N_f = F_f (1-h_f) (1-z_f) m_nonheat,f
residential heat total = Q_e + Σ H_f
residential direct electricity = grown original electricity + Σ F_f (1-h_f) z_f
```

Q_e 的新增燃料项及新增非热电力项没有像 H_f 一样完整乘上未来增长/效率；“electricity residential space/water”是 Q_e 的拆分列，随后用作 heat service，并不代表优化前已确定的 HP 耗电。不同字段的命名、单位和转换口径不能混用。

**混合口径**：H_f 仍是 fuel-input energy；Q_e 的燃料部分已经乘0.9，再与它相加成 total heat。没有统一把所有燃料换成 useful heat 的链条。cooking 等燃料用途并未由原始 end-use 分类单独识别，热份额默认值可能把非 space/water 的用途误分，需验证，不能断言所有燃料都是采暖。

`add_residential` 将 H_f 加回固定 fuel Loads，并把 nominal heat target 缩为 Q_e；最后又用 Q_e 覆盖该国所有 heat Loads，包括 services/central。因此：

- **并非所有燃料→电力转换都已经作为额外电负荷加了一遍。** 热转电的 Q_e 进入剩余 heat target，之后 HP/boiler 等再决定供给；简单断言“同一笔Q_e必然算两遍电”不成立。
- 但热需求边界部分由外生燃料份额决定，剩余 H_f 不能被 HP 替代，不满足 BH-1。
- 当 base electricity 含 existing electric heating 时，原本计划扣减的代码被注释；现有电热量没有独立源识别，是否与剩余热服务重叠及重叠量未关闭。
- 未分组的商品类别、缺失记录与显式 false 时被忽略的煤，都应分别标记；不能把 fillna(0) 理解为证实零需求。

## 四层与状态

F 支持固定 fuel Loads 与可替代 heat Links 并存；U 开启两条路径且末端裁剪热；T 使用相同0.6/默认链且存在现成中间量；P metadata 记录同类开关，但 paper power case 未验证完整建筑热逻辑。

科学接受：SCIENTIFIC_DECISION_REQUIRED（统一 useful-heat / 非热边界）、REJECT_DEFAULT（无地区依据的份额直接采用）、ENGINEERING_ISSUE（跨部门覆盖、扣减与守恒）。本轮不改任何比例或 fuel-carrier 配置。
