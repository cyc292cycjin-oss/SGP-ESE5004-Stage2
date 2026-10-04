"""Assemble review tables/documents from preserved evidence, never solve."""
from pathlib import Path
import json,hashlib,shutil,collections,re,sys
W=Path(__file__).resolve().parent;E=W/'evidence';D=W/'reports';B=W/'build';B.mkdir(exist_ok=True)
G=W/'stage/research/04_model_assembly/gate3';G.mkdir(parents=True,exist_ok=True)
def load(name):return json.loads((E/name).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def doc(name,text): (G/name).write_text(text.strip()+'\n',encoding='utf-8')
start=load('START.json');graph=load('REFERENCE_GRAPH_AUDIT.json');raw=load('RAW_ELECTRICITY_CLASSIFICATION.json')
test=load('GATE3_TEST_RESULTS.json');config=load('RESEARCH_GATE3_CONFIG_CHECK.json');commits=load('IMPLEMENTATION_COMMITS.json')
assert test['pass'] and all(load('GATE2_HASH_GUARD.json').values())
buildings=load('BUILDINGS_REGRESSION.json');shipping=load('SHIPPING_REGRESSION.json')
assert buildings['all_pass'] and len(buildings['rows'])==1062 and len(shipping['tests'])==17 and all(r['status']=='PASS' for r in shipping['tests'])
HEAD=commits[-1]['sha'];base=start['head'];ref=load('TUTORIAL_COMPONENTS.json')
statuses={'GATE3_RESUMED_FROM_VERIFIED_GATE2_HEAD':'YES','CARRIER_ISOLATION_IMPLEMENTED':'PARTIAL','HIDDEN_CROSSBORDER_CARRIER_SHARING':'PARTIAL','CROSS_BORDER_H2':'OFF','CROSS_BORDER_GAS_NETWORK':'OFF','CROSS_BORDER_CO2_NETWORK':'OFF','POWER_POLICY_CO2_SCOPE_ISOLATED':'PARTIAL','FULL_SYSTEM_CO2_REPORTING_READY':'PARTIAL','GATE2_DEMAND_GUARDS_PRESERVED':'YES','BUILDINGS_REGRESSION':'PASS','SHIPPING_REGRESSION':'PASS','CARRIER_REACHABILITY_TESTS':'PASS','CARBON_SCOPE_TESTS':'PASS','SCIENTIFIC_ASSUMPTIONS_SILENTLY_CHANGED':'NO','RESEARCH_BRANCH_CLEAN':'YES','REMOTE_MAIN_UNCHANGED':'YES','READY_FOR_PHASE4_GATE4_FULLSC_NETWORK_ASSEMBLY':'NO'}
blockers=[
dict(ID='G3-01',Scope='SYSTEM_INPUT_ACCEPTANCE',Issue='Real Gate2 demand and node/time allocation remain PENDING',Required='Accept annual/future parent and sector obligations, missing industrial fuel/process entries, bunker ownership and spatial/temporal allocation; never substitute zero',Evidence='Gate2 pinned demand ledger; RESEARCH_GATE3_CONFIG_CHECK.json',Status='OPEN',ActionOwner='Human acceptance + subsequent assembly input gate'),
dict(ID='G3-02',Scope='SYSTEM_SUPPLY_RESOURCE_BOUNDARY',Issue='Real external supply and finite-resource assumptions not accepted',Required='Accept fuel price/year/currency/heat basis and availability; biomass/biogas country allocations conserving regional total; local geological capacity and cost; do not copy 360 TWh or Europe 200 Mt to each country',Evidence='Phase3 EXTERNAL_COMMODITY_SUPPLY_BOUNDARY; EFFECTIVE_CONFIG.json',Status='OPEN',ActionOwner='Human source/allocation acceptance'),
dict(ID='G3-03',Scope='SYSTEM_CARBON_ATTRIBUTION',Issue='Mixed SMR/CHP and capture/recycled-carbon attribution incomplete',Required='Accept power-use attribution, carbon origins and stock/flow tracing through mixed CO2/oil pools; demonstrate power-only reference equivalence including H2/SMR and geothermal',Evidence='Phase3 CARBON_SCOPE_FREEZE; REFERENCE_POLICY_MAP.json',Status='OPEN',ActionOwner='Human attribution acceptance + implementation validation'),
dict(ID='G3-04',Scope='SYSTEM_TOPOLOGY_ASSEMBLY_PREREQUISITE',Issue='Pinned raw transformer endpoint 765/766 unresolved; final clustered control edges unavailable',Required='Resolve known topology issue in its authorised later gate and freeze actual assembled bus-country/control-edge mapping; do not use raw 62 or tutorial 30 as final intervention set',Evidence='RAW_ELECTRICITY_CLASSIFICATION.json: transf_524_0',Status='OPEN_DEFERRED_BY_GATE3_SCOPE',ActionOwner='Later authorised topology/assembly work')]
tables={}
def add(name,rows):
 headers=list(rows[0]);values=[headers]+[[r.get(k) if r.get(k) is not None else '' for k in headers] for r in rows]
 tables[name]={'export_values':values}
add('PHASE4_CARRIER_REACHABILITY_AUDIT.csv',graph['audit'])
add('PHASE4_HIDDEN_CROSSBORDER_PATHS.csv',graph['hidden'])
add('PHASE4_ELECTRICITY_LINK_CLASSIFICATION.csv',graph['electricity']+raw['rows'])
pol=load('REFERENCE_POLICY_MAP.json')
for r in pol:
 r['FactorUnit']='tCO2/MWh_Link_input' if r['Component'].startswith('Link:') else 'tCO2/MWh_Generator_output' if r['Component'].startswith('Generator:') else 'fixed_Load_trace_not_unit_factor'
 r['NumericAccepted']=False
add('PHASE4_CO2_POLICY_COMPONENT_MAP.csv',pol)
carrier=[];carbon=[]
for r in test['records']:
 name=r['Test_ID'];iscarbon='.CarbonTests.' in name or any(x in name for x in ['atmosphere','industrial_coal','fuel_factor','linopy_constraint','pending_scope','legacy_cap'])
 (carbon if iscarbon else carrier).append(dict(Test_ID=name,Status=r['Status'],Evidence=r['Evidence'],Source='tests/research/test_carrier_carbon.py',Coverage='accepted/synthetic fragment only; full model NOT assembled'))
add('PHASE4_CARRIER_REACHABILITY_TESTS.csv',carrier);add('PHASE4_CARBON_SCOPE_TESTS.csv',carbon);add('PHASE4_GATE3_BLOCKERS.csv',blockers)
(B/'tables.json').write_text(json.dumps(tables,ensure_ascii=False),encoding='utf-8')
(E/'DELIVERY_COUNTS.json').write_text(json.dumps({k:len(v['export_values'])-1 for k,v in tables.items()},indent=2))
(E/'FINAL_STATUS.json').write_text(json.dumps(statuses,indent=2))
doc('PHASE4_GATE3_START_IDENTITY.md',f'''# Gate3 续接身份

核验基点：`{base}`；分支 `research/full-sc-baseline`，续接时 working tree clean，本地与远程一致。远程 main 为 `a3616a68ee44592af6527ca9024a90f1956646ae`。详情：`evidence/RESUME_IDENTITY.json`；30 项输入、源文件、配置与历史网络核验全部通过。

先盘点并生成精确差异，后集成六个白名单文件。`GATE3_RESUME_INVENTORY.md` 和 `GATE3_DRAFT_DIFF_REVIEW.md` 区分有效证据、待复核草稿与禁止合入内容。未丢弃历史资产、未重建有效审计证据。

测试通过后依次提交载体接口、碳架构、验证接口；另有共用价格与国家可用量解耦的窄修复。实现与测试提交：

'''+'\n'.join('- `'+c['sha']+'` — '+c['message'].splitlines()[0] for c in commits)+f'''

最后测试的实现 SHA：`{HEAD}`。交付文档提交与远程最终身份在包根 `CLOSEOUT.json` 记录，避免文档自含最终 SHA 的循环。Gate2 输入及 demand 脚本 21 项 SHA 未变，上游三个被追踪源码 SHA 未变。历史 shipping 修复仍在 Gate2 祖先中。

没有执行 solver、Full-SC 组装、765/766 修复或 Integrated/Disconnected 切换。
''')
doc('PHASE4_HYDROGEN_ARCHITECTURE.md','''# H2 国家与节点归属

已验证：当前配置 `sector.hydrogen.network=false`；上游 `add_hydrogen` 支持电解、SMR/SMR CC、燃料电池、H2 储存和配置允许的 H2 turbine。能力、配置候选、已接受数值三者分开。

`local_blueprint` 为每个明确 country/node 创建独立 H2 Bus，转换端口只能连接本国节点；本轮不新增任何管线。候选方向进入可达图，但缺少人工接受的参数时 `to_pypsa_fragment` 拒绝物化。真实 Load 必须经过 Gate2，载体构造器直接拒绝 Load。

同国不同节点也没有隐式 H2 pooling。今后若需要国内 H2 网络，须明确节点与接受的物理资产；它不是本轮默认连接。NH3、methanol 与外部 H2 导入均 deferred；不会因旧配置中 ammonia=true 自动加入首版。跨国 H2/gas/CO2/NH3/MeOH 为 OFF。

历史 tutorial 的 H2 export bus 是单向汇集出口：14 条 export Link 的 p_min_pu=0、没有返送路径，不能把名称含 global 的节点直接称为跨国 H2 传送。真实出口义务尚未接受，首版不自动激活。

证据：`source/scripts/prepare_sector_network.py:add_hydrogen`、EFFECTIVE_CONFIG、TUTORIAL_COMPONENTS 与 `REFERENCE_GRAPH_AUDIT`。新模板的可达性已测试；历史 NetCDF 未修改，完整 Research 网络尚未建立。
''')
doc('PHASE4_FUEL_SUPPLY_ARCHITECTURE.md','''# 燃料外部供给与物理隔离

上游 `add_carrier_buses:272–317` 使用带 fuel marginal_cost 的供给 Generator、Bus、可扩张 Store。它表示外生供给接口，不能证明国内气田、现实进口来源或无限世界市场。

新接口为 gas/oil/coal/lignite 各国节点建立独立、单向 source Generator。共用价格标识只包含 price、unit、source hash/year、热值口径等元数据；国家容量及年度可用量独立保留。允许同价、不同国别供给上限，禁止把本国 FT 产油返送到共同市场再进入外国。

价格输入要求 EUR/MWh_fuel 与明确 HHV/LHV 等 basis；容量、年度上限必须显式给出，若无年上限须有明确接受标记。本轮真实参数均未据此批准。有限年度供给通过已建 Linopy 变量上的 `ResearchImportAnnual-*` 约束计入，必须调用 `install_fragment_constraints`；当前没有组装/求解 workflow 入口。

燃料成本只在源 Generator 计一次；转换 Link 承担自身转换成本与燃料消耗，不再加同份燃料源价。固定或可扩张供给/储存的实际数值必须后续接受，不能为消除不可行擅自放宽。

`combustion_accounting_interface` 是最终燃料计量接口：1 MWh_fuel 输入对应 1 MWh 最终燃料义务输出，另一个端口按已接受因子报告 CO2。它不推定有用能效率、不添加新服务技术、不创建 Load；工业煤的能流和排放来自同一 Link-p，不能只有 CO2 Load 而没有煤消费。

历史 Earth lignite 为共享供给/库存访问，需隔离；不是所有路径都代表 A 国向 B 国注入。当前 gas/oil spatial=true 已分节点，仍需用所有转换端口而非配置名称核验。Integrated/Disconnected 未来使用完全相同的这些输入；本轮 overlays 未变。
''')
doc('PHASE4_BIOMASS_ARCHITECTURE.md','''# 生物质有限资源隔离

已验证：`biomass_transport=false` 仍可能生成 Earth solid biomass 共享库存；它给多国访问同一资源的能力。上游原候选 solid biomass=360 TWh、biogas=0.5 TWh，不是人工接受的 ASEAN 国家资源表，也不能逐国复制。

新接口 `allocate_finite_resource` 只接受明确来源、国家/节点分配、总量与成本。分配和必须回到唯一总量，否则报错。各节点有限 Store 的 e_nom/e_initial 固定，不能自行扩张；`Store-p >= 0` 保证资源只可消耗。PyPSA 0.30.3 的 Store 没有 p_min_pu/p_max_pu，方向依赖显式 Linopy hook，不能把无效属性当约束。

国家间资源没有共享 Bus/Store，也没有贸易 Link。全局价格信息可以共享，物理库存不可以。实际国家分配仍 PENDING，合成测试 30+70=100 只是守恒 fixture，绝不是研究输入。

历史审计把 110 条 biomass 多国访问记录标为 SHARED_RESOURCE_ACCESS_NOT_A_TO_B_INJECTION，不伪称直接双向流。biogas 的 location=Earth 也不能单凭字符串判定共享，审计使用真实 bus country/location 映射。

碳口径：biogas upgrading 的负大气端口在原源码中存在；biomass EOP 部分原 CO2 端口被注释。没有明确因子不能把缺失视为0，也不能默加生物碳中和。模型内 uptake/stack 与生命周期排放分别陈述。
''')
doc('PHASE4_CO2_PHYSICAL_ARCHITECTURE.md','''# 物理 CO2 与报告大气隔离

上游 `add_co2:1409–1543` 在 co2_network=false 时仍使用共同 co2 stored pool；不同国家的 capture、FT 与储存可以通过该物理池相连。开关 false 不能证明没有跨国 CO2 协同。新方案不通过开启跨国 pipeline 消除这个问题。

三类账户：

| 对象 | 物理角色 | Research 归属 |
|---|---|---|
| ReportingCO2 atmosphere | 环境/报告账；DAC 可从环境取碳 | ALLOWED_ACCOUNTING_GLOBAL，policy carrier factor=0 |
| co2 captured | 捕集后可供本地 FT 等使用的原料 | 国家/节点独立；须另有来源追踪 |
| co2 sequestered | 永久地质库存 | 国家/节点独立、不可回取、不允许供 FT/vent |

捕集池可流向当地地质库；地质 Store 使用 e_nom_extendable=true、e_nom_max=接受容量、e_initial=0、e_cyclic=false，保留 capital_cost 的投资成本含义。显式 `Store-p <= 0` 阻止回取。不能把原每吨容量成本默改成吞吐边际费用。

上游 `solve_network:939–954` 的末期总库存 <=200 Mt 是另一个资源限制，且默认潜力带欧洲 TODO；它既不是 Power 碳预算，也不是各国200 Mt。本轮不采用或分配这个值。

FT 的 H2、captured CO2、电力输入与油输出全部属同一国家。多端口输入为负 efficiency2/3，测试检查符号与 p_min_pu>=0。地质库存不进入 FT。共同 atmosphere 不能用于点源捕集的跨国搬运；环境移除须显式 accepted DAC/origin 语义，不自动创建 DAC。

工业 process emissions 共同池失去国别/来源，不能沿用后再宣称隔离。必须在已接受的工业输入与映射上重建，当前 deferred。物理隔离不等于已完成混合 CO2/oil 池的来源核算，真实流归属仍是 blocker。
''')
doc('PHASE4_CURRENT_CO2_SCOPE_TRACE.md',f'''# 当前 CO2 实现链

直接证据来自 Gate2 HEAD `{base}` 的三个源码字节副本及当前安装的 PyPSA 0.30.3 `define_primary_energy_limit`。副本位于 `evidence/source/scripts/` 与 `evidence/PYPSA_PRIMARY_ENERGY_FUNCTION.py`；不拿旧文档行号代替当前快照。

| 链条 | 当前实现与风险 |
|---|---|
| prepare_sector_network.add_co2_budget:3578–3639 | annual=base_value*year factor，再乘 sum(objective weights)/8760；没有 power 用途过滤 |
| prepare_network.add_co2limit:149 | CO2Limit、carrier_attribute=co2_emissions，默认 primary_energy |
| PyPSA define_primary_energy_limit | Generator 加权 p*因子/效率 + 非循环 Store 的末期/初始库存项；不是 sector 标签筛选 |
| add_co2 | atmosphere carrier co2_emissions=-1，因此大气末期增量进入旧总账 |
| convert_conventional_generators_to_links:3720–3809 | 燃烧 Link 的 atmosphere 端口报告排放；fuel 源 carrier 因子设0，避免源+燃烧双计 |
| solve_network:939–954 | stored CO2 总库存上限，属于物理资源，不能替代政策预算 |

当前 baseline `co2.budget.enable=false` 保持不变。已有 DEC 年度限额不变：2025/2030/2035/2040/2045/2050 = 1000/820/640/460/280/100 MtCO2。不能为本轮测试将 baseline 自动打开，也不引入国家配额。

恢复非电部门后沿用 aggregate atmosphere cap 会让非电燃烧消耗 Power cap。新接口只接受明确的发电/原供电用途系数表达式，不以“与电网连通”或“名字像化石发电”替代边界。供电 H2/SMR、CHP 分摊与 geothermal 等原因子均不能遗漏。

参考映射 1354 条：283 标作 Power 候选，638 非 Power，288 共享用途待定，145 捕集/来源待定。所有行 `NumericAccepted=false`；True 是范围候选分类，不是参数确认。缺少 emission factor 的行保留空缺。该表来自历史 tutorial + 当前源码角色比对，不是 paper 复现，也不是新 Research 组件清单。

`install_power_policy` 拒绝未完成 scope、非电权重、重复组件以及遗留 aggregate cap 共存；以物理 generators snapshot weights 计算排放，要求与原 objective hours 总和一致，保留 /8760 缩放。安装只作用于已有变量，不调用 create_model 或 solve。本轮 Linopy 仅合成变量，检查 RHS 与实际变量标签，无优化。
''')
doc('PHASE4_CARBON_ACCOUNTING_ARCHITECTURE.md','''# PolicyCO2_Power 与 ReportingCO2_FullSystem

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
''')
doc('PHASE4_GATE3_TEST_REPORT.md',f'''# Gate3 测试与证据边界

| Suite | 结果 | 证据 |
|---|---|---|
| 新载体/碳/真实 PyPSA fragment + 未求解 Linopy 系数 | {test['tests']}/{test['tests']} PASS | GATE3_TEST_RESULTS.json、gate3_tests.log |
| Buildings strict E1/E2/E4 | 1062/1062 assertions PASS | BUILDINGS_REGRESSION.json |
| Shipping | 17/17 tests PASS | SHIPPING_REGRESSION.json |
| Gate2 demand | 70/70 tests PASS | gate2_regression_70.log |
| Gate1 static | 20/20 tests PASS | gate1_static_regression.log |
| Manifest schema | 7/7 tests PASS | gate1_manifest_regression.log |
| Gate2 数据/脚本字节守卫 | 21/21 PASS | GATE2_HASH_GUARD.json |

Buildings 1062 是逐行 assertions，其他数量是 unittest 方法，不混称独立实验。所有测试为静态/合成 fixture，无求解、无正式需求物化。最终实现 SHA `{HEAD}`。首次59方法通过后，对价格元数据窄修复重跑新增到60的受影响套件与配置门禁；上游及 Gate2 输入未变，旧 suite 结果继续有效。

11 国模板：{config['template_buses']} Bus、{config['template_components']} 候选组件，全部{config['pending_numeric_components']}候选未接受、无真实 Load；方向图无跨国载体可达路径。可达图包含 PENDING 技术方向，非空图，且变异测试能检出错误跨国端口。它是多输入转换的潜在路径上界，不是可行调度证明。

有效参考证据复用：历史6306条组件审计、280条共享/路径风险记录；其中110 CO2方向路径、110 biomass共资源访问、60 lignite共资源访问。没有篡改历史网络以制造“已修好”的结论。电力记录分开标记 historical tutorial 与 current pinned raw topology；最终 clustered 网络尚无。

PROJ 数据目录提示及旧配置弃用警告仍出现在现有环境日志；本轮所有相关测试完成并通过，未调整环境，也未据此宣称 GIS/完整 workflow 就绪。

## 可复核命令（从模型根目录、既有 pypsa-earth 环境）
```text
python scripts_project/run_gate3_validation.py --output /tmp/gate3-review
python scripts_project/check_research_carriers.py --output /tmp/gate3-review/config.json
python tests/research/test_demand_accounting.py
python tests/research/test_phase4_static.py
python tests/research/test_run_manifest_schema.py
python tests/transport/test_shipping_allocation.py . /tmp/gate3-review/shipping.json
python tests/research/approved_buildings_regressions.py --repo . --fix combined --output /tmp/gate3-review/buildings.json
```

`audit_reference.py --evidence <evidence-dir>` 可从冻结 JSON 重做方向图审计；当前未重跑。`complete_source_audit.py` 还要求原历史 NetCDF/原 pinned raw topology，并先核验 NetCDF SHA。工具副本用于追溯；不是可直接组装 Full-SC 的入口。
''')
doc('PHASE4_GATE3_READINESS.md',f'''# Gate3 完成，停在 Gate4 之前

已实现并验证国家/节点载体接口、有限资源守卫、单向外部供给、物理碳库存、Power 政策表达式与全系统事件账。审计和实现交付完成；尚不满足真实 Full-SC 网络组装的输入与归属验收条件。

```text
'''+ '\n'.join(k+' = '+v for k,v in statuses.items())+'''
```

`PARTIAL` 的统一含义：接受数值上的结构接口与合成测试通过，但真实 Research 网络未组装，历史网络共享池未被原地修改，真实共同用途/碳来源未全部归属。不能把“新模板无非法路径”扩大为“完整模型全部消除”；不能把 reporting 函数可用扩大为真实全系统碳账完整。clean/main 状态以包根 CLOSEOUT.json 的最终本地/远程核验为准。

## 必须处理的系统级前提
'''+ '\n'.join(f"- **{b['ID']}** — {b['Issue']}。{b['Required']}。" for b in blockers)+'''

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
''')
for p in D.glob('*.md'):shutil.copyfile(p,G/p.name)
with (G/'GATE3_DRAFT_DIFF_REVIEW.md').open('a',encoding='utf-8') as f:
 f.write('\n## 集成前审阅落实与窄修复\n\n地质 Store 改为有明确上限的投资变量，禁止 Link 反向流，分摊后内部碳转移仍不能产生负信用；均经合成测试。集成使用六文件 allowlist。最终精确差异在 evidence/final_diffs。额外窄修复只将价格元数据与各国可用量解耦（独立 commit），无参数变更。没有 E 类内容合入。\n')
doc('README.md','''# Phase4 Gate3 交付导航

从 PHASE4_GATE3_READINESS.md 阅读范围与系统前提；随后看 TEST_REPORT、START_IDENTITY、RESUME_INVENTORY 与 DRAFT_DIFF_REVIEW。七张 CSV 均可筛选 Evidence/Status。CSV 是审计数据合同，UTF-8 BOM、引号与 CRLF；空 emission factor 表示未明确，不等于零。

PHASE4_CARRIER_REACHABILITY_AUDIT / HIDDEN_CROSSBORDER_PATHS / CO2_POLICY_COMPONENT_MAP 的对象是历史 tutorial reference。ELECTRICITY_LINK_CLASSIFICATION 用 Evidence 列区分历史与 current raw 两个层级，不能混加形成一个网络。

源数据与设计冻结文档在 evidence/，可追踪到 byte SHA；sources manifest 不包含自身。JSON 原记录不被表格清洗覆盖，Infinity/NaN 等原快照缺失/无限标志保持原样。CSV 仅投影字段；不存在未确认数据的 CONFIRMED 升级。

所有静态工具、源代码、测试、审计与运行记录可由 Git 历史复核。交付包只包含 Gate3 新文件/配置和审计证据，不代替整个模型仓库。未求解的 fragment 也不是正式结果。最终提交/远程对齐与包内容 SHA 在包根 CLOSEOUT.json / SHA256SUMS.json。
''')
(G/'.gitignore').write_text('!*.csv\n!*.log\n!*.json\n')
(G/'.gitattributes').write_text('* -text\n')
GE=G/'evidence';GE.mkdir(exist_ok=True)
for p in E.rglob('*'):
 if p.is_file() and 'previews' not in p.parts:
  q=GE/p.relative_to(E);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
tools=GE/'tools';tools.mkdir(exist_ok=True)
for name in ['probe.py','audit_reference.py','complete_source_audit.py','resume_inventory.py','integrate.py','review_fix.py','build_delivery.py']:
 shutil.copyfile(W/name,tools/name)
freeze=GE/'phase3_design';freeze.mkdir(exist_ok=True)
native=W.parents[1]
for name in ['CARBON_SCOPE_FREEZE.md','CROSS_BORDER_INTERVENTION_CONTRACT.md','EXTERNAL_COMMODITY_SUPPLY_BOUNDARY.md','FULLSC_CARRIER_INVENTORY.md']:
 shutil.copyfile(native/'research/02_sector_coupling/phase3c'/name,freeze/name)
(GE/'EVIDENCE_HASHES.json').write_text(json.dumps({p.relative_to(GE).as_posix():sha(p) for p in sorted(GE.rglob('*')) if p.is_file() and p.name!='EVIDENCE_HASHES.json'},indent=2))
print(json.dumps({'implementation_head':HEAD,'tables':{k:len(v['export_values'])-1 for k,v in tables.items()},'reports':len(list(G.glob('*.md')))},indent=2))
