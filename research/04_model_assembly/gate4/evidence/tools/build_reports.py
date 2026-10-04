"""Report observed Gate4 stop honestly; never manufacture an actual network."""
from pathlib import Path
import json,hashlib,collections,shutil
W=Path(__file__).resolve().parent;E=W/'evidence';S=W/'stage';G=S/'research/04_model_assembly/gate4';G.mkdir(parents=True,exist_ok=True)
B=W/'build';B.mkdir(exist_ok=True)
def load(name):return json.loads((E/name).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def doc(name,text):(G/name).write_text(text.strip()+'\n',encoding='utf-8')
start=load('START.json');fix=load('TOPOLOGY_FIX_PROOF.json');freeze=load('ASSEMBLY_FREEZE_COUNTS.json');pre=load('ASSEMBLY_PREFLIGHT.json');commits=load('INPUT_COMMITS.json');head=commits[-1]['head']
registry=json.loads((S/'research_inputs/assembly_v1/registry.json').read_text());records=registry['records'];countries=sorted({r['Country'] for r in records if r['Kind']=='DEMAND'})
assert pre['status']=='BLOCKED_INPUT_FREEZE' and pre['network_exported'] is False
blockers=[
dict(ID='G4-INPUT-01',Group='INPUT_FREEZE',MaterialImpact='2050 final electricity, Road/EV and fixed fuel quantities directly determine capacity, electrification, H2/FT fuel supply and interconnection value',Affected='All 11 national direct-electricity parents; major-country Buildings/Transport/Industry/Agriculture and four shipping/aviation accounts',MinimumResolution='One traceable, jointly consistent 2050 direct A* and sector final-energy/growth input set; Road R and final-energy share with compatible residual carriers; preserve embedded children; no DEFAULT or generation target',Status='OPEN',Evidence='ASSEMBLY_PREFLIGHT.json; GROWTH_SOURCE_REVIEW.json; Phase3 Road/Industry contracts'),
dict(ID='G4-INPUT-02',Group='INPUT_FREEZE',MaterialImpact='Fuel heat basis, price and availability change gas/coal/oil costs, substitution and conversion demand; unavailable biomass cannot silently erase positive fuel obligations',Affected='Country-owned external fossil fuel interfaces and source-supported biomass obligations',MinimumResolution='Close HHV/LHV compatibility and explicit source availability/capacity assumptions for frozen fuel records; retain independent country imports; source-qualified biomass resource allocation or documented unavailable supply, without erasing demand',Status='OPEN',Evidence='COST_CANDIDATES_2050.json; Assembly registry; Gate3 external supply contract'),
dict(ID='G4-CARBON-01',Group='CARBON_ATTRIBUTION',MaterialImpact='Shared SMR/CHP/captured-carbon/FT attribution can move non-power emissions or credits into the unchanged Power cap and falsely treat recycled fuel as neutral',Affected='Power-supplying H2 plus non-power H2/FT uses and mixed captured CO2/oil pools',MinimumResolution='Map actual emitting/conversion roles and implement accepted conserving attribution/origin tracing on the assembled components; validate reference power expression equivalence without solve',Status='OPEN_BEFORE_VALIDATED_ASSEMBLY',Evidence='Gate3 PHASE4_CARBON_ACCOUNTING_ARCHITECTURE; CARBON_SCOPE_FREEZE')]
tables={}
def table(name,rows):
 headers=list(dict.fromkeys(k for r in rows for k in r))
 def value(v):return '' if v is None else json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v
 tables[name]={'export_values':[headers]+[[value(r.get(k)) for k in headers] for r in rows]}
table('PHASE4_ASSEMBLY_INPUT_REGISTRY.csv',records)
ref=json.loads((W.parent/'phase4_gate3/evidence/TUTORIAL_COMPONENTS.json').read_text())
table('PHASE4_NETWORK_COMPONENT_INVENTORY.csv',[dict(Component=c,ActualCount=None,Country='NOT_AVAILABLE',Carrier='NOT_AVAILABLE',Sector='NOT_AVAILABLE',Status='NOT_RUN_NO_RESEARCH_NETWORK',HistoricalTutorialCount=len(ref['tables'][c]) if c in ref['tables'] else None,HistoricalScope='TUTORIAL_REFERENCE_NOT_CURRENT_ASSEMBLY',Reason='Input freeze failed before actual network construction') for c in ['Bus','Load','Generator','Link','Store','StorageUnit','Line','Transformer','GlobalConstraint']])
table('PHASE4_ACTUAL_DEMAND_CONSERVATION.csv',[dict(Country=r['Country'],Year=r['Year'],Sector=r['Sector'],Account=r['Account'],Carrier=r['Carrier'],SourceAnnualValue=r['Value'],SectorLedgerValue=r['Value'] if r['AssemblyStatus']=='ASSEMBLY_V1_ACCEPTED' else None,NodeSum=None,WeightedTimeSum=None,Unit=r['Unit'],SourceToLedger='PASS_BASEYEAR_ONLY' if r['AssemblyStatus']=='ASSEMBLY_V1_ACCEPTED' else 'PENDING',ActualNetworkStatus='NOT_RUN_NO_RESEARCH_NETWORK',Evidence=r['InputID'],ToleranceMWh='1e-6 absolute / 1e-10 relative') for r in records if r['Kind']=='DEMAND'])
rules=[('Astar','No unverified all-sector subtraction or AEO8 generation target'),('Buildings','No explicit heat Load for embedded accounts'),('EV','Future direct Astar excludes same explicit EV obligation'),('Conversion','No preloaded electrolysis/FT/HP electricity'),('Rail','Embedded once, no duplicate independent rail Load'),('Bunkers','Domestic and international shipping/aviation accounts remain distinct'),('IndustrialCoal','Physical fuel-energy obligation accompanies combustion reporting'),('Agriculture','All accepted oil/biomass/coal obligations retained')]
table('PHASE4_ACTUAL_EXACTLY_ONCE_TESTS.csv',[dict(Account=x,RequiredRule=y,ActualStatus='NOT_RUN_NO_RESEARCH_NETWORK',SyntheticPriorEvidence='Gate2/Gate3 preserved; not actual-network proof',NetworkFile=None) for x,y in rules])
table('PHASE4_ACTUAL_CARRIER_REACHABILITY.csv',[dict(Carrier=x,Countries='11 ASEAN; directed A-to-B checks pending',PhysicalCrossBorderAllowed=False,ActualPathCount=None,ActualStatus='NOT_RUN_NO_RESEARCH_NETWORK',PriorTemplateStatus='PASS_GATE3_ONLY',NetworkFile=None) for x in ['H2','gas','captured CO2','stored CO2','solid biomass','biogas','synthetic oil']])
table('PHASE4_ACTUAL_CARBON_ATTRIBUTION.csv',[dict(Component=None,Sector=x,PowerPolicyExpected='ACCEPTED_POWER_ROLE_ONLY' if x=='Power' else 'NO_DIRECT_NONPOWER_EMISSIONS',FullSystemReportingExpected=True,ActualPolicyOwnership='NOT_EVALUATED_NO_COMPONENTS',Status='NOT_RUN_NO_RESEARCH_NETWORK',ScopeRisk='Shared use/origin requires explicit tracing') for x in ['Power','Buildings','Road','Industry','Agriculture','DomesticShipping','InternationalShipping','DomesticAviation','InternationalAviation']])
table('PHASE4_ACTUAL_ELECTRICITY_LINK_CLASSIFICATION.csv',[dict(Component=x,Name=None,Country0=None,Country1=None,Carrier=None,ExistingCapacity=None,Expandable=None,FutureScenarioControl='NOT_ESTABLISHED',Classification='NOT_EVALUATED_NO_NETWORK',Evidence='Raw topology PASS is not a clustered actual-network control set') for x in ['Line','Link','Transformer']])
paths=[('Electricity → EV','electricity','EV charging','EV obligation','Target Road energy and EV energy share missing'),('Electricity → H2','electricity','H2 Electrolysis','local H2 uses','Four electrolyser assumptions frozen; no assembled components'),('H2 → Industry','H2','qualified industry interface','industry H2','DEFERRED where no accepted industrial H2/service'),('Electricity/H2/CO2 → FT','electricity;H2;captured CO2','Fischer-Tropsch','synthetic oil','Requires local carbon origins and coherent fuel obligations'),('FT → fixed transport/bunker fuels','synthetic oil','final-fuel interface','shipping;aviation;road','Demand quantities and fuel/origin attribution pending'),('Electricity → heat','electricity','qualified heat conversion','explicit heat service','NOT_REQUIRED where Buildings service remains embedded')]
table('PHASE4_ACTIVE_SECTOR_COUPLING_PATHWAYS.csv',[dict(Pathway=x,InputCarrier=i,Technology=t,OutputCarrier=o,DemandSink=o,CapacityStatus='NO_ACTUAL_COMPONENTS',DemandStatus=d,CanCarryNonzeroFlow='NOT_TESTED',ScientificRole='Existing Research design only; not observed active pathway',ActualStatus='NOT_RUN_NO_RESEARCH_NETWORK') for x,i,t,o,d in paths])
table('PHASE4_GATE4_BLOCKERS.csv',blockers)
(B/'tables.json').write_text(json.dumps(tables,ensure_ascii=False))
statuses=dict(ASSEMBLY_INPUTS_FROZEN='PARTIAL',TOPOLOGY_REFERENTIAL_INTEGRITY='PASS',FIRST_FULLSC_UNSOLVED_NETWORK_BUILT='NO',SOLVER_RUNS_EXECUTED=0,ACTUAL_NETWORK_FINITE_VALUES='FAIL',ACTUAL_DEMAND_CONSERVATION='FAIL',ACTUAL_EXACTLY_ONCE_ACCOUNTING='FAIL',HIDDEN_CROSSBORDER_CARRIER_SHARING='PARTIAL',ACTUAL_POWER_CO2_SCOPE='FAIL',ACTIVE_SECTOR_COUPLING_PATHWAYS='FAIL',ELECTRICITY_INTERCONNECTION_CONTROL_SET_READY='NO',FULL_SC_RESEARCH_NETWORK_STATICALLY_VALIDATED='NO',READY_FOR_PHASE4_GATE5_VALIDATION_SOLVE='NO')
(E/'FINAL_STATUS.json').write_text(json.dumps(dict(statuses=statuses,actual_check_failure_reason='NOT_RUN_NO_RESEARCH_NETWORK; failed readiness criterion, not an observed invalid network'),indent=2))
doc('PHASE4_GATE4_START_IDENTITY.md',f'''# Gate4 起点与工程范围

用户授权起点 `{start['head']}`，Research 本地/远程相同、working tree clean。main=`a3616a68ee44592af6527ca9024a90f1956646ae`。本轮于客户端日期 2026-10-05 工作，未重开 Phase1–3 设计。身份原记录：evidence/START.json。

本轮授权：输入冻结、765/766 溯源修复、满足门禁后的未求解 Full-SC 构网与实际网络静态检查。求解器、正式情景比较仍禁止。实际推进到输入门禁及独立拓扑修复；未越过未闭合的目标年数值门槛。

已分开提交：

- `{load('TOPOLOGY_COMMIT.json')['head']}` — 删除唯一过时变压器引用。
- `{commits[0]['head']}` — Assembly V1 来源合格的部分输入冻结。
- `{head}` — 失败即停止的输入预检、回归与配置防护。

最终审计提交/远程结果在交付包 CLOSEOUT.json，不把“预检实现 SHA”误称为构网 SHA。Gate2 输入及 Gate2/Gate3 控制块未改；参考/归档分支不操作。尚无 Research `.nc`。
''')
parents=[r for r in records if r['Kind']=='DEMAND' and r['AssemblyStatus']=='ASSEMBLY_V1_ACCEPTED']
doc('PHASE4_ASSEMBLY_INPUT_FREEZE.md','''# Assembly V1：部分冻结，目标年门禁未通过

**45 条 ASSEMBLY_V1_ACCEPTED，531 条 PENDING，共576条登记。** 接受状态严格区别于 HUMAN_ACCEPTED；原 Gate2 状态/文件不改。45条包含11个2019电力父账数值、4个2050电解参数、6个原Power年度限额、22个R/S表示控制、2个供给可用性控制；不是45个已就绪2050需求。

## 可冻结内容

2019 A* 来自现有 UNSD 原文件 `UNdata_Export_20250502_110820872.txt`，SHA256 `12c99b3c40927449d9a4d0402f255a8b84b24917ff58e54efd4ec43b2125fe6b`。精确 transaction=`Electricity - Final energy consumption`，million kWh ×1000=MWh。原始十进制转换与 Gate2 浮点文本差值均≤1e-6 MWh，差值单列，不做 residual correction。

| 国家 | 2019 A*（MWh/year） |
|---|---:|
'''+ '\n'.join('| '+r['Country']+' | '+r['Value']+' |' for r in parents)+'''

这些是基年锚点。没有将2019值改名为2050，没有设定零增长，没有从A*减去所有UNSD sector rows；未证明互斥的子账户留在父账。未来 EV/电解/FT/HP 电量不能预载到 direct A*。AEO8 generation 继续不作为目标；这不是对实际网络已经验证的声明。

2050 电解参数沿用原 v0.13.2：efficiency=0.6994（LHV H2/electric input）、lifetime=25年、FOM=4%/年、investment=1000 EUR2020/kW_e。现有 pre_costs_2050 与已恢复官方 SHA `ec22a184…` 输出逐字节相同，未更新DEA。前三项已有旧sheet86链；投资为公开冻结 manual override 所载原情景假设，按本轮优先级3沿用，原 private communications 无独立实证核验作为限制保留，不能称为“私人来源已恢复”。未激活组件。

Power原限额 2025/2030/2035/2040/2045/2050=1000/820/640/460/280/100 MtCO2/year，baseline enable=false；预算年份不是需求预测来源。

地质库采用本轮明确允许的无储存资产 fallback，潜力数值仍 unknown，不创建无限储存；biomass无接受分配的资源暂不可用，不复制360 TWh，也不引入无上限进口。二者是可用性控制，不是观测到自然资源=0。未来正生物质义务仍必须保留；该供给限制可能使验证模型不可行，不能静默删除需求。无地质库会排除永久封存但不自动禁止有来源的本地CO2→FT原料回用。

## 2050 阻断与最低资料

现有通用增长/工业增长文件只有 DEFAULT、MA、NA、US（效率文件 DEFAULT、MA、US），无 ASEAN 专属行；Git 历史显示通用默认值，不提供所需的 ASEAN growth 依据。`prepare_energy_totals` 又有列对齐后 fillna(0)；旧未来缓存不能充当合格预测。`FUTURE_INDUSTRY_GROWTH_BLOCKER` 保留。

旧 DEC_2050 EV share=1 同时参与车种效率/车辆处理，未证明是本轮要求的最终能耗份额。不得仅改名为 s_E；R 和 s_E 必须联合定义，使 EV=R*s_E 与各残余燃料同一基准。原无量纲/里程混用道路链未启用。

2050需要的275个物理需求记录均未接受（11电力、88 Buildings、77 Transport、44 Industry、33 Agriculture、22国际bunker）；这是依赖账本计数，**不是要求用户分别找275份新资料**。需要的是一套相容的目标年 direct A*、道路最终能耗/份额、各主要部门增长/燃料义务；可采用已有可靠数据或明确来源的简约方法，不能由程序默认补值。空间/时序分配也尚未被物化，空 allocation_missing 仅因无 accepted 2050需求，绝不等于分配已通过。

煤/气/油价格原输出分别为9.5542、24.568、52.9111 EUR2020/MWh_th；source currency_year 仍保留2010/2015，不能再通胀。热值匹配、国家容量/年可用量尚未闭合，数值保留 PENDING。外部供给不等于跨国物理通道或能源自给。

TL无来源独立工业子账户不单列为阻断整个 ASEAN 的原因；保留A*与未知覆盖限制。当前主要阻断来自所有国家目标年父账和主要部门数值，不是要求完整TL工业微观调查。

## Buildings 国家×部门表示矩阵（冻结设计，实际网络未构建）

| Country | Residential | Services | Explicit heat |
|---|---|---|---|
'''+ '\n'.join('| '+c+' | electricity embedded in A*; fixed fuels pending | electricity embedded in A*; fixed fuels pending | none accepted; no default heat Load |' for c in countries)+'''

Cooling嵌入；Cooking仅核算；space/water heat未有合格服务量时保持嵌入；不造stock、uniform district heating或BDEW需求。R/S分开标识并不意味数据完整或有新增Load。农业油/biomass/煤、工业煤实际能源量、四类国内/国际船/航空义务均保留输入门禁，未以只有排放的Load替代燃料。
''')
doc('PHASE4_TOPOLOGY_FIX_REPORT.md',f'''# 765/766：证据支持删除过时引用

**Referential integrity PASS；仅删除 `transf_524_0` 一行。** bus765、其余2520个现有节点和所有其他数据行未改，无新造bus。

上游引入提交 `138ea07b21c55727c937831c396e80286b5ef586` 的 `data/osm-plus-prebuilt/0.1.1/modification_list.txt` 明确在Thailand条目删除766/772。0.1中766为station524的230kV层，只接765→766变压器，没有Line、converter或clean-generator引用；0.1.1及作者paper run树 `5bacad70…` 都仍遗留这条变压器。恢复766会恢复作者明确删除的层级，没有独立证据支持，所以选最小删除遗留引用。

修复前测试记录引用缺失766，失败；修复后9项测试通过。Transformer 651→650，Line3441、Link17、Bus2520、clean Generators1982不变；对全部保留Bus构造的有效端点连通分组前后完全一致。765本来没有有效线路邻接，其孤立状态没有被本轮新增或掩盖；未在此步骤删除其未来应保留的国家能源。

输入 transformer SHA256：

- before `{fix['input_hashes_before']['all_transformers_build_network.csv']}`
- after `{fix['input_hashes_after']['all_transformers_build_network.csv']}`

源码与测试先写入，测试失败后才编辑数据。`TOPOLOGY_FIX_PROOF.json` 包含全部前后端点/连通分组，`TOPOLOGY_FIX.diff` 为精确一行删除。修复隔离于 commit `{load('TOPOLOGY_COMMIT.json')['head']}`，未混入需求、碳或配置修改。参考树/原tutorial文件不改。

首次验证器把三条跨国Transformer标签与无效国家混在一起；已纠正为归属复核项，而不是改源数据让测试通过。`transf_407_0`、`transf_443_0`、`transf_501_0` 具有合法但不同的两端country；保留显式复核标记。PASS只覆盖引用/合法元数据，不能据此宣称这些源标签已验证为真实跨境换电设施，也不能直接放进Gate5最终控制集。

原始电力边现在4108条，按现有标签4046 domestic / 62 cross-border / 0 unknown；这是未聚类原始层。尚无实际Research网络，最终控制集仍未就绪。
''')
doc('PHASE4_RESEARCH_BUILD_CONFIG.md','''# Research 配置：已加防护，尚不是可运行完整构网配置

沿用 base config + project overrides。`research_demand`、`research_carrier_architecture`、`research_carbon` 的 Gate2/Gate3 控制块保持逐字段一致；Integrated/Disconnected overlays 无改变。

新增 Research override：

- `demand_data.update_data=false`：不刷新已经冻结的数据。
- `final_adjustment.only_elec_network=false`：解除已知只留电力的最终裁剪设置。
- `research_assembly.target_year=2050`，新状态 ASSEMBLY_V1_ACCEPTED，固定registry路径。
- `legacy_final_adjustment=forbidden`、`legacy_sector_demand_builders=forbidden`：旧最终校准还可能重写电力量，不能仅关裁剪就直接复用整个旧函数。
- `network_export_enabled=false`、`solver_allowed=false`、scenario_switching=false；目标年fallback禁止。

配置不能以“开关写成true”代替输入通过。本轮预检已实际执行：

```text
python scripts_project/check_assembly_inputs.py --year 2050 --output <review.json>
```

返回码2、状态BLOCKED_INPUT_FREEZE；没有调用Snakefile构网、任何solve rule、n.optimize/lopf或solver CLI。`composition.runnable_workflow=false` 明确保留，并解释为何阻断。没有提交名为“assemble first network”的虚假实现或空网络占位文件。用户要求的完整可运行baseline/网络导出尚未达成。

既有完整配置的2013天气、全年快照、100 clusters与3h选项仅是请求规格；未验证实际网络的snapshot数量、weight sum或空间归属。以后必须运行独立国家→节点→时间守恒，并检查objective与physical权重，不把tutorial六天50clusters网络改名当本次成果。

Policy baseline仍关闭预算；六年原DEC轨迹保留，未引入新的whole-system cap。无地质储存和不支持biomass资源的可用性fallback不会激活负Load或伪造零需求；两者真正组件效果尚未执行。
''')
manifest=dict(network_id='research_fullsc_2050_assembly_v1_NOT_BUILT',build_status='BLOCKED_INPUT_FREEZE',git_commit=head,branch='research/full-sc-baseline',config=['configs/research/baseline.yaml','configs/research/composition.json'],config_sha256=None,input_registry_sha256=sha(S/'research_inputs/assembly_v1/registry.json'),network_file=None,network_sha256=None,network_size_bytes=None,build_time=None,Python_version='3.11.13',PyPSA_version='0.30.3',year=2050,weather_year=2013,spatial_resolution='requested upstream 100 clusters; NOT_BUILT',snapshot_count=None,physical_weight_sum=None,objective_weight_sum=None,component_counts=None,demand_ledger_version='Gate2 pinned + assembly-v1-freeze-1',carrier_architecture_version='Gate3 140294807bffe5cc172d5226ee0af3d4f548d180',carbon_architecture_version='Gate3 631b27bb; see exact Git ancestry',solver_status='NOT_RUN',solver_runs=0,network_exported=False,actual_fields_null_reason='No actual network exists; metadata must not be fabricated',preflight_evidence='evidence/ASSEMBLY_PREFLIGHT.json')
(G/'PHASE4_FIRST_FULLSC_NETWORK_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
doc('PHASE4_GATE4_TEST_REPORT.md',f'''# Gate4 检查结果

| 检查 | 结果 | 范围 |
|---|---|---|
| 修复前原始拓扑 | FAIL（期望） | 唯一悬空Transformer端点766；非实际Full-SC网络 |
| 拓扑修复/变异测试 | 9/9 PASS | 端点、重复bus、元数据异常；保留节点分组不变 |
| Assembly输入测试 | 12/12 PASS | 源hash、重复父账、missing!=0、基年不可改成未来、状态/单位门禁 |
| 2050实际预检 | BLOCKED，返回码2 | 275个所需需求未接受；未开始构网 |
| Gate1静态回归 | 20/20 PASS | 配置及既有检查接口 |
| Gate2会计回归 | 70/70 PASS | 旧需求/父账规则 |
| Gate3回归 | 60/60 PASS | 合成fragment/未求解Linopy，不是实际网络 |
| Gate2输入hash/旧控制块 | PASS | 原表字节不变，Research旧契约不变 |
| 实际网络有限值/守恒/路径/碳/控制集 | NOT_RUN | 无 `.nc`，不得写PASS |

没有 solver、优化目标求解或正式实验。Buildings1062、Shipping17在Gate3已通过，本轮相关源码未变、沿用其有效证据；不重复无关实验。PROJ目录提示仍为已知环境限制，本轮未因此改环境，不能推断完整GIS工作流已就绪。

最终测试实现 SHA `{head}`。Input gate的通过只代表可继续其他验证，本身不代表完整网络可组装；当前该门禁没有通过。实际结果CSV以NOT_RUN/空计数明确区别unknown与0。A* source→ledger原值闭合仅是2019一层证据，不能扩大到2050/节点/时间。

工具命令、固定源、前后日志和hash在evidence。没有调用旧growth fillna(0)、未接受的道路公式、默认heat Load、重复工业电或排放-only工业煤。下次工作需从真正输入缺口续接，无需重复765/766溯源。
''')
answers=[('A','冻结11个2019 A*、4个2050电解参数、6个原预算、24个表示/可用性控制；45项并非45个目标年需求。'),('B','531条PENDING，其中275个所需2050物理需求全部尚未合格；按三个系统问题合并，不是531个新研究任务。'),('C','没有 assembled network。接受的锚点为UNSD2019 national final energy consumption，million kWh×1000；未变成2050。'),('D','Research输入和门禁排除AEO8 generation作为目标；无实际网络可检验。'),('E','R/S分别保留，cooling嵌入、无默认heat；表示矩阵明确。实际Load尚无。'),('F','R=EV+残余燃料的最终能源合同维持；旧share/道路公式不合格，未实例化2050。'),('G','煤/biomass/oil/gas义务与未知状态保留，未丢载体；实际网络守恒NOT_RUN。'),('H','国内船、国际marine bunker、国内航空、国际aviation bunker四账仍分开；未建真实Load。'),('I','作者明确删除766，遗留变压器唯一引用；删除transf_524_0一行，不恢复不存在的bus。'),('J','否；预检返回BLOCKED_INPUT_FREEZE，未执行full workflow/network export。'),('K','不存在首个Research Full-SC .nc，路径/大小/SHA均null，不用旧tutorial替代。'),('L','是，ZERO optimization solves；合成回归也没有求解。'),('M','未验证；没有实际accepted Loads，不能用空集合宣称finite PASS。'),('N','实际source→sector→node→time未执行；2019父账source→ledger闭合单独记录。'),('O','实际exactly-once未执行；Gate2规则及70项回归通过不能替代实网证明。'),('P','实网未知；Gate3模板通过仍有效，不能宣称完整模型已消除所有隐含通路。'),('Q','结构契约为独立国家供给接口/共享价格元数据；实际网络尚无。'),('R','否；真实组件未组装，SMR/CHP/capture/FT映射仍待闭合。'),('S','六年数值与原baseline关闭语义保持，Gate3静态表达式已测；实际网络政策层未建立。'),('T','尚无exact actual control set；raw标签62跨境只供参考，含3条待归属复核Transformer，不直接用于Gate5。'),('U','没有本轮实际active路径可报告；所列Electrolysis/EV/FT等为待验证设计。'),('V','没有Research网络，FULL_SC_REPRESENTATION不满足；未制造electricity+fixed Loads后称Full-SC。'),('W','目标年需求一致性、外部供给口径/可用量、真实混合用途碳归属三组；实际网络/分配验证随闭合后执行。'),('X','最终HEAD见包根CLOSEOUT.json；本文件列明测试实现SHA，未声称存在build SHA。'),('Y','main保持a3616a68…，最终远程核验见CLOSEOUT.json；不动reference/archive。')]
doc('PHASE4_GATE4_READINESS.md','''# Gate4 未通过：完成部分输入冻结与拓扑修复，未生成网络

已完成本轮可以独立核实的工程；**目标“第一份完整未求解 Full-SC 网络”尚未达成**。依用户“目标年存在实质歧义须在构网前标记”的规则，停止在输入门禁，不把基年改名为2050，不使用DEFAULT预测，不造空/示意网络。没有进入Gate5。

```text
'''+ '\n'.join(f'{k} = {v}' for k,v in statuses.items())+'''
```

实际网络项的FAIL表示**未满足验收条件，原因NOT_RUN_NO_RESEARCH_NETWORK**；不是发现一个已构建网络的NaN/错误流。报告CSV保留更精确的NOT_RUN状态，数值与文件身份留null而非0。PARTIAL仅指已有结构测试有效，不代表实际隐藏路径验证。

## 三组实质门槛
'''+ '\n'.join(f"- **{b['ID']} / {b['Group']}**：{b['MaterialImpact']}。最低解决：{b['MinimumResolution']}。" for b in blockers)+'''

小项作为限制：TL独立工业覆盖、未接受的Buildings细分保持嵌入、私有通信成本假设来源、三条原始跨国Transformer标签复核。没有发明材料性数值阈值，也没有无证据断言未知燃料影响小。无储存/biomass不可用是透明供给限制，不能抹去需求或提前保证可行性。

## A–Y 逐项回答

| 问题 | 回答 |
|---|---|
'''+ '\n'.join('| '+a+' | '+v+' |' for a,v in answers)+'''

## 证据等级

直接验证：Git身份、UNSD原始文件hash/行值、成本冻结输出同字节、growth国家覆盖、拓扑删除记录/端点与回归日志。

分析推导：直接父账不能按非互斥UNSD行相减；旧share不能直接当energy share；基年/目标年不等价；方向/年度守恒的验收规则。

已采用Assembly假设：仅明确列出的冻结上游电解参数和本轮授权的可用性fallback，来源限制可见，没有HUMAN_ACCEPTED升级。

未验证：实际Full-SC网络所有验收项、未来调度/成本/互联价值。报告不产生科学结果。需用户与ChatGPT复核记录中的目标年方法和边界后续接，不扩展为新研究阶段。
''')
doc('README.md','''# Gate4 blocked delivery

先读PHASE4_GATE4_READINESS与ASSEMBLY_INPUT_FREEZE。16项要求文件均提供，但无网络的actual表明确NOT_RUN；清单齐全不等于Gate4通过。网络manifest中的null为未生成，不是零规模网络。没有.nc成果。

research_inputs/assembly_v1 是独立部分冻结，原Gate2账本保持。SOURCE→raw→unit/year→transformation→Assembly status可追踪。CSV是registry.json的可审阅投影；ASSEM acceptance不等于HUMAN_ACCEPTED。

原始拓扑修复已用独立commit保存，一行数据删除通过前后验证。最终HEAD、remote保护引用、源/配置hash和包Git字节对应关系在CLOSEOUT.json / SHA256SUMS.json。实际网络项不得用历史tutorial/Gate3合成模板替代。
''')
(G/'.gitignore').write_text('!*.csv\n!*.json\n!*.log\n!*.txt\n');(G/'.gitattributes').write_text('* -text\n')
GE=G/'evidence';GE.mkdir(exist_ok=True)
for p in E.rglob('*'):
 if p.is_file():
  q=GE/p.relative_to(E);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
tools=GE/'tools';tools.mkdir(exist_ok=True)
for p in W.glob('*.py'):shutil.copyfile(p,tools/p.name)
(E/'DELIVERY_COUNTS.json').write_text(json.dumps({k:len(v['export_values'])-1 for k,v in tables.items()},indent=2))
print(json.dumps({'tables':{k:len(v['export_values'])-1 for k,v in tables.items()},'reports':len(list(G.glob('*.md'))),'status':'BLOCKED_BEFORE_NETWORK_CONSTRUCTION'},indent=2))
