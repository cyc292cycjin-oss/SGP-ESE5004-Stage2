"""Phase3A7 representation proposal from retained evidence, without model inputs.

Country-specific limitations remain separate from shared numerical assembly gates.
No source values, heat shares, COPs, profiles or model configs are created here.
"""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;P=R.parent
E=R/'evidence';E.mkdir(exist_ok=True);D=R/'data';D.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
files=[
 'phase3a4/BUILDINGS_E3_ACCOUNTING_SPEC.md',
 'phase3a4/BUILDINGS_USEFUL_HEAT_METHOD.md',
 'phase3a4/BUILDINGS_FIX_INTEGRATION_REPORT.md',
 'phase3a5/data/derived/buildings/ASEAN_BUILDINGS_HISTORICAL_ELECTRIC_HEATING_MATRIX.json',
 'phase3a5/data/derived/buildings/ASEAN_BUILDINGS_ENDUSE_EVIDENCE_MATRIX.json',
 'phase3a5/data/derived/buildings/BUILDINGS_USEFUL_HEAT_INPUT_CANDIDATES.json',
 'phase3a5/BUILDINGS_SPACE_WATER_MAPPING.md',
 'phase3a5/BUILDINGS_PHASE3A5_READINESS.md',
 'phase3a6/PHASE3A6_READINESS.md',
 'phase3a6/ASEAN_ELECTRICITY_BOUNDARY_TRACE.md',
 'phase3a6/ELECTRICITY_LOSS_ACCOUNTING.md',
 'phase3a6/MALAYSIA_2016_2019_YEAR_BRIDGE.md',
 'phase3a6/MALAYSIA_E3_ACCOUNTING_PROTOTYPE.md',
 'phase3a6/data/derived/PROTOTYPE_METRICS.json',
 'phase3a6/evidence/LOSS_CODE_IDENTITY.json']
evidence=[dict(path='../'+f,sha256=sha((P/f).read_bytes()),role='REUSED_PROJECT_EVIDENCE; scientific values retain prior status') for f in files]
request=Path('C:/Users/20122/.codex/attachments/ca4546e0-5f5b-461f-a0b7-50f21ccdbd21/已粘贴的文本.txt')
saved=E/'USER_PHASE3A7_REQUEST.txt'
if not saved.exists():saved.write_bytes(request.read_bytes())
evidence.append(dict(path='evidence/USER_PHASE3A7_REQUEST.txt',sha256=sha(saved.read_bytes()),role='DIRECT_HUMAN_INSTRUCTION; conceptual boundary and fallback policy only'))
(E/'INPUT_MANIFEST.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
heat=json.loads((P/files[3]).read_text(encoding='utf8'))
fuel=json.loads((P/files[4]).read_text(encoding='utf8'))
useful=json.loads((P/files[5]).read_text(encoding='utf8'))
assert len(heat)==44 and len(fuel)==154 and len(useful)==140
assert all(r['UsefulService']=='' for r in useful)
countries=['BN','KH','ID','LA','MM','MY','PH','SG','TH','TL','VN'];sectors=['Residential','Services']
notes={
 ('BN','Residential'):'仅保留UNSD终端能耗候选；既有有界证据未恢复国家space/water服务。',
 ('BN','Services'):'终端燃料/电力候选可保留；未恢复国家服务业热用途证据。',
 ('KH','Residential'):'ERIA城市/乡村混合燃料地方样本，含微小space记录；不能国家化或解释为全国电热量。',
 ('KH','Services'):'无足够国家服务业space/water服务量；保留原终端账户。',
 ('ID','Residential'):'ERIA地方water样本与住宅用途资料；舍入space零不是全国零，未闭合国家useful服务。',
 ('ID','Services'):'来源定义可含water，但未恢复兼容的全国数量/性能；不造服务量。',
 ('LA','Residential'):'ERIA城市water混合燃料样本不能代表全国及目标基年；保留原能耗。',
 ('LA','Services'):'无足够国家服务业space/water服务量；保留原终端账户。',
 ('MM','Residential'):'UNSD终端量候选为主要证据；没有可晋升的国家useful热账户。',
 ('MM','Services'):'UNSD终端量候选为主要证据；没有可晋升的国家useful热账户。',
 ('MY','Residential'):'NEB2016半岛water输入可核对；全国2019、R/S分类及历史设备性能未闭合。保留方法原型，不接国家基准。',
 ('MY','Services'):'NEB2016半岛商业water输入可核对；Commercial映射、表间差异、地域年份及性能仍待定。',
 ('PH','Residential'):'国家调查水热索引和ERIA地方资料已登记；原件/统计期及电量到服务链不完整。',
 ('PH','Services'):'国家服务业water/space输入链不足；不用住宅样本填服务业。',
 ('SG','Residential'):'典型户water份额和ERIA地方样本不能替代全国加权年量；space样本不外推。',
 ('SG','Services'):'没有可直接构建国家服务业useful热量的证据；不套住宅份额。',
 ('TH','Residential'):'ERIA地方water样本、BELDA所选地区行为证据；无兼容全国热服务量。',
 ('TH','Services'):'国家服务业热用途证据不足；保留原电力/燃料账户。',
 ('TL','Residential'):'主要为终端能耗候选；AEO10到模型11的TL总量边界须在系统层另核，不靠热份额补齐。',
 ('TL','Services'):'国家服务业热服务量不足；TL总量边界属于共享系统门槛。',
 ('VN','Residential'):'BELDA北部space与地方water、Hanoi小样本时序说明异质性；不能证明全国零或构造全国热服务。',
 ('VN','Services'):'没有兼容的国家服务业热服务量；住宅北部/小样本证据不移用。'}
boundary=[]
for c in countries:
 for s in sectors:
  rows=[(i+1,r) for i,r in enumerate(heat) if r['Country']==c and r['Sector']==s];assert len(rows)==2
  assert len([r for r in fuel if r['Country']==c and r['Sector']==s])==7
  refs='; '.join(f'P5_HEAT_ROW_{i:02}:{r["EndUse"]}' for i,r in rows)
  boundary.append(dict(Country=c,Sector=s,SpaceHeating='EMBEDDED',WaterHeating='EMBEDDED',Cooling='EMBEDDED',Cooking='EMBEDDED_ACCOUNTING_ONLY',DirectElectricity='EXPLICIT_SECTOR_ACCOUNT_KEEP_ONCE',DirectFuel='EXPLICIT_FUEL_ACCOUNTS_KEEP_ONCE_IF_PRESENT',Representation='EXPLICIT_R_S_FINAL_ACCOUNTS_WITH_EMBEDDED_THERMAL_USES',EvidenceStatus='THERMAL_SERVICE_NOT_COMPATIBLE_FOR_NATIONAL_EXPLICIT_USE; NUMERIC_INPUTS_PENDING',FullSC_Blocker='SHARED_SYSTEM_GATES_ONLY',Reason=notes[(c,s)],ThermalDetailBlocker='NO_UNIVERSAL_E3_REQUIREMENT',SharedGateIDs='M01;M02;M03;M04;M05;M06;M15',ExplicitThermalEligibility='NOT_ESTABLISHED',ThermalPromotionStatus='PENDING_LOCAL_EVIDENCE_IF_MATERIAL',BoundaryDecisionStatus='PROPOSED_ACCOUNT_MAP_UNDER_HUMAN_FROZEN_RULES',NumericDataAcceptance='PENDING_UNCHANGED',NumericInputWritten='NO',ParentContainment='R/S contained in reconciled A*; never add parent plus children',Evidence=refs+'; '+('Phase3A6 Malaysia ledger/prototype/year bridge' if c=='MY' else 'Phase3A5 space/water mapping'),CountrySpecificSystemConcern='R/S classification family and Commercial crosswalk' if c=='MY' else ('ASEAN10 versus11/TL total scope' if c=='TL' else 'shared final-account reconciliation'),Sensitivity='omitted thermal electrification/flexibility and unequal evidence coverage; effect not quantified'))
(D/'BUILDINGS_FIRST_FULLSC_BOUNDARY.json').write_text(json.dumps(boundary,ensure_ascii=False,indent=2),encoding='utf8')
specs=[
 ('M01','共同最终电力父账户与地域/年份','SYSTEM_ACCOUNTING','YES_BEFORE_NUMERIC_ASSEMBLY','A*若仍是发电/供电侧或ASEAN10量分给11国，会改变总需求、容量与国家投资。','total cost; capacity; country investment','P6 AEO/source trace; HUMAN Phase3A7 §1','冻结概念已完成；国家A*数值、年/域/计量证据仍PENDING。','在研究层证明final-meter国家向量和TL范围；不可用热用途缺口回填。','meter/地域数值仍不一致，或试图将generation直接当Load。'),
 ('M02','未来直接用电与内生转换重叠','SYSTEM_ACCOUNTING','YES_BEFORE_NUMERIC_ASSEMBLY','综合未来电量若已含同一用途，又加转换输入，会系统性重复需求。','sector electrification; capacity; cost; flows','P6 scope matrix/source trace; HUMAN §1','AEO generation仅paper comparator，TFEC仅一致性benchmark；不数值替换。','为每个待显式部门规定父账户扣除/保留及未来service/direct演化。','相同服务在固定Load和内生转换输入同时存在。'),
 ('M03','R/S、其他电力和直接燃料互斥保留','SYSTEM_ACCOUNTING','YES_BEFORE_NUMERIC_ASSEMBLY','父子重复、R覆盖原综合AC后丢O、燃料丢失/重复或R/S错分会改成本和空间投资。','cost; country investment; flows','P4 E3 specification; P6 MY2019 Table17/Table29 conflict','R/S分开；每个燃料一次；未知用途留unclassified；未接受数值家族。','接受同域R/S划分、非Buildings O及燃料单位/供给/成本映射，验证能量各记一次。','选择冲突表、删除未分类能耗，或按部门拆分改变了国家父总量。'),
 ('M04','共同时间/空间分配和物理年量权重','SYSTEM_ACCOUNTING','YES_BEFORE_NUMERIC_ASSEMBLY','不一致的时间权重或分配可在年总量相同下改变峰值、网流和投资。','flows; capacity; country investment','P4 accounting contract; P6 growth weighting observation','保留已接受物理权重契约；不要求每个embedded热用途先有独立小时曲线。','核对R+S+O与父曲线/年量的共同覆盖及不重复分配；有效base形状仍需接受。','年量或节点时刻对不上；先有年度显式服务却无可解释形状。'),
 ('M05','0.97及网络损耗边界','SYSTEM_ACCOUNTING','YES_BEFORE_NUMERIC_ASSEMBLY','预含与物理损耗重复或未经证据缩减Load改变供用平衡与网流。','cost; flows; capacity','P6 loss audit; HUMAN §2','0.97 NOT SCIENTIFICALLY ACCEPTED；不patch。','后续研究层实现应与final-meter边界一致并记录显式/省略的loss；本轮不指定替代数。','旧0.97未经解释继承，或同一网络段损耗计两次。'),
 ('M06','嵌入用途与默认显式heat重复建模','INTEGRATION_GATE','YES_BEFORE_NUMERIC_ASSEMBLY','把能量保留direct却照搬默认热服务生成器，会将嵌入与显式服务同时建入网络。','cost; sector electrification; capacity','P4 heat constructor trace; HUMAN §3-6','本轮22个R/S行无已达标国家显式热账户；boundary CSV不是可执行override。','将来组装按账户选择热构造路径并验证没有synthetic/default服务偷偷进入；不做universal E3。','默认space/water、DH或虚构stock被自动生成。'),
 ('M07','全11国设备型号/η/COP细节','THERMAL_PROMOTION_DETAIL','NO_FOR_EMBEDDED_BASELINE','当前未转换成useful service时这些参数不进入优化；晋升显式账户后才影响用电和技术选择。','conditional sector electrification; cost','P5 140 candidates lack accepted performance; HUMAN §3F','保留原能耗；不找齐所有设备，不借未来DEA。','只对确需显式且具实质影响路径的账户收集足够性能证据。','决定增加该热转换账户，且输出/输入边界依赖缺失性能。'),
 ('M08','全国完整space/water拆分及细小用途','THERMAL_PROMOTION_DETAIL','NO_UNIVERSAL_DATA_BLOCKER','能耗父账户保留时，未知拆分本身不会再增删能量；省略响应的效果尚未证明可忽略。','conditional capacity; flows; electrification','P5 country map; HUMAN §3B-E','EMBEDDED；UNKNOWN不写零，不造共同60/40。','仅登记限制；若有针对某国/用途的可信大系统影响证据，再局部升级审查。','出现地区性热量或电气化变化证据，足以影响研究比较。'),
 ('M09','Malaysia2016用途小差额与年份桥细节','PROTOTYPE_REFINEMENT','NO_WHILE_PROTOTYPE_NOT_USED','未把半岛2016表投入全国基准时，0.43GWh等原型差异不流入模型。','conditional source accounting','P6 source ledger/closure/year bridge','保留方法原型和所有差额；不扩全国、不移用其他国家。','只在计划晋升MY显式服务时解决表内差、2016→目标年、半岛→全国。','使用MY用途值/份额形成国家热服务；MY R/S父账户分区冲突仍归M03。'),
 ('M10','用途专属热负荷小时曲线/建筑楼面细分','THERMAL_PROMOTION_DETAIL','NO_FOR_EMBEDDED_USES','未单独建热服务时无需先生成其热形状；若以后显式，时序/空间可能影响灵活性和网流。','conditional flows; storage; investment','P4 useful-heat method; HUMAN §3F','BDEW仅reference；不合成11国water小时曲线。','显式账户先年度闭合，再按需要核对非负转移和服务分配。','新增可转移/可储热服务，而形状影响跨境峰时或地区投资。'),
 ('M11','DH和历史brownfield热设备存量','EXCLUDED_FEATURE','NO_FOR_DECLARED_FIRST_BASELINE','没有被引入的资产明细不控制本基准；以后引入会改变约束与投资成本。','conditional country investment; cost','HUMAN §4; P4 method','DH不自动开；不伪造ASEAN存量；未建库存不表示真实库存为零。','记录未表示既有热资产约束/沉没成本，不用欧洲库存填充。','研究问题需要热网或既有存量的约束与投资归属。'),
 ('M12','cooking细分和未分类直接燃料','RETAINED_ENDUSE','NO_FOR_ENDUSE_SPLIT_ONLY','只要原燃料与电力各保留一次，未细分cooking无需独立热服务；总燃料丢失则M03阻断。','conditional cost; electrification','P4 cooking contract; HUMAN §4','NON-EXPLICIT + ACCOUNTING REQUIRED；unclassified保留。','无需新cooking模块；核对direct fuel与system cost边界。','父燃料账户缺失，或将cooking转入space/water demand。'),
 ('M13','cooling需求响应和内生灵活性','HUMAN_SCOPE_LIMIT','NO_FOR_DECLARED_FIRST_BASELINE','制冷灵活性可能改变峰值、储能和互联价值；用户明确首基准固定嵌入，影响未量化。','flows; capacity; cost','HUMAN §4; P6 cooling scope','保留制冷电量，不添加第二份Load；首基准不建内生cooling flexibility。','作为后续敏感性候选，不把固定负荷结果推广成完整Buildings灵活性结果。','研究结论依赖峰时可转移负荷，或新证据显示比较对cooling敏感。'),
 ('M14','未表示Buildings热电气化/灵活性的比较限制','RESEARCH_INTERPRETATION','NO_FOR_DECLARED_ASSEMBLY; CONDITIONAL_FOR_GENERAL_CLAIMS','保留历史direct能耗不能揭示所有替代HP/阻热/储热方案，因此可能遗漏互联收益通道。','electrification; country investment; flows; cost','HUMAN minimum baseline; analytical scope implication','这是受约束的首基准，不是已证明热需求无关或互联收益数学下界。','允许按明确范围前进；保持限制。出现具体证据时按country/sector局部升级，而非追求通用完美数据。','要声称全面Buildings转型收益，或有具体国家/用途证据提示关键结果会改变。'),
 ('M15','Integrated与Disconnected的对称边界','COMPARISON_GATE','YES_BEFORE_COMPARATIVE_EXPERIMENT','两情景若使用不同嵌入/显式掩码、需求或非网络假设，差额不能归因于互联。','integrated-disconnected comparison; cost; investment','HUMAN research objective; P4 accounting contract','相同国家需求/部门表示和转换边界；只允许未来明确定义的连接差异。','以后实验设计记录共同表示矩阵和输入身份；本轮不建正式情景。','只在一侧改变热电气化、损耗、父账户或部门开关。')]
register=[]
for id,item,category,blocker,pathway,outcomes,evidence_text,action,minimum,trigger in specs:
 register.append(dict(ItemID=id,Item=item,Category=category,FullSC_Blocker=blocker,CredibleMaterialityPathway=pathway,AffectedResearchOutcomes=outcomes,Evidence=evidence_text,CurrentDisposition=action,MinimumClosureOrContainment=minimum,ReopenTrigger=trigger,QuantifiedMateriality='',NumericThreshold='',MaterialityAssessment='QUALITATIVE_RESEARCH_JUDGMENT_NO_SOLVE',DataAcceptance='NO_NEW_NUMERIC_ACCEPTANCE',DecisionStatus='PROPOSED_TRIAGE_FOR_REVIEW'))
(D/'BUILDINGS_MATERIALITY_REGISTER.json').write_text(json.dumps(register,ensure_ascii=False,indent=2),encoding='utf8')
counts=dict(country_sector_rows=len(boundary),countries=11,sectors=2,thermal_account_cells=44,explicit_thermal_accounts=0,embedded_thermal_accounts=44,cooling_embedded_rows=22,cooking_accounted_rows=22,materiality_items=len(register),new_numeric_model_inputs=0,solver_runs=0)
(E/'PROPOSAL_COUNTS.json').write_text(json.dumps(counts,indent=2),encoding='utf8')
print(json.dumps(counts,indent=2))
