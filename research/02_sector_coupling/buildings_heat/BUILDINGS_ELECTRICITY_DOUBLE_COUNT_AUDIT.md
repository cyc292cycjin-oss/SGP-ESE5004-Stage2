# Buildings electricity and heat accounting

固定版本/四层见 [README](README.md)。**当前未通过 Buildings 端到端守恒验收。已证实有需求覆盖与丢失；某些重复风险是条件性推断，不能报告成已定量测得的重复电量。**

## A–J demand accounting map

下表 F/U 为裁剪前构网逻辑；最终 T/P/U-only-electric 的处理另列在表后。“base已含？”指端用覆盖，不能把原始 aggregate base 与后来被覆盖后的 AC Load 当同一份账。

| Demand / Carrier | Source | 外生/内生 | Base 已含？ | 单独添加/替换？ | 潜在重复或失守 | 当前状态 |
|---|---|---|---|---|---|---|
| A Base electricity | U DemandCast；P GEGIS/SSP；UN人口/人均电力及final total调校 | 外生 | 本身为总负荷入口 | residential 覆盖，final 再缩放 | 各阶段语义变化，无一致 residual 定义 | ENGINEERING_ISSUE |
| B R nonthermal electricity | 实际为 UNSD household Electricity +coal+非热转电；未分端用 | 外生 | household原始电力是total的一部分 | **替换 AC**，非另加“住宅”一份 | 不能标nonthermal；已有电热/制冷未剥离；但不是A+B简单相加 | SCIENTIFIC_DECISION_REQUIRED |
| C S nonthermal electricity | 实际为 UNSD services Electricity +coal，未来缩放 | 外生 | services原始电力通常是total的一部分 | 新增 services electricity Load | 初期AC已变住宅，不能直接叫双计；final aggregate重标定后若保留C则重叠风险 | ENGINEERING_ISSUE |
| D Space heat service | heat commodity + DEFAULT居民燃料拆分；BDEW×HDD | 外生候选 | fossil部分原不在base电力；已有电热部分未知 | 独立 heat Loads | 暖区shape零导致丢失；随后R函数改写S/DH；服务量不能守恒 | ENGINEERING_ISSUE |
| E Water heat service | 同D；water shape常数1 | 外生候选 | 已有电热包含关系未识别 | 独立heat Loads | useful/final energy口径、原电热扣减未清 | ASEAN_VALIDATION_PENDING |
| F Cooling | aggregate electricity隐含项 | 外生、未分解 | 推断包含部分/多数影响，未量化 | **没有独立cooling Load** | 无“base+explicit cooling”已实证重复；未来拆分需扣减 | SCIENTIFIC_DECISION_REQUIRED |
| G HP electricity | Link bus0调度，heat/COP | 内生 | 应不提前另加新转换电量 | 电力Bus平衡中按Link消耗 | 与未剥离existing电热可能重叠，数额未知 | ACCEPT_STRUCTURE；计量待审 |
| H Resistive electricity | Link bus0调度，heat/efficiency | 内生 | 同G | 同G | 同G | ACCEPT_STRUCTURE；计量待审 |
| I Existing electric heating | 总电力中未识别；欧洲资产表也不能提供ASEAN电热量 | 原消费外生；替换后的供给应内生 | 很可能有，但未取得分量证据 | prepare_heat_data算electric_heat_supply却不返回、不扣减 | 不能以名为electricity heat的推算列冒充实测existing电热 | ASEAN_VALIDATION_PENDING |
| J Fuel→electricity | coal 1:1；住宅非热油等z_f；热转电Q_e | 外生份额；Q_e后续供给可内生 | 原化石消费不在原始electricity；future aggregate边界未知 | 煤/非热项进direct；热项进heat target | 与final总量是否已含新电气化须对账；不能把全部J机械加在A上 | SCIENTIFIC_DECISION_REQUIRED |

## 构网次序关闭了什么误解

[prepare_sector_network main](source_snapshot/upstream/scripts/prepare_sector_network.py) L3955–4065：`add_heat → … → add_residential → add_services → distribution grid → temporal aggregation`。

1. `add_residential` 末尾 **将 AC Load 的量替换为 residential electricity**。所以“原始全系统base仍原样保留，再加R再加S”的说法不符合代码。
2. `add_services` 再加服务电力 Load。此刻能否解释为完整国别直接电力，需要其他分量与输入年份一致，不能仅因两列加起来就通过。
3. `prepare_heat_data` 中 electric heat deduction 整块注释；计算出的 electric_heat_supply 也没导出，未形成可复核的 baseline→residual bridge。
4. final adjustment 在 U/T/P `only_elec_network=true` 下剔除 heat；拼写不一致又剔除 `services electricity`。`include_electricity_growth` 始终执行，选定 AC 等负荷按国家总需求再调校。
5. 若未来仅把 only_elec=false，服务负荷恢复保留，但它不在 final `elec_carrier` 调校集合中。根据源码可推导总账风险，**尚未运行这种配置，不能称为实测 full-SC duplicate MWh**。

配电模块还会将 AC 与 services 电负荷、HP/电阻输入移到 low-voltage Bus，并在配置给出 distribution efficiency_static 时先按该效率缩减 AC 负荷。这个网损口径应单独记入桥接表；它不是existing electric heat/cooling的扣减。[distribution函数](source_snapshot/upstream/scripts/prepare_sector_network.py) L3413–3490。

## 原函数隔离验证：跨部门热量覆盖

使用固定 U `add_residential` 和真实 PyPSA 对象，只有2个小时、一个合成节点，无 solver。以下数值全是辨识错误的**合成夹具**，不是 ASEAN 参数：

| 热负荷 | 调用前合成 TWh | 调用后 TWh |
|---|---:|---:|
| residential rural | 6 | 0.5 |
| services rural | 4 | 1.0 |
| urban central | 2 | 0.5 |
| 全部 heat | 12 | 2.0 |

给定居民总热6、固定剩余热燃料4，则 rem_heat=2。函数先调整居民热，再以 `.filter(regex='heat').filter(like=country)` 选出**全部**该国热负荷，用 rem_heat=2 重新归一化。服务供热从4变1，集中热从2变.5。独立 annual services target 与 DH损耗随之不守恒。测试也确认 AC 从合成20变住宅7，再新增services3：这是覆盖，不是保留20再叠加7和3。

原始输入核算、此隔离案例和教程shape守恒检查见 [ACCOUNTING_VALIDATION.json](evidence/ACCOUNTING_VALIDATION.json)。它证明函数行为，不测量未运行U full-SC案例的误差大小。

## 已完成教程文件：另一条独立证据

2030 heat CSV 144小时×192列（48nodes×4uses），11808个NaN单元，即82整列缺失：41个节点×R/S space。正年度居民space需求的41节点全部受影响；service正space需求的2个泰国节点也受影响。`add_heat.fillna(0)` 将缺失变零。

这不是“ASEAN应无供暖”的科学判断，是配置给出正服务量而shape未能承载它。U 全年能否避免部分零shape尚未实测；无论全年或短样本，零分母不得静默变零。

## 未来验收式（本轮只定义，不实施）

对每国、年、快照，以统一 snapshot weighting 计算：

```
Accepted direct electricity
 = Residual base electricity + separately represented direct electricity

Total electricity withdrawals
 = Accepted direct electricity + endogenous conversion electricity

Delivered heat service_R/S
 = accepted exogenous heat service_R/S
```

换算、网损、设备损耗、DH附加量单列；先保持国家R/S年度需求，再做节点/时间守恒。HP/电阻耗电来自Link dispatch，不提前重复塞进direct electricity。原有电热/cooling只有在被新服务模型替代时，按同源证据从直接负荷剥离一次。既有6天教程不作为全年能量校准样本。

必须通过的下一步小验证：R/S分别守恒、DH分区加总守恒、零shape有明确失败状态、existing electric heat只扣一次、final调校不恢复已扣除项、服务carrier被正确处理。均未在本轮修复，也未启动正式Integrated/Disconnected。
