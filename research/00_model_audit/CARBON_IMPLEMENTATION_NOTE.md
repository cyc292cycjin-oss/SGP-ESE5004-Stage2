# 碳假设实现审计（A4）

审计对象ce327bfa。这里只核实实现并列出未来可比性选项，不改变政策、排放系数或预算。

## 当前到底是什么机制

**直接读取：当前ASEAN baseline及已跑教程没有启用CO₂净排放总量上限，也没有启用Co2L/Ep wildcard。** `co2.budget.enable=false`、opts为空、emission_price=0；三个postnetwork的global_constraints仅有 `lv_limit`（输电体积约束），无CO2Limit。存在排碳记账组件和封存约束，不能由“无CO2Limit”推导“完全没有碳相关结构”。

**论文原文已核实**：本地IOP论文 DOI `10.1088/1755-1315/1654/1/012020`，PDF第5页（印刷第4页）§3.1–3.3：案例研究覆盖电力，其他部门仅体现为电力需求；baseline无显式排放约束；decarbonised施加ASEAN电力部门绝对上限，从2025年1000 Mt降到2050年100 Mt。它不是排放强度上限。精确作者代码SHA和各年实际配置尚未核实，不能认定ce327bfa复现该路径。

论文来源：[本地论文](C:/Users/20122/Desktop/ASEAN政策文件/Andreyana_2026_IOP_Conf._Ser.__Earth_Environ._Sci._1654_012020.pdf)，证据文本/哈希见 `PAPER_EVIDENCE.json`。本文仅摘要与当前审计相关的方法，未复现论文数值。

## 代码路径

| 路径 | 条件/实现 | 含义 |
|---|---|---|
| prepare_network.py Co2L | opts包含Co2L；可用co2.limit、带数值的co2.base倍数、或历史排放数据automatic_emission | 添加GlobalConstraint CO2Limit，carrier_attribute=co2_emissions，sense≤，constant=annual_emissions×Nyears |
| prepare_sector_network.py:add_co2_budget（约3601行） | co2.budget.enable时；year取factor；base_value为limit/base/absolute或float；存在CO2Limit按override_co2opt选择覆盖 | 分规划年份的年度绝对量路径，myopic逐期约束；不是跨2025–2050累计碳预算，也不是单位产出强度 |
| prepare_sector_network.py:add_co2（约1408行） | 建co2 atmosphere Bus/Store，Carrier.co2_emissions=-1；排放/捕碳经多端Link流入/流出 | 非循环Store的碳存量变化参与排放记账；不能只求各发电机carrier排放和而忽略多端Link/Store |
| convert_conventional_generators_to_links（约3740行） | 化石发电转fuel→electricity + atmosphere Link，相关燃料carrier排放设0避免重复计数 | 排放系数/效率输入口径要随变换核对；不能将fuel Generator与Link排放重复统计 |
| solve_network.py:add_co2_sequestration_limit（939行） | extra_functionality中调用，存在co2 stored Store才添加；最后快照stored CO₂之和≤sector.co2_sequestration_potential×1e6 | 当前配置继承200 Mt、注释欧洲。Linopy模型约束不必出现在network.global_constraints表；不是大气净排放预算 |
| prepare_network.py:add_emission_prices | Ep wildcard向Generator/SU加排放成本 | 当前未启用；对后续多端Link碳计价的完整覆盖不能仅凭此函数认定 |

`Nyears=Σw_objective/8760`用于CO2Limit；三个教程结果objective/generators/stores权重均合计8760，故当前教程Nyears=1（只表示归一化）。封存上限函数未按Nyears缩放，改变时间权重需单独审核。纸面“CO₂-eq”用词不证明模型包含CH₄/N₂O或生命周期全温室气体，当前代码主要使用co2_emissions/CO2 intensity及过程排放。

## 已发现的配置键冲突：不能直接启用预算

- `configs/config.asean.yaml`写 `co2.budget.co2base_value: 1.0e+09`。
- `config.default.yaml`写 `co2.budget.base_value: limit`、`co2.limit: 7.75e7`（注释欧洲默认）。
- add_co2_budget读取 `budget['base_value']`。`_helpers.py:_migrate_co2_budget_base_value`只迁移旧的顶层 `co2_budget.co2base_value`，不迁移现在这个嵌套混合键。
- **实际教程meta同时保存**co2base_value=1e9和base_value=limit；预算关闭，故没有激活错误上限。
- **静态推导，未运行验证**：在当前合并配置仅切enable=true而没有其他覆盖，将读77.5 Mt基数，按ASEAN factors成为2025年77.5、2030年63.55、2035年49.6、2040年35.65、2045年21.7、2050年7.75 Mt；不是论文1000→100 Mt。

这一不一致需要单独修复/确认任务，不能在本轮默默将base_value改成1e9。`scenario.demand=DEC`是需求情景标签，也不等于净排放预算已开启。

## 11国standalone怎样保持可比：只列选项

首先确认导师“当前模型”指当前baseline还是论文/仓库decarbonised。二者都真实存在，但碳假设不同。若选择完整SC，还须确认预算覆盖哪些部门；把论文的电力预算无解释地施加到所有部门不是自动“保持相同”。本轮不替用户选择。

| 选项（未实施） | 数学/实现想法 | 可比性与风险 |
|---|---|---|
| A 保持当前baseline | integrated与各国均不启用CO2Limit/Ep；保留同排放因子/记账与已确认封存边界 | 忠于现有baseline，不得称“各国同等减排目标”；区域200Mt封存等有限资源不能每国各200Mt |
| B 同基年减排比例 | 采用同口径经确认基年E_i,0，B_i,t=α_t E_i,0；整体B_t=α_tΣE_i,0 | 同相对削减幅度、国家预算加总闭合；区域整体允许跨国调配预算，而单国固定份额不允许，收益会混有碳额度协调价值 |
| C 冻结区域预算份额 | B_i,t=w_i B_t，Σw_i=1；份额须事先共同确认（例如同口径基年排放份额） | 不复制区域绝对量；不能任意用人口/GDP/电量代替已选口径；需要明确分配含义，避免新增国家政策问题 |
| D 使用整体基准的排放分配作诊断 | 将已验收integrated结果E_i,t作为standalone限额候选，统一统计净排放/捕碳 | 外生限额依赖整体结果、可能为零/负值且单国不可行；不是独立政策基准，不能宣称同等减排努力 |
| E 无跨境能量连接但共享区域碳约束 | 一个模型内断开能量网络，各国只通过ΣE_i≤B_t耦合 | 更接近单独识别电力网络效应，但已不是11个完全独立求解；不能把各自无协调求解结果简单相加替代 |

**分析推导边界**：若所有国家预算可行、ΣB_i=B且其它资源/成本约束一致，固定国家预算的可行集通常是区域共享预算可行集的子集。这里的“通常”依赖相同服务需求、边界及可分解约束；不能对含不同共享资源、负排放池、不同聚类的模型直接使用。需要区分网络收益与排放分配约束收益。

不采用：每国复制1e9或区域总B；未经确认按人口平分；把碳预算换成统一碳价/强度政策；将净排放与毛排放或CO₂和CO₂-eq混用。未设计新政策情景。

## 后续验收要求（未执行）

逐年保存有效co2配置及其来源层级、CO2Limit最终constant与所有额外求解约束、快照权重、碳carrier和多端Link映射；核对国家预算/区域资源加总；用一致的净排放方程验证结果残差。原始排放因子/基年源、论文SHA、full-SC统计边界未共同确认前，不进入正式实验。
