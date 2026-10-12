"""Write only C06 evidence-grounded closeout documents and ledgers.
No launch, network, solver or production result mutation.
"""
from pathlib import Path
import json,hashlib,shutil,collections,subprocess,datetime
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c06_barconvtol_20261012');N=W/'analysis_view'
ROOT=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');O=ROOT/'research/05_baseline_evolution/20261011/c06';E=O/'evidence'
B=Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run')
F=Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/c05_daily_diagnostic/c05_aggregate0_daily122_20261012T074925Z_a39647d9/cloud_run')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def cp(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
def table(h,rows):return '| '+' | '.join(h)+' |\n|'+'|'.join(['---']*len(h))+'|\n'+'\n'.join('| '+' | '.join(str(v) for v in r)+' |' for r in rows)
def redact(s):return '\n'.join('[REDACTED: license registration metadata; numerical log unchanged]' if 'Academic license ' in line else line for line in s.split('\n'))
assert subprocess.check_output(['git','-C',str(ROOT),'branch','--show-current']).decode().strip()=='codex/c06-barconvtol-daily-20261012'
C=read(W/'C03_C05_C06_METRIC_COMPARISON.json');A=read(W/'C06_ALL_ACCOUNT_AND_GROUP_COMPARISON.json');K=read(W/'C06_KKT_FAILURE_SET_COMPARISON.json');M=read(W/'C06_MATRIX_ROW_FAMILY_COMPARISON.json');X=read(W/'C06_EXACT_LOCAL_FORENSICS.json');G=read(W/'C06_GROUP_PATTERN_AND_FREE_RC.json');BS=read(W/'C06_FINAL_BACKUP_STATUS.json');RS=read(W/'C06_RESOURCE_AND_DEADLINE_SUMMARY.json');logs=read(W/'C06_LOG_TRAJECTORY_COMPARISON.json');RID=C['run_id'];V=C['C06_daily_V4']
oldclass=read(Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c04_daily_pattern_20261012/C04_KKT_COLUMN_CLASSIFICATION.json'))
def assetkey(r):return r['family']+':'+str(r['coordinates'][r['family'].split('-')[0]])
oldassets={assetkey(r) for r in oldclass['failed_columns']};newassets={assetkey(r) for r in K['failed_columns']}
C['stationarity_asset_sets']={'C03_count':len(oldassets),'C06_count':len(newassets),'new':sorted(newassets-oldassets),'resolved':sorted(oldassets-newassets),'retained':sorted(oldassets&newassets)}
C['account_subcheck_fail_counts']={k:dict(collections.Counter(q for a in A['accounts'] for q,v in a[k]['checks'].items() if not v)) for k in ('C03','C06')}
C['account_extrema']={k:{
 'maximum_annual_positive_excess':max(({'asset':a['asset'],'excess_MWh':a[k]['metrics']['annual_overuse_MWh'],'budget_MWh':a[k]['budget_MWh'],'excess_over_own_budget':a[k]['metrics']['annual_overuse_MWh']/a[k]['budget_MWh']} for a in A['accounts']),key=lambda x:x['excess_MWh']),
 'maximum_annual_absolute_error_over_budget':max(({'asset':a['asset'],'signed_error_MWh':a[k]['metrics']['annual_signed_error_MWh'],'budget_MWh':a[k]['budget_MWh'],'ratio':a[k]['error_over_own_budget']['annual_abs_error_MWh']} for a in A['accounts']),key=lambda x:x['ratio']),
 'minimum_stock_MWh':min(a[k]['metrics']['minimum_stock_MWh'] for a in A['accounts']),
 'maximum_prefix_residual_MWh':max(a[k]['metrics']['prefix_max_MWh'] for a in A['accounts']),
 'maximum_state_residual_L1_MWh':max(a[k]['metrics']['state_residual_L1_MWh'] for a in A['accounts'])} for k in ('C03','C06')}
assert V['status']=='OPTIMAL_BUT_NOT_ACCEPTED' and len(K['failed_columns'])==3336
# Every conclusion names its provenance and limitations; backup qualification is independent.
prov=[];bulk=[];known={v['relative']:v for v in read(W/'C06_PARTIAL_EVIDENCE_RECOVERY.json')['member_records']}
for p in sorted(N.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(N).as_posix()
 if p.suffix not in ('.json','.jsonl','.log') or p.stat().st_size>=4_000_000:
  bulk.append({'relative':rel,'local_analysis_path':str(p),'bytes':p.stat().st_size,'sha256':known[rel]['sha256'] if rel in known else sha(p),'origin':'COMPLETE_MEMBER_FROM_PARTIAL_ARCHIVE' if rel in known else 'COORDINATE_INVERSE_MATCHES_NATIVE_SHA','published':False});continue
 q=E/'current_run'/rel
 if q.suffix=='.log':q=q.with_name(q.stem+'.redacted.log')
 q.parent.mkdir(parents=True,exist_ok=True);data=p.read_bytes();public=redact(data.decode('utf-8')).encode('utf-8');q.write_bytes(public)
 prov.append({'source_relative':rel,'source_sha256':hashlib.sha256(data).hexdigest(),'source_bytes':len(data),'published_relative':q.relative_to(O).as_posix(),'published_sha256':sha(q),'redaction':None if public==data else 'Academic license registration metadata only','source':'archive complete member' if rel in known else 'monitor receipt reserialization with original SHA match'})
for run,p in [('C03',B),('C05',F)]:
 for rel in ['raw/vectors/RAW_RECEIPT.json','EFFECTIVE_MODEL_PARAMETERS.json','NATIVE_CALL_EXIT.json','NATIVE_TRANSFER.json']:
  cp(p/rel,E/('baseline_'+run)/rel)
 for name in ('KKT.json','POSTPROCESS_RECEIPT.json','DUAL_COST_LEDGER.json'):
  if (p/'postprocess'/name).exists():cp(p/'postprocess'/name,E/('baseline_'+run)/name)
 q=E/('baseline_'+run)/'gurobi.redacted.log';q.write_text(redact((p/'gurobi.log').read_text(encoding='utf-8')),encoding='utf-8')
 prov.append({'source_relative':str(p/'gurobi.log'),'source_bytes':(p/'gurobi.log').stat().st_size,'source_sha256':sha(p/'gurobi.log'),'published_relative':q.relative_to(O).as_posix(),'published_sha256':sha(q),'redaction':'Academic license registration metadata only'})
evidence_names=['C06_ARCHIVE_SOURCE_IDENTITY.json','C06_PARTIAL_EVIDENCE_RECOVERY.json','C06_ANALYSIS_PROVENANCE.json','C06_RESUME_LOCAL_SYNC_PENDING.json','C06_TRANSFER_WINDOW.json','C06_TRANSFER_BACKEND_HANDOFF.json','C06_RESUME_PREFIX_VERIFICATION.json','C06_SINGLE_RESUME_CONSUMED.json','LOCAL_SYNC_PENDING.json','DEPLOYMENT_RECEIPT.json','LAUNCH_RECEIPT.json','C06_ALL_ACCOUNT_AND_GROUP_COMPARISON.json','C06_KKT_FAILURE_SET_COMPARISON.json','C06_MATRIX_ROW_FAMILY_COMPARISON.json','C06_COMPARISON_METHOD_RECEIPT.json','C06_EXACT_LOCAL_FORENSICS.json','C06_GROUP_PATTERN_AND_FREE_RC.json','C06_LOG_TRAJECTORY_COMPARISON.json','C06_RESOURCE_AND_DEADLINE_SUMMARY.json','C06_C03_C05_RESOURCE_COMPARISON.json']
for name in evidence_names:cp(W/name,E/name)
snap=read(W/'monitor_snapshots/20261012T100539Z.json');assert all(not v['live'] for v in snap['live_identities'].values())
snap=json.loads(redact(json.dumps(snap,ensure_ascii=False)))
dump(E/'C06_TERMINAL_OBSERVATION.json',snap)
dump(E/'C06_PUBLIC_EVIDENCE_PROVENANCE.json',{'files':prov,'bulk_excluded':bulk,'originals_unchanged':True,'archive_backup_complete':False,'integrity_scope':'partial archive CRC unavailable; mapped/native vector SHA chain and monitor receipts independently crosschecked'})
dump(O/'C03_C05_C06_METRIC_COMPARISON.json',C);dump(O/'C06_COMPLETE_V4_AND_BASELINE_COMPARISON.json',C);cp(W/'C06_FINAL_BACKUP_STATUS.json',O/'C06_FINAL_BACKUP_STATUS.json');cp(N/'C06_C03_C05_PARAMETER_COMPARISON.json',O/'C06_C03_C05_PARAMETER_COMPARISON.json')
methods=['salvage_received_evidence.py','authenticate_partial_analysis.py','compare_saved_results.py','local_exact_forensics.py','compute_receipt_metrics.py','publish_comparative.py']
for name in methods:cp(W/name,O/'methods'/name)
gate_table=table(['日V4门槛','C03','C06'],[(k,'PASS' if C['C03_daily_V4']['gates'][k] else 'FAIL','PASS' if v else 'FAIL') for k,v in V['gates'].items()])
native_table=table(['项目','C03','C05','C06'],[(key,*(C['native'][r]['native_info'].get(key,'NOT_AVAILABLE') for r in ('C03','C05','C06'))) for key in ('SolCount','BarIterCount','Runtime','ConstrVio','DualVio','ComplVio')]+[('Status',2,'12 NUMERIC',2)])
result=f'''# C06 BarConvTol 日诊断最终交付

**C06_EXECUTION_ACCEPTED_SCIENCE_NOT_ACCEPTED。** C06原生求解完成，日V4未通过；云端已封存，本地完整归档仍为 **LOCAL_SYNC_PENDING**。本轮仅整理已有证据，没有新的优化、模型构建或远端操作。

## 真实运行与对照身份

Run：`{RID}`。生产提交`34a34b69ef752d7809487ca609cd91e12f75bffd`。GRBoptimize返回码0，优化调用1次；Status=2 OPTIMAL、SolCount=1、Barrier143次、Runtime282.17975401878357秒。NATIVE_CALL_EXIT、NATIVE_RETURN、RAW_RECEIPT、原生日志及POSTPROCESS均对应同一run和模型Manifest；未把OPTIMAL作为科学PASS。

{native_table}

C03为主对照，C05为Aggregate=0的NUMERIC分支。154项实际数值参数重新逐项比较：C06相对C03仅BarConvTol从1e-6到1e-9；相对C05有Aggregate 0→1和BarConvTol变化。Aggregate=1，Crossover=0，NumericFocus=0，FeasibilityTol/OptimalityTol=1e-6；TimeLimit3600、SoftMemLimit65十进制GB、MemLimit1e100。完整差异表见`C06_C03_C05_PARAMETER_COMPARISON.json`和主比较JSON。

三次同一日数学模型：2,450,005列、6,042,238行、11,403,496非零元。冻结日CSC、边界、D/R、标签、目标、Scheme A、C01R和日V4绑定均复用。模型Manifest SHA `{C['native']['C06']['model_manifest_sha256']}`；日cost SHA `c9a9717c664e2b3d5d4ca9b56848097f5231823465516113a13e00cb8f632d83`；日V4 SHA `8c48d0735e6dcde870fdff589915aba57b55870994e75bc04b76d39e41c38459`，父V4 `955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f`。

C06生产核验17,369项输入SHA，EXACT_READBACK_PASS用时3.736114秒，原生模型句柄在交接与唯一调用中一致；本轮又核对9项核心文件SHA。没有重建、CSR→CSC转换、P2或warm start。最终C06 BACKUP_INDEX文件尚未收到，因此完整封存引用列表的本地独立核验仍待办，不能用这9项检查替代。

## 保护、RAW与完整日V4

生产t0为{RS['start_utc']}，固定总截止2026-10-12T11:57:05.802316Z；全流程至封存guard退出406.461504秒。监督回执无保护触发、无OOM。进程树RSS采样峰值{RS['sampled_worker_tree_peak_rss_bytes']/2**30:.6f}GiB；cgroup共享/生命周期峰值{RS['cgroup_lifetime_peak_start_bytes']/2**30:.6f}→{RS['cgroup_lifetime_peak_end_bytes']/2**30:.6f}GiB；最小余量{RS['minimum_cgroup_headroom_bytes']/2**30:.6f}GiB，磁盘最小{RS['minimum_disk_free_bytes']/2**30:.6f}GiB。RSS并非连续峰值，cgroup峰值并非库独占峰值。末次10:05:32Z观察确认worker/supervisor/guard均退出；本轮未重新连接实例，未操作电源。

RAW先持久化X/Pi/RC，分别2,450,005 / 6,042,238 / 2,450,005个float64，再验收。三个原生SHA及原单位SHA见`evidence/C06_ANALYSIS_PROVENANCE.json`。本地从已接收完整成员恢复原单位向量，独立逆映射所得NPY三个SHA均与云端RAW回执相同；这证明分析使用同一返回点，不是修补解，也不是完整归档传输完成。

{gate_table}

日模型仍有243条Store库存下界矩阵行、85个资源账户、3336个stationarity列失败。385组义务全部通过；没有将输入表示预算从求解残差扣除。NetCDF逐值回读和FOM一次计量通过，不代替物理/KKT门槛。

原科学已知成本{V['costs']['original_scientific_objective_known_scope']:.9f} EUR；V3复算{V['costs']['adapted_objective']:.9f} EUR；微扰贡献{V['costs']['numerical_perturbation_contribution']:.9f} EUR；组分复算误差{V['costs']['reconciliation_residual']:.12g} EUR。ObjCon={C['objective_constant_EUR']} EUR。独立V3复算减原生ObjVal={C['native_ObjVal_vs_independent_V3_EUR']:.12g} EUR。均为未合格候选的核算值；NULL未填造，FullSystemCostComplete=false，原未扰动目标最优性NOT_PROVEN。

## 封存、传输与明确缺口

云端封存回执：53项新文件、457,423,943字节，BACKUP_INDEX SHA `{BS['cloud_seal_index_SHA']}`。归档153,715,959字节，SHA `fcfb61920d094aec9cf84b755a25d5b589097d4842656fbc863b5e901cb56c07`。

原60分钟传输窗已结束，连接错误为`Connection reset`。两段现有接收数据共140,640,256字节，仍缺13,075,703字节。保留全部partial、旧窗口和失败回执；本轮没有重开窗口或续传。完整gzip CRC、全归档SHA和53项BACKUP_INDEX逐文件验证 **尚未完成**。云端原件及消费标记不变。

本地分析目录：`D:\\ResearchWorkspaces\\ASEAN\\work\\c06_barconvtol_20261012\\analysis_view`；原partial恢复目录：同目录下`recovered_partial_evidence`。云端Run：`/root/autodl-tmp/SGP/runs/{RID}`。完整归档位置及最小补齐方案见`C06_FINAL_BACKUP_STATUS.json`。只有获得新的明确传输授权后才能补齐；无需也不得重新求解。

## 交付与停止

比较结论见`C03_C05_C06_COMPARATIVE_FORENSICS.md`；全部计量见同名前缀JSON。当前仍为C阶段365日日诊断，未进入D阶段2920时段Gate6。G6-05持续PAUSED_BY_USER；不启动下一实验。此次结果分支`codex/c06-barconvtol-daily-20261012`，关联PR #13/#14/#15，实际提交和PR见ZIP的GIT_PUBLICATION。实例最后已知保持运行及计费，本轮不声称进行了新的在线状态核验。
'''
(O/'C06_BARCONVTOL_DAILY_DIAGNOSTIC_RESULT.md').write_text(result,encoding='utf-8')
def val(k,r):return C['all_metric_comparison'][k][r]
rows=[('矩阵失败行',val('row_fail_count','C03'),val('row_fail_count','C06'),'改善'),('矩阵最大违约 MWh',val('row_violation_max','C03'),val('row_violation_max','C06'),'改善'),('资源失败账户/807',377,85,'改善；保留85，无新增'),('义务失败组/385',111,0,'改善；组级通过'),('年度正向资源超用 MWh',A['totals']['C03']['annual_positive_resource_excess_MWh'],A['totals']['C06']['annual_positive_resource_excess_MWh'],'改善，不能与少用抵消'),('组级正向超供 MWh',A['totals']['C03']['gross_positive_group_oversupply_MWh'],A['totals']['C06']['gross_positive_group_oversupply_MWh'],'改善'),('组级反向欠供 MWh',0,A['totals']['C06']['gross_negative_group_undersupply_MWh'],'新增非零，但各组在原预算内'),('Bus最大残差 MW',8.320791,7.313872265513055e-5,'改善；C03值此表简写，源JSON保留完整精度')]
for key,label in [('stationarity_fail_count','stationarity失败列'),('stationarity_normalized_max','最大归一化stationarity'),('stationarity_max_original','最大原单位stationarity'),('dual_sign_fail_count','对偶符号/自由RC失败'),('complementarity_l1','互补性L1 EUR'),('complementarity_max','最大局部互补项 EUR'),('stationarity_weighted_l1','加权stationarity L1 EUR'),('absolute_gap','原对偶绝对目标差 EUR'),('relative_gap','相对目标差')]:rows.append((label,val(key,'C03'),val(key,'C06'),C['all_metric_comparison'][key]['direction']))
card=table(['每组账户数','组数/账户数','C03失败组/账户','C06失败组/账户'],[(r['account_count'],f"{r['groups']}/{r['accounts']}",f"{r['C03']['failed']}/{r['C03']['failed_accounts']}",f"{r['C06']['failed']}/{r['C06']['failed_accounts']}") for r in A['cardinality']])
worst=C['account_extrema']['C06']['maximum_annual_positive_excess'];ratiow=C['account_extrema']['C06']['maximum_annual_absolute_error_over_budget']
forensic=f'''# C03 / C05 / C06 comparative forensics

**结论：BarConvTol收紧改善了大部分原单位物理残差和互补性，但没有使全部局部可行性/KKT成立。** C03和C06均是求解器容差意义的OPTIMAL、原V4 NOT_ACCEPTED。本轮没有新的求解。

证据等级：VERIFIED=原始回执/保存向量或独立计算；DERIVED=明示数学恒等式；INFERENCE=机制解释；PROPOSED=未执行方案。冻结身份、资源和备份资格见C06结果报告及主比较JSON。本地完整备份未完成，不隐藏该限制；科学比较所需三向量已通过独立SHA恢复和同点核验。

## 1. 严格对照、轨迹与资源

VERIFIED：三次同一科学问题与日数值表达。C03 Aggregate1/BarConvTol1e-6；C05 Aggregate0/1e-6；C06 Aggregate1/1e-9。154项参数相对C03仅BarConvTol变化，相对C05有两项变化；数学文件SHA并非只靠日志Model fingerprint。

{table(['项目','C03','C05','C06'],[(key,*(logs['logs'][r][key] for r in ('C03','C05','C06'))) for key in ('presolve_seconds','presolved','ordering_seconds','free_variables','dense_columns')]+[('Barrier / Runtime秒','69 / 155.370943','24 / 81.595145','143 / 282.179754')])}

C03与C06的0—69共70条打印迭代数值相同；这是实际日志逐项比较结果，不能证明内部状态逐位相同。C06后续至143次。C03末次打印 primal/dual residual=2.45e-5/2.41e-3、complementarity=.137；C06为1.92e-6/4.04e-3、7.53e-7。打印量经过预处理/舍入，不能直接当作原单位MW/MWh。双侧残差并未同步单调下降。

{table(['原生调用区间采样','C03','C05','C06'],[(key,*(f"{C['resources'][r][key]:.6f}" for r in ('C03','C05','C06'))) for key in ('native_sampled_worker_tree_RSS_peak_GiB','native_cgroup_current_sample_peak_GiB','native_average_CPU_cores')])}

CPU核数由真实调用区间的CPU时间差/墙钟差估算，完整区间、样本数和限制在资源JSON。未将C03构建期峰值与C06纯求解期混比。三次没有证据显示资源保护造成上述数值终态。

C05 Status12 NUMERIC、SolCount0：原始向量及物理/KKT/成本对照全部NOT_AVAILABLE，不能填0。Aggregate0改变了presolve规模和后续数值路径并失败；这否定“关闭聚合在本例一定更稳”的预期，不证明聚合1导致资源违规，也不证明模型不可行。

## 2. 同单位、同预算下的完整比较

{table(['指标','C03','C06','判读'],rows)}

一般行预算仍为0.001+1e-7×reference；账户B_i=min(0.001+1e-7Q_i,1e-6Q_i) MWh。账户比值只除以该账户自身B_i；组比值只除以原组预算。没有用总量或输入表示误差稀释局部违约。全部807/385均覆盖，包括旧通过资产。C05无合法点，以上表不列伪残差。

C06矩阵243条失败均为Store-fix-e-lower：旧失败消失48,055、保留243、新增0；变量列界均无失败。Store库存下界在本LP中是矩阵行，故“列界0失败”不表示库存下界通过。

85个失败账户中：年度/终态各85项失败，库存下界/累计资源上限各62项失败；逐期动态、全部前缀恒等式、状态L1及meter对应关系均通过原检查。其余23项包含资源未用尽/终期正库存；不能将85全部称为超用账户，也不能把动态方程成立当作库存界成立。

最大年度正向超用账户`{worst['asset']}`：{worst['excess_MWh']:.12g} MWh，自身预算{worst['budget_MWh']:.12g} MWh，比值{worst['excess_over_own_budget']:.9g}。最大绝对年度误差/预算反而来自`{ratiow['asset']}`，少用{abs(ratiow['signed_error_MWh']):.12g} MWh、预算{ratiow['budget_MWh']:.12g}，比值{ratiow['ratio']:.9g}。极小账户不能用组总需求相对误差代替其预算。

所有账户的最小库存、终态、前缀最大、累计状态L1、meter和各预算倍数在逐账户JSON；两个全量极值表在主比较JSON。最小库存C03 −18298.4059834→C06 −54.8319548505 MWh，仍不能通过。

## 3. 1/2/3/4账户模式与组内抵消

{card}

VERIFIED：C06失败仍只出现在原3/4账户组的子集，49个组含失败账户，但这些组的总交付均在组预算内。旧111个“组必失败”离散模式已消失，不得描述为完全不变。国家/部门/D和年度规模分层见`C06_GROUP_PATTERN_AND_FREE_RC.json`；这些共同变化因素没有随机化或独立干预，因此账户数因果效应仍NOT_PROVEN。

明确例子：`MM:2050:Buildings:ResidentialFuel:biomass@MM2 1 :: final obligation`。C06商品账户正向超用54.8319548507 MWh、其他商品少用54.7832753494 MWh；净差只有0.0486795013 MWh。组级通过是对总交付的检验，不能掩盖商品库存与年度义务失败。组内抵消是直接算术事实，不是新的免费资源或新增路径；也未通过修改解消除它。

## 4. 独立精确局部核算与机制边界

本輪使用冻结日CSR的163条选定完整行支撑及CSC的5个完整列支撑，以Fraction(binary64)精确点积计算；对159个NetCDF显式值与原单位X逐值交叉核对。少数选中StorageUnit列在NetCDF表中未单独存储，标明未做直接标量回读，未以此替代原生产18表语义回读。完整失败集合另外仅作一次日CSC stationarity遍历；未读取旧全年矩阵。

DERIVED并逐项验证：A_s=R A D，x=Dz，pi_original=R pi_s，rc_original=rc_s/D。故r_original=r_solver/R；stationarity_original=(c_s−A_sᵀpi_s−rc_s)/D。选定行/列用两条独立路径计算，精确有理数相等；没有发现所选样本的映射、符号或回读错误。该结论不外推为所有代码都不存在bug。

VERIFIED：实际行3357088（Store-fix-e-lower），R=2^-24=5.960464477539063e-8；原单位负库存54.83195485051556 MWh，缩放残差3.268239191205237e-6。行3258844的R=2^-28，原单位0.164924271274 MWh对应6.14390787757e-10。后者远小于常用1e-6输入坐标量级却超过原单位V4库存门槛。这严格证明残差尺度放大关系，**没有证明缩放是生成该返回点的唯一原因**。前者甚至大于1e-6，不能笼统解释为“所有输入残差都在FeasibilityTol以内”。原生ConstrVio=4.999788120237309e-6也明确保留。

VERIFIED：列318846，Line 2，2013-01-05，D=1，两个线路容量行和两个Bus行的R均为1。精确归一化stationarity从1.26203364056e-5变为2.75736254804e-5，恶化；列1407794，Link `1076672675-1_0+4`，2013-11-10，D/R也为1，归一化残差1.85041654686e-6→1.95404250854e-6。这些局部dual失败不能用资源库存R放大直接解释。它们在代数位置上不同，但共同最优性系统、presolve和对偶解相互耦合，统计或因果独立仍未证明。

旧Line52自由RC样本列356365：RC_original从3.80294343319e-5变为1.95831431490e-11；全部365项旧符号失败均消失。当前stationarity中3012条Line-s、324条Link-p；旧4304项消失1013、保留3291、新增45。新增列不等同于新增物理资产；资产集合精确差异见主JSON（新增资产数{len(newassets-oldassets)}）。不能只报总数下降而隐去新增失败。

## 5. 为什么OPTIMAL仍未通过V4

Gurobi Barrier停止条件综合相对原/对偶目标差、相对原/对偶可行性和互补性，并不是逐个MWh账户预算或本项目局部归一化stationarity的同义词。[Gurobi参数定义](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#parameterbarconvtol)。本报告仅用此官方定义解释指标，不将当前文档默认值代替实际12.0.3的154项回执。数值容差对单位/缩放敏感；官方也明确容差与严格精确可行性不同。[Gurobi 12.0数值说明](https://docs.gurobi.com/projects/optimizer/en/12.0/concepts/numericguide/tolerances_scaling.html)。

本例的直接结论不是“OPTIMAL记录错误”，而是同一返回点满足库的停止判据却未满足获批V4的所有局部门槛。V4目标归一化Z=max(1,|primal|,|dual|)包含固定offset；C06相对差2.74988682909e-7虽小于1e-6，绝对差117699.0634765625 EUR仍比C03的84271.25708007812 EUR大。双目标由未完全可行的primal/dual候选构造，不应宣传成严谨的上下界最优性证书。

互补L1从189887.484984大幅降至29.5324601821 EUR；加权stationarity L1从101694.676552升至120113.441519 EUR。两者除Z后均在1e-6内，但局部stationarity仍超限。FOM一次计量/目标复算/NetCDF回读可通过，同时物理与KKT失败；这些验收门槛是合取关系。

INFERENCE：资源原单位预算与输入坐标精度不匹配、组内资源分配退化及postsolve误差传播都值得诊断。但本轮没有估计条件数、保存Gurobi内部消元过程或单独改变坐标，不能区分这些候选机制的因果贡献；不得据此认定Gurobi/PyPSA代码Bug。旧精确源常数问题已经由Scheme A源级修订，本轮不将历史10.24TWh或全年INF_OR_UNBD作为这次日返回点的因果证明。

## 6. 唯一下一步建议（PROPOSED，未执行）

**建议转向一次“预算匹配的数学等价坐标表达”日模型对照，以C06为基准；不再优先单纯收紧BarConvTol。** 只改变一份明确冻结的正对角D/R数值表达，α=1，科学目标、offset、科学矩阵、Scheme A/C01R/V4及全部C06算法参数保持；它是一个数值表达因素，不冒称只修改一个Gurobi参数，也不直接套用曾失败的全年P2。

实施前仅需针对本轮已定位的资源行/账户预算及Line/Link完整列支撑核定一个候选：计算预算映射到输入坐标后的尺度、系数/边界范围和L1累计预算；验证精确等价、正对角恢复及无溢出/截断，保留D/R=1的Line/Link失败作为不同机制的观测对象。若不存在安全的单一候选，应停止并报告该具体阻碍，不开展参数网格。这一步必须避免以缩放隐藏原单位V4违规。

依据：BarConvTol这一已执行干预使物理残差大幅改善却留下库存和局部dual失败；实测R放大关系明确，且Line/Link存在无该放大效应的剩余错误。新的等价表达干预比再试1e-10/1e-12更能检验“坐标选择是否影响独立V4结果”。仍不能证明唯一根因，也不保证新的表达更稳或通过；仅资源问题改善而电网KKT保留同样是有价值的反证/分离信息。

新增计算建议仅一个候选的本地静态坐标核验，随后若用户批准才进行一次同日LP原生载入、精确回读及一次优化；沿用现有90GiB、Threads4、SoftMemLimit65GB、RSS75GiB/余量12GiB/盘8GiB保护，建议原生≤3600秒、总≤7200秒，不根据本次282秒保证未来时长。静态核验可按分钟级、数GiB工作集作预算估计（未执行测量）；新因子分解峰值与时间未知，现有资源保护不得放宽。**需要新的表达批准与独立优化授权，本任务没有实施。**

## 7. 完整性与停止

科学证据足以确认C06_EXECUTION_ACCEPTED_SCIENCE_NOT_ACCEPTED；完整原始归档备份单独为LOCAL_SYNC_PENDING，缺13,075,703字节及最终全包SHA/CRC/BACKUP_INDEX核验。只恢复本地已收到成员和同SHA向量，未申请或擅自使用新传输窗口。审阅ZIP为轻量报告/证据包，不是完整原始备份。

本轮停止。G6-05持续暂停，不开始C07、2920时段Gate6或Integrated/Disconnected/DEC。下一步由用户与ChatGPT审阅决定。
'''
(O/'C03_C05_C06_COMPARATIVE_FORENSICS.md').write_text(forensic,encoding='utf-8')
ledger=f'''\n## C06 final comparative closeout — 2026-10-12\n\n- **C06_EXECUTION_ACCEPTED_SCIENCE_NOT_ACCEPTED**；Run `{RID}`，真实Status2/SolCount1/143 Barrier/282.179754秒，唯一optimize已结束，生产提交`34a34b69ef752d7809487ca609cd91e12f75bffd`。\n- C03单因素BarConvTol 1e-6→1e-9，Aggregate1；154项实际参数核验。C05 NUMERIC/SolCount0，无可比较返回解。\n- 资源账户377→85（无新增），义务组111→0；矩阵48298→243（均库存下界，无新增）；stationarity4304→3336（保留3291/新增45），自由RC365→0；目标差与加权stationarity L1恶化，不能宣称科学PASS。\n- 原单位/原生三向量由已接收数据与D/R逆映射核得一致云端SHA；163局部行/5列精确核算支持真实返回点违规。科学模型、阈值及旧结果未修改。\n- 云端封存完成；**LOCAL_SYNC_PENDING**：已收140640256/153715959字节，缺13075703，原60分钟窗过期且未重开。完整gzipCRC/BACKUP_INDEX待新传输授权；审阅ZIP不替代原始备份。\n- 唯一建议为预算匹配等价坐标的受控日模型对照，PROPOSED/未执行，须另行批准。仍在C阶段，D及2920时段未获授权；G6-05 PAUSED_BY_USER。\n- 详细报告：`research/05_baseline_evolution/20261011/c06/C03_C05_C06_COMPARATIVE_FORENSICS.md`；本轮独立分支`codex/c06-barconvtol-daily-20261012`，关联#13/#14/#15。真实结果提交与PR在Git发布回执绑定，不自动合并。\n'''
for rel in ('research/05_baseline_evolution/20261011/BASELINE_EVOLUTION_LEDGER.md','research/STAGE2_PROJECT_LEDGER.md','research/05_baseline_evolution/20261011/b03_c00/C00_GO_NO_GO_CHECKLIST.md'):
 p=ROOT/rel;text=p.read_text(encoding='utf-8');assert '## C06 final comparative closeout — 2026-10-12' not in text;p.write_text(text+ledger,encoding='utf-8')
index=O/'C06_EVIDENCE_INDEX.json';dump(index,{'status':'COMPARATIVE_CLOSEOUT_BACKUP_PENDING','production_commit':'34a34b69ef752d7809487ca609cd91e12f75bffd','files':[{'relative':p.relative_to(O).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(O.rglob('*')) if p.is_file() and p!=index]})
print(json.dumps({'status':C['classification'],'backup':BS['status'],'evidence_files':len(read(index)['files']),'new_stationarity_assets':sorted(newassets-oldassets)},ensure_ascii=False))
