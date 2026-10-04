# Gate3 完成，停在 Gate4 之前

已实现并验证国家/节点载体接口、有限资源守卫、单向外部供给、物理碳库存、Power 政策表达式与全系统事件账。审计和实现交付完成；尚不满足真实 Full-SC 网络组装的输入与归属验收条件。

```text
GATE3_RESUMED_FROM_VERIFIED_GATE2_HEAD = YES
CARRIER_ISOLATION_IMPLEMENTED = PARTIAL
HIDDEN_CROSSBORDER_CARRIER_SHARING = PARTIAL
CROSS_BORDER_H2 = OFF
CROSS_BORDER_GAS_NETWORK = OFF
CROSS_BORDER_CO2_NETWORK = OFF
POWER_POLICY_CO2_SCOPE_ISOLATED = PARTIAL
FULL_SYSTEM_CO2_REPORTING_READY = PARTIAL
GATE2_DEMAND_GUARDS_PRESERVED = YES
BUILDINGS_REGRESSION = PASS
SHIPPING_REGRESSION = PASS
CARRIER_REACHABILITY_TESTS = PASS
CARBON_SCOPE_TESTS = PASS
SCIENTIFIC_ASSUMPTIONS_SILENTLY_CHANGED = NO
RESEARCH_BRANCH_CLEAN = YES
REMOTE_MAIN_UNCHANGED = YES
READY_FOR_PHASE4_GATE4_FULLSC_NETWORK_ASSEMBLY = NO
```

`PARTIAL` 的统一含义：接受数值上的结构接口与合成测试通过，但真实 Research 网络未组装，历史网络共享池未被原地修改，真实共同用途/碳来源未全部归属。不能把“新模板无非法路径”扩大为“完整模型全部消除”；不能把 reporting 函数可用扩大为真实全系统碳账完整。clean/main 状态以包根 CLOSEOUT.json 的最终本地/远程核验为准。

## 必须处理的系统级前提
- **G3-01** — Real Gate2 demand and node/time allocation remain PENDING。Accept annual/future parent and sector obligations, missing industrial fuel/process entries, bunker ownership and spatial/temporal allocation; never substitute zero。
- **G3-02** — Real external supply and finite-resource assumptions not accepted。Accept fuel price/year/currency/heat basis and availability; biomass/biogas country allocations conserving regional total; local geological capacity and cost; do not copy 360 TWh or Europe 200 Mt to each country。
- **G3-03** — Mixed SMR/CHP and capture/recycled-carbon attribution incomplete。Accept power-use attribution, carbon origins and stock/flow tracing through mixed CO2/oil pools; demonstrate power-only reference equivalence including H2/SMR and geothermal。
- **G3-04** — Pinned raw transformer endpoint 765/766 unresolved; final clustered control edges unavailable。Resolve known topology issue in its authorised later gate and freeze actual assembled bus-country/control-edge mapping; do not use raw 62 or tutorial 30 as final intervention set。

765/766 与最终控制边是被本轮明确推迟的后续工程，不在 Gate3 偷修；其余缺口是既有接受/归属要求，不另开研究阶段。未经这些门禁通过，不执行正式实验。

## 审计问题回答

| 事项 | 已验证结论及限制 |
|---|---|
| 当前共池有哪些 | stored CO2、Earth solid biomass、Earth lignite；工业 process/biomass 汇总池归属缺失；H2 export 为单向 sink，不是返送网络 |
| 哪些构成物理共享 | CO2 有方向转换路径；biomass/lignite 有共同资源/供给访问，两类明确区分 |
| 新 H2 与外部供给 | 本国本节点 H2；每国单向供给，共价格不共库存，禁止新 H2/NH3/MeOH 进口 |
| 生物质与地质库存 | 接受分配后守恒，不能复制区域总量；地质不允许回取；真实分配 pending |
| FT 与 captured CO2 | 全端口国别一致；原料池与永久库不同；来源追踪仍 pending |
| 合法全局对象 | 大气环境/报告账、价格元数据、原区域 Power 政策；不是跨国燃料 Bus |
| 电力边 | 历史65=30跨国+35国内；当前raw4109=62跨国+4046国内+1未知；不能代替最终控制集 |
| 六年预算与 baseline | 1000/820/640/460/280/100 Mt，/8760 缩放保持；baseline enable=false |
| Policy 与 FullSystem | 静态 +1 及表达式系数已隔离，SMR/CHP与origin完整实数映射未闭合 |
| Bunkers | 国内/国际海运/航空四账户分别测试，不消耗Power cap |
| 捕集、回用、封存 | 合成一次核算守恒；真实油/CO2混池来源未假设中和 |
| Gate2 | A*、exactly-once、missing!=0、embedded/explicit、未来值门禁不变；44 country-year数值构造仍 blocked |
| 正式工作 | 未求解、未修拓扑、未切换I/D、未加新技术、未改变已接受科学假设 |

## 证据等级

**直接读取**：当前源码/配置、Gate2输入、历史NetCDF组件快照、原始拓扑、Git引用、测试输出与哈希。

**分析推导**：由真实端口符号与 country 映射构造的方向依赖图、共享资源访问分类、旧 aggregate cap 对全系统 scope 的影响。可达性是潜在上界，不证明调度流。

**合成验证**：+1 t、100单位资源、源价、测试容量与FT系数，仅用于程序性质检查，不是 ASEAN 输入。

**待接受/后续验证**：真实数据、共享用途份额、资源分配、来源追踪、最终组装后的完整图与碳表达式等价。审计表任何 True/分类均不构成人工数值确认。
