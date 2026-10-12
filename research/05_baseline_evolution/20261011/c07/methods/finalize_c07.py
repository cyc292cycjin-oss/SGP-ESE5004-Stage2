"""Publish bounded C07 evidence after local source verification; no cloud/solver calls."""
from pathlib import Path
import json,shutil,hashlib,subprocess,datetime,re,ast
from compact_exact_evidence import compact
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c07_v4_reliability_20261013')
REPO=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
O=REPO/'research/05_baseline_evolution/20261011/c07';E=O/'evidence'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
def put(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
def table(headers,rows):return '| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in rows)
assert subprocess.check_output(['git','-C',str(REPO),'branch','--show-current']).decode().strip()=='codex/c07-v4-reliability-20261013'
C=read(W/'C07_C06_A_B_COMPARISON.json');A=C['results']['A'];B=C['results']['B'];assert A['native_status']==2 and B['native_status']==3 and not all(A['postprocess']['gates'].values()) and B['postprocess'] is None
roots={};backups={};calls={};params={};provenance=[];bulk=[];logs={};resources={}
base=read(W/'release/C06_EFFECTIVE_MODEL_PARAMETERS.json')
for k in ('A','B'):
 br=read(W/(k+'_LOCAL_BACKUP_RECEIPT.json'));assert br['status']=='LOCAL_BACKUP_SHA_VERIFIED';p=Path(br['local_run'].replace('D:\\','/mnt/d/').replace('\\','/'));roots[k]=p;backups[k]=br
 call=read(p/'NATIVE_CALL_EXIT.json');assert call['optimization_calls']==1 and call['native_return_code']==0
 para=read(p/'EFFECTIVE_MODEL_PARAMETERS.json');assert len(para)==len(base)==154
 difference=[dict(parameter=n,C06=base[n],C07=para[n]) for n in sorted(base) if base[n]!=para[n]]
 assert difference==([] if k=='A' else [dict(parameter='Crossover',C06=0,C07=-1)])
 calls[k]=dict(run_id=br['run_id'],call=call,entry=read(p/'C07_NATIVE_OPTIMIZE_ENTERED.json'),raw=read(p/'raw/vectors/RAW_RECEIPT.json'),transfer=read(p/'NATIVE_TRANSFER.json'),authorization=read(p/'AUTHORIZATION.json'))
 params[k]=dict(count=154,differences_vs_C06=difference,all_parameters=para)
 index=read(p/'BACKUP_INDEX.json');assert sha(p/'BACKUP_INDEX.json')==br['BACKUP_INDEX_sha256']
 for r in index['files']:
  src=p/r['relative'];assert sha(src)==r['sha256']
  if src.suffix not in ('.json','.jsonl','.log') or r['bytes']>4_000_000:
   bulk.append(dict(run=k,relative=r['relative'],bytes=r['bytes'],sha256=r['sha256'],local_path=br['local_run']+'\\'+r['relative'].replace('/','\\'),published=False));continue
  dst=E/('run_'+k)/r['relative'];dst.parent.mkdir(parents=True,exist_ok=True);data=src.read_bytes();public=data;redaction=None
  if src.suffix=='.log':
   # Preserve numerical lines byte-for-byte; only registration/credential metadata lines are replaced.
   ls=data.splitlines(keepends=True);safe=[];changed=[]
   for num,line in enumerate(ls,1):
    if any(tag.lower() in line.lower() for tag in (b'Academic license ',b'WLSAccessID',b'WLSSecret',b'LicenseID',b'licensed to',b'registered to')):
     safe.append(b'[REDACTED: license registration metadata; numerical lines unchanged]\n');changed.append(num)
    else:safe.append(line)
   public=b''.join(safe);redaction={'scope':'registration metadata lines only','line_numbers':changed} if changed else None;dst=dst.with_name(dst.stem+'.redacted.log')
  dst.write_bytes(public);provenance.append(dict(run=k,source_relative=r['relative'],source_sha256=r['sha256'],public_relative=dst.relative_to(O).as_posix(),public_sha256=sha(dst),bytes=len(public),redaction=redaction))
 for n in ('BACKUP_INDEX.json','CLOUD_SEAL_COMPLETE.json'):copy(p/n,E/('run_'+k)/n)
 copy(W/(k+'_LOCAL_BACKUP_RECEIPT.json'),E/(k+'_LOCAL_BACKUP_RECEIPT.json'))
 snap=read(sorted((W/'monitor_snapshots').glob(k+'_*.json'))[-1]);assert all(not x['live'] for x in snap['live'].values()) and snap['_SEAL_GUARD_RECEIPT.json']['status']=='SEALED'
 put(E/(k+'_TERMINAL_OBSERVATION.json'),snap)
 text=(p/'gurobi.log').read_text();lines=text.splitlines();rows=[]
 for line in lines:
  m=re.match(r'^\s*(\d+)\s+([+-]?[\d.]+e[+-]\d+)\s+([+-]?[\d.]+e[+-]\d+)\s+([\d.]+e[+-]\d+)\s+([\d.]+e[+-]\d+)\s+([\d.]+e[+-]\d+)\s+(\d+)s\s*$',line)
  if m:rows.append(dict(iteration=int(m[1]),primal=m[2],dual=m[3],primal_residual=m[4],dual_residual=m[5],complementarity=m[6],seconds=int(m[7])))
 logs[k]=dict(barrier_rows=rows,presolve=[l for l in lines if 'Presolve' in l or 'Presolved' in l],warnings=[l for l in lines if 'Warning' in l],final_lines=lines[-20:],source_log_sha256=sha(p/'gurobi.log'))
 resources[k]=dict(**C['results'][k]['resources'],t0_epoch=calls[k]['authorization']['started_epoch'],total_absolute_deadline=calls[k]['authorization']['absolute_deadline_epoch'],seal_exit_epoch=snap['_SEAL_GUARD_RECEIPT.json']['ended_epoch'],elapsed_to_seal_seconds=snap['_SEAL_GUARD_RECEIPT.json']['ended_epoch']-calls[k]['authorization']['started_epoch'],worker_supervisor_guard_exited=True)
assert len(logs['A']['barrier_rows'])==len(logs['B']['barrier_rows'])
same=all({q:v for q,v in x.items() if q!='seconds'}=={q:v for q,v in y.items() if q!='seconds'} for x,y in zip(logs['A']['barrier_rows'],logs['B']['barrier_rows']))
put(O/'C07_PARAMETER_AND_CALL_LEDGER.json',dict(new_optimize_calls=2,third_call_authorized=False,parameters=params,calls=calls,B_condition='A OPTIMAL + complete vectors + identity/mapping PASS, original physical/local KKT FAIL, all A processes exited and seal complete',printed_barrier_trajectories_same_excluding_seconds=same,comparison_scope='printed precision only; not internal iterates'))
put(E/'C07_LOG_TRAJECTORY.json',logs);put(E/'C07_RESOURCE_AND_STOP_SUMMARY.json',resources)
put(E/'C07_PUBLIC_EVIDENCE_PROVENANCE.json',dict(files=provenance,bulk_excluded=bulk,raw_originals_unchanged=True))
backup={k:{q:v for q,v in br.items() if q!='files'} for k,br in backups.items()};backup['C06']={q:v for q,v in read(W.parent/'c06_barconvtol_20261012/C06_LOCAL_BACKUP_RECEIPT.json').items() if q!='files'};put(O/'C07_FINAL_BACKUP_STATUS.json',backup)
for n in ['C07_C06_A_B_COMPARISON.json','C07_EXACT_LOCAL_CROSS_COORDINATE_CHECK.json','A_ALL_ACCOUNT_GROUP_COMPARISON.json','A_ROW_FAMILY_CHECK.json','A_KKT_CLASSIFICATION.json','A_TARGETED_EARLY_CHECK.json','C07_TRANSFER_SOURCE_IDENTITIES.json','C07_TRANSFER_WINDOW.json','A_TRANSFER_COMPLETE.json','B_TRANSFER_COMPLETE.json']:
 if n=='C07_EXACT_LOCAL_CROSS_COORDINATE_CHECK.json':put(E/n,compact(W/n))
 else:copy(W/n,E/n)
put(O/'C07_FULL_V4_COMPARISON.json',C);copy(W/'expression/C07_EXPRESSION_BINDING.json',O/'C07_NUMERICAL_EXPRESSION_SPEC.json');copy(W/'C07_EXPRESSION_STATIC_CHECK.json',O/'C07_EQUIVALENCE_AND_BUDGET_AUDIT.json')
for n in ['compare_c07.py','finalize_c07.py','backup_c07.py','targeted_readonly.py','compact_exact_evidence.py']:
 # Connection utility is not published; backup method imports site-local safe SSH configuration.
 copy(W/n,O/'methods'/n)
register=[
 ('physical_rows_bounds','A','Direct frozen LP and engineering equations','native row units: MW/MWh/tCO2/MWkm','0.001+1e-7*reference','release/helpers/v4_algebra_extracted.py','budget_arrays'),
 ('resource_terminal_annual','B','Derived for frozen exclusive lossless fixed-demand group: sum(eT)=sumQ-D, eT>=0','MWh','Bi=min(.001+1e-7Qi,1e-6Qi); all Sg<Bi','release/helpers/fixed_resource_acceptance.py','inventory'),
 ('resource_dynamic_prefix','A/B','Store dynamics and cumulative resource conservation','MWh','Same single annual Bi, no daily reset','release/helpers/fixed_resource_acceptance.py','inventory'),
 ('gross_L1','C','Approved cumulative numerical leakage and cancellation control','MWh','Existing V4/1ppm rule','release/helpers/fixed_resource_acceptance.py','obligation'),
 ('stationarity_sign_complementarity','C','Minimization LP primal/dual stationarity and endpoint sign, no 0*Inf','EUR/original unit; EUR','Existing normalized 1e-6 and explicit free RC sign check','release/helpers/v4_algebra_extracted.py','complete_kkt'),
 ('identity_export','D','Complete label/coordinate/SHA binding and exact export readback','identity','Exact, no 1ULP relaxation','release/daily_acceptance.py','postprocess')]
rr=[]
for key,kind,meaning,unit,budget,src,fn in register:
 tree=ast.parse((O/src).read_text());functions={n.name:n.lineno for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)}
 assert fn in functions,(src,fn)
 rr.append(dict(requirement=key,classification=kind,meaning=meaning,unit=unit,budget=budget,source=src,source_sha256=sha(O/src),function=fn,line=functions[fn],formal_contract_changed=False))
put(O/'V4_REQUIREMENT_TO_MODEL_REGISTER.json',dict(status='CURRENT_V4_APPLICABLE_WITH_EXPLICIT_NUMERICAL_LIMITS',requirements=rr,scientific_decision_required=False,universal_optimal_threshold_claim=False,candidate_V5_created=False))
K=A['KKT'];Q=A['resource_totals'];S=A['KKT_classification'];ex=read(W/'C07_EXACT_LOCAL_CROSS_COORDINATE_CHECK.json');row=read(W/'A_ROW_FAMILY_CHECK.json')['failed_rows'][0];er=next(r for r in ex['rows'] if r['row']==row['row']);rowasset=er['support'][0]['coordinates']
old=read(W.parent/'c06_barconvtol_20261012/C06_ALL_ACCOUNT_AND_GROUP_COMPARISON.json');ak=read(W/'A_KKT_CLASSIFICATION.json');tr=S['C06_stationarity']
gates=table(['原V4门槛','C07A','C07B'],[(k,'PASS' if v else 'FAIL','FAIL: Status=3' if k=='native_optimal' else 'NOT_AVAILABLE: SolCount=0; V4未执行') for k,v in A['postprocess']['gates'].items()])
native=table(['指标','C06','C07A','C07B'],[('Status / SolCount','2 / 1','2 / 1','3 / 0'),('Barrier迭代',143,A['info']['BarIterCount'],B['info']['BarIterCount']),('Simplex迭代',0,A['info']['IterCount'],B['info']['IterCount']),('Runtime秒',282.17975401878357,A['info']['Runtime'],B['info']['Runtime']),('算法变化（相对C06）','基准','无；仅D/R变化','Crossover 0→−1；D/R与A相同')])
metric=table(['原单位/原V4指标','C06','C07A','C07B'],[
 ('矩阵失败行',243,K['row_fail_count'],'NOT_AVAILABLE'),('矩阵最大库存违约 MWh',54.83195485051556,K['row_violation_max'],'NOT_AVAILABLE'),('列界失败',0,K['column_fail_count'],'NOT_AVAILABLE'),('资源失败账户 /807',85,Q['failed_accounts'],'NOT_AVAILABLE'),('义务失败组 /385',0,Q['failed_groups'],'NOT_AVAILABLE'),('年度正向账户超用 MWh',307.6417865795645,Q['positive_annual_overuse_MWh'],'NOT_AVAILABLE'),('年度少用绝对量 MWh',sum(max(0,-r['C06']['metrics']['annual_signed_error_MWh']) for r in old['accounts']),Q['negative_annual_shortfall_MWh'],'NOT_AVAILABLE'),('最大账户误差/自身预算','见C06原表',Q['max_account_error_budget_ratio'],'NOT_AVAILABLE'),('stationarity失败列',3336,K['stationarity_fail_count'],'NOT_AVAILABLE'),('stationarity最大归一化',2.7573625480333517e-5,K['stationarity_normalized_max'],'NOT_AVAILABLE'),('自由RC失败',0,S['free_RC_failures'],'NOT_AVAILABLE'),('全部对偶符号失败',0,K['dual_sign_fail_count'],'NOT_AVAILABLE'),('互补L1 EUR',29.53246018208337,K['complementarity_l1'],'NOT_AVAILABLE'),('最大互补项 EUR',1.0581741502357782,K['complementarity_max'],'NOT_AVAILABLE'),('加权stationarity L1 EUR',120113.44151863272,K['stationarity_weighted_l1'],'NOT_AVAILABLE'),('原对偶绝对差 EUR',117699.0634765625,K['absolute_gap'],'NOT_AVAILABLE'),('相对目标差',2.749886829086506e-7,K['relative_gap'],'NOT_AVAILABLE')])
card=table(['组内账户数','组数/账户数','C06失败账户','C07A失败账户/组'],[(r['account_count'],str(r['groups'])+'/'+str(r['accounts']),next(o['C06']['failed_accounts'] for o in old['cardinality'] if o['account_count']==r['account_count']),str(r['failed_accounts'])+'/'+str(r['failed_groups'])) for r in Q['cardinality']])
resource_table=table(['Run','RSS采样峰值GiB','cgroup最小余量GiB','磁盘最小余量GiB','生产到封存秒','保护触发'],[(k,f"{r['sampled_process_RSS_max']/2**30:.6f}",f"{r['cgroup_headroom_min']/2**30:.6f}",f"{r['disk_free_min']/2**30:.6f}",f"{r['elapsed_to_seal_seconds']:.6f}",r['protection_reasons']) for k,r in resources.items()])
backup_table=table(['Run','归档字节','SHA256','新增索引文件','本地状态'],[(k,br['archive_bytes'],br['archive_sha256'],br['indexed_files'],br['status']) for k,br in backup.items()])
literature=(O/'LITERATURE_AND_VERSION_EVIDENCE.md').read_text();shortlit=literature[literature.index('|原文|'):literature.index('上述原文')]
report=f'''# C07 V4可靠性核定与有限数值补救结果

**C07A：ORIGINAL_V4_FAIL；C07B：NO_QUALIFIED_SOLUTION。两次新增调用均已结束，全部新增原件及C06补齐归档为LOCAL_BACKUP_SHA_VERIFIED。** 没有修改正式V4或科学模型，没有第三次优化。仍为C阶段365日日诊断，不是2920时段Gate6通过。

证据等级：VERIFIED为原始机器回执/实际数组计算；DERIVED为明示假设下的恒等式；INFERENCE为机制解释；PROPOSED为未执行后续方向。主索引、逐账户/逐列数据及复核脚本均在本目录，原始大文件留在独立证据目录。

## 1. 真实调用与终态

- C07A：`{A['run_id']}`；C07B：`{B['run_id']}`。每次GRBoptimize返回码0、调用计数1，各自独立授权、Run、消费标记和固定7200秒窗口。
- A先合法OPTIMAL并保存完整X/Pi/RC，源SHA、154参数、精确交接、坐标映射、契约和NetCDF回读通过，仅原单位物理/局部KKT失败，且所有生产进程退出/封存完成，才启动B。条件证据包含在B的AUTHORIZATION及本轮调用台账。
- B在同一次原生调用内完成153次Barrier后进入Crossover：dual pushes与primal pushes完成，cleanup/uncrush后最终Status=3 INFEASIBLE、SolCount=0。Barrier中间“Optimal objective”不是最终状态；511,564次IterCount也不等于511,564次新增优化。无合法X/Pi/RC，不运行虚构V4。

{native}

B日志末尾显示push后Dinf约11.263173，cleanup从509,766迭代到511,562时出现PInf约9.69117e−4、DInf约1.9929e11，另有2次uncrush迭代。它是本次返回过程的直接证据，不能单凭该日志定位哪条科学约束不可行。Status3为数值求解器分类，本轮未取得严格Farkas/有理数证书；A也不是严格可行点，二者不能据此认定为Gurobi逻辑自相矛盾。

## 2. V4科学含义与原文核定

**当前V4定义在此冻结模型范围内有明确依据；本轮没有发现必须改变科学定义/阈值的实现冲突。主要未达标点仍是返回解的局部数值质量。** 这不宣称V4是所有能源模型的普适最优精度。详细A/B/C/D分类、单位、代码位置见V4_REQUIREMENT_TO_MODEL_REGISTER.json和LITERATURE_AND_VERSION_EVIDENCE.md。

{shortlit}

固定资源Q是上限，不被改写成普遍“必须耗尽”的科学原则。但在当前独占、无损、非循环且终端Load固定的组内，完整平衡/库存等式给出ΣeT=ΣQ−D=Sg；eT≥0推出0≤e_iT≤Sg。Fraction核算385组均Sg≥0且Sg小于每个Bi，最大Sg=9.816722013056278e−8 MWh，最大Sg/minBi=4.673060929996528e−5。因此本模型近零终态/近Q年度释放是派生结果，不是临时添加eT=0。C06的23项少用不能由Scheme A源舍入余量解释，也不能独立忽略同组负库存。

一般原单位预算仍0.001+1e−7×reference；807账户仍Bi=min(0.001+1e−7Qi,1e−6Qi)，前缀、逐期和全年L1不每日重置，也不扣除C01R表示误差。局部stationarity归一化正是原V4的|c−Aᵀy−r|/max(1,|c|+Σ|Aijyi|+|r|)，没有另造宽松指标。固定变量/等式允许任意符号乘子；不存在端点须零对应乘子，自由RC须零；代码掩码避免0×Inf。

须区分物理等式与数值预算的依据：精确LP要求零残差，但不能从物理等式本身推导0.001 MWh或1e−6恰为唯一合理的工程精度。这些是已批准的项目数值质量要求，不是原始数据测量精度或文献普适标准。本次失败库存行的一般预算约为该账户Q的2.26e−10，明显严于账户Bi/Q约1.00e−7；这种双重门槛值得在未来科学决策中明示，却不构成实现自相矛盾。本轮仍执行两者的交集。即使单独讨论该库存行的精度，另有3353列stationarity及12045自由RC未达标，不能仅放宽这一条就宣布科学通过；没有启用任何替代阈值。

全局目标差、互补L1和加权stationarity L1仍以含固定项max(1,|P|,|D|)归一化，门槛1e−6，并披露绝对EUR值。这是浮点认证，不是严格最优区间。C06两个固定目标列加offset合计2,594,498,284.5356255 EUR，去全部固定项尺度425,419,710,269.86273 EUR，正式尺度428,014,208,554.3984 EUR；绝对差不变。不存在通过改offset稀释误差的处理；未建立或启用V5。

## 3. 同一数学问题、唯一D/R表达与原生交接

日模型2,450,005列、6,042,238行、11,403,496非零；CSC、行列次序、科学目标及V3微扰、Scheme A、C01R、父V4均不变。原数学Manifest SHA `f70b2dc2dfc79e5b7caadc22beb30b82520a91b1aabf3dd720962af120302a70`，日V3 cost `c9a9717c664e2b3d5d4ca9b56848097f5231823465516113a13e00cb8f632d83`，日V4 `8c48d0735e6dcde870fdff589915aba57b55870994e75bc04b76d39e41c38459`，父V4 `955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f`。

唯一表达C07_DAILY_RESOURCE_BUDGET_POW2_V1，绑定SHA `5561a91045ca9196183e6d4ae61c9dde76d85343e8397d880b5c4652a6b5e77f`；α=1，offset −12,788,967.997821666 EUR不变。D指数SHA `e1b8ae22033efd37737b99c77d05d91b73fc868e5787ceef4dc76347b1971ba3`；R指数SHA `cba72671b366f0e0cfbc7941ac36dea7896eb5ef10378d167a07d136ec41d2c5`。改884,472个D和2,203,217个R，指数范围分别[−17,12]/[−12,17]。

以τ=1e−6、N=365、H=8760、设计安全因子8，资源能量行R_e=2^ceil(log2(8τN/Bi))，流量/Bus行R_p=2^ceil(log2(8τH/Bi))；对应Store-e与Store-p/meter/capacity列D分别取倒数，组Bus按最小Bi选择。覆盖全部807/385，不只改历史失败资产。普通列D≤64、普通行R≥1/64，两个固定目标列不变；这是一套数学等价坐标，不是更改算法参数或科学预算。

全量binary64反变换逐值通过，保持±0/无穷语义、自由界、行方向、无非零下溢或溢出，结构与索引原样；新系数非零绝对值0.0012500829394132243—32768。目标固定项仍达8.22449e9，最大固定列界5.61720e9，未为缩小范围做消元。设计预算RBi与τ的比较只是输入表达参考，不能保证Barrier相对停止或累计残差必过V4。

本机静态接口10项正反例和全量恢复通过；真实12.0.3 WLS环境启动通过。A/B各自同一原生模型完整载入与逐值回读，耗时{calls['A']['transfer']['load_and_readback_seconds']:.6f}/{calls['B']['transfer']['load_and_readback_seconds']:.6f}秒；17,369项不可变输入SHA核验。154项参数A对C06差异0，B唯一Crossover0→−1；TimeLimit3600、SoftMemLimit65十进制GB、MemLimit1e100。全部基底参数表随包公开，不只列7项。

新RAW原生X/Pi/RC先fsync/SHA，再以z_old=(Dnew/Dold)znew、pi_old=(Rnew/Rold)pinew、rc_old=(Dold/Dnew)rcnew映射到独立旧V4坐标目录。未覆盖原生数组或重贴旧质量属性；原V4代码和阈值复用。没有重建网络/LP、CSR→CSC、warm start、独立presolve、IIS或feasRelax。

## 4. 原V4结果与C06定量对照

{gates}

{metric}

{card}

C06的85个失败账户（62超用/负库存、23少用/正终态）在A全部通过，原377/111集合没有新增账户或义务失败；1/2/3/4账户组均无失败。年度总的微小gross误差仍如表披露，不能把它们写成精确零或与少用相互抵消。A仍有一条非合格库存行：row={row['row']}，label={row['label']}，资产/时间`{rowasset}`，违约{row['violation']:.15g} MWh，预算{row['budget']:.15g} MWh。该账户Q=4,422,461.756462411 MWh、Bi=0.4432461756462411 MWh；同一库存值可通过账户Bi门槛，却不通过约0.001 MWh的一般行门槛。两项是正式V4并存的独立检查，没有把更宽的Bi覆盖一般行规则。不是“其他非固定Store”的失败。

stationarity分类：{S['stationarity_families']}；相对C06保留{len(tr['retained'])}列、解除{len(tr['resolved'])}列、新增{len(tr['new'])}列。全部对偶符号分类{S['sign_families']}，其中自由RC {S['free_RC_failures']}项。不能只报告旧失败消失而忽略新失败。明细含完整列号/资产/时段，不输出大向量。

本轮独立核算只遍历一次现成11.4M日CSC来分类全部返回列，未扫描历史全年矩阵；用保存activity/预算分类全部行。另对{len(ex['rows'])}个局部完整CSR行、{len(ex['columns'])}个完整CSC列使用Fraction核验原单位、旧坐标与新坐标残差恒等；均精确相等。代表列给出γ_(2k+4)算术误差上界，假定无溢出/渐进下溢及通常binary64运算，不是模型条件数或求解误差保证。见C07_EXACT_LOCAL_CROSS_COORDINATE_CHECK.json，不把浮点差异归咎于坐标回映射。

A的已知范围原科学成本{A['costs']['original_scientific_objective_known_scope']:.9f} EUR，V3复算{A['costs']['adapted_objective']:.9f} EUR，扰动贡献{A['costs']['numerical_perturbation_contribution']:.9f} EUR，FOM一次计量复算差{A['costs']['reconciliation_residual']:.12g} EUR；均为未合格候选，不是正式系统成本。原未扰动目标最优性NOT_PROVEN，NULL费用未填零，FullSystemCostComplete=false。B没有候选成本或双账数值，NOT_AVAILABLE。

## 5. 证据支持的解释与剩余阻断

VERIFIED：同一数学问题的表达变化改善了资源库存/年度数值质量；全部807/385通过，但局部KKT及同一固定账户的一般库存行仍失败。该行Rnew=1/128，0.008419696565397317 MWh对应新坐标6.577887941716654e−5，恰与原生ConstrVio对应。账户预算匹配没有保证更严格的一般行预算或Barrier返回点本身达到全部门槛。

原生DualVio={A['info']['DualVio']}属于新坐标，不能直接与原单位比较。最坏自由RC位于Store-p列2047858，MM2 3住宅Biogases、1月1日；Dnew=2^−14，原生RC=6.6060390710395024e−9，原单位RC=1.0823334413991121e−4，精确乘2^14而得。实际表明这套偏重原始物理预算的表达并不同时保证自由RC原单位预算。不能用求解器小于1e−6的输入空间质量值替代V4。全局相对gap通过也不蕴含每个局部物理/KKT通过。

VERIFIED：A/B打印精度下的Barrier轨迹（除秒数）相同={same}；B增加Crossover/cleanup后最终分类发生变化。没有B合法向量，因此不能断言它修复了A的库存或KKT，也不能将日志PInf0当作完整可行证书。

INFERENCE：预算匹配表达能改善一部分原单位误差，而原生停止/原模型恢复及cleanup仍有数值敏感性。当前证据不足以区分其他精确不可行性、预处理/恢复敏感性或某实现Bug；未找到可以只改验收代码就获得科学PASS的证据。旧Scheme A之前的严格证书不得移作当前日LP的证书。

**唯一下一步建议：以当前冻结日LP及A/B同表达、同参数除Crossover的成对原生回执，开展有明确目标的供应商数值复核。** 问题限定为“Barrier候选未达局部原单位门槛，Crossover/uncrush为何最终Status3”。不要再盲试1e−10/1e−12、NumericFocus等网格。现成原始数组、表达代码、154参数表、原生日志、完整回读/RAW和局部有理数残差构成最小重现资料规范；大模型为私有数据，未经用户批准不得对外上传。支持方若需重跑、写MPS或第三次优化，须新的明确授权，本轮不执行。

复现定位资料：源CSC三维及SHA如第3节；`release/c07_native.py`的唯一原生调用与`c07_expression_runtime.py`的输入覆盖；`release/expression/c07_expression.py`的精确幂二变换；A/B实际参数差异、日志cleanup段、A失败行/列及各坐标残差见本包。只读本地提取已完成；不把局部支撑子块单独冒称为等价可求解的缩小模型。

## 6. 资源、备份与最终停止

实际122号机12有效CPU、90GiB cgroup，Python3.11.13、Gurobi12.0.3。严格可信ED25519验证，WLS只绑定路径，未读取或公开密钥。独立supervisor/guard覆盖载入、RAW、验收与封存；RSS75GiB、余量12GiB、盘8GiB不变，启动盘≥20GiB并预留4GiB新增输出。A/B各固定7200秒，不滚动延期，均正常提前结束。

{resource_table}

RSS是进程树采样峰值；cgroup样本/生命周期峰值含同容器其他进程和缓存，不能当成Gurobi独占峰值。终态核实worker/supervisor/guard全部退出，sealguard退出0，无保护事件。122实例保持运行，未关机/释放，实例开机继续计费。

{backup_table}

C06用新获批60分钟窗口在源SHA与140,640,256字节前缀一致后补收13,075,703字节；旧partial/过期窗口保留。C07另一个60分钟窗在最后云端封存后开始，只接收现成A/B新增归档；大小、整包SHA、gzipCRC、tar安全路径及逐文件BACKUP_INDEX全部核验。17,369项旧输入按C04已SHA验证索引及原绑定/大小/存在性复用，未重复拷贝。云端封存中的历史LOCAL_SYNC_PENDING字段不改写，新本地回执提供当前状态。

本地原件：`D:\\ResearchWorkspaces\\ASEAN\\outputs\\c07_daily_diagnostic\\<run_id>\\cloud_run`；云端：`/root/autodl-tmp/SGP/runs/<run_id>`。完整精确路径与SHA见C07_FINAL_BACKUP_STATUS.json和公开大文件索引。审阅ZIP只含轻量证据/代码，不是大向量归档。

本轮实际优化总数2，无第三次授权。原V4没有通过，不进入2920时段Gate6或Integrated/Disconnected/DEC；G6-05仍PAUSED_BY_USER。待用户与ChatGPT审阅后再决定唯一后续动作。
'''
(O/'C07_V4_RELIABILITY_AND_REMEDIATION_RESULT.md').write_text(report,encoding='utf-8')
record=read(O/'IMPLEMENTATION_AND_PAYLOAD_REFERENCES.json');record['C07_archive_reception']='LOCAL_BACKUP_SHA_VERIFIED';record['final_report']='C07_V4_RELIABILITY_AND_REMEDIATION_RESULT.md';put(O/'IMPLEMENTATION_AND_PAYLOAD_REFERENCES.json',record)
milestone=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD']).decode().strip()
entry=f'''\n\n## C07 V4可靠性与有限补救收口 — 2026-10-13\n\n- **A ORIGINAL_V4_FAIL；B NO_QUALIFIED_SOLUTION；C06/A/B LOCAL_BACKUP_SHA_VERIFIED。** 本轮新增调用恰好2，全部结束，未改科学模型或V4。方法/代码及初始终态里程碑提交`{milestone}`已push。最终交付提交见包内GIT_PUBLICATION。\n- A `{A['run_id']}`：Status2、SolCount1、153 Barrier、281.128073秒；807/385全部通过；剩1矩阵库存下界、3353 stationarity、12045对偶符号项失败。完整X/Pi/RC先保存后映射，NetCDF/FOM通过不替代V4。\n- B `{B['run_id']}`：仅Crossover0→−1；Status3、SolCount0、153 Barrier/511564 simplex、343.263406秒；向量及V4 NOT_AVAILABLE，未伪造零残差，也不称严格不可行证明。\n- 同一日CSC、Scheme A/C01R/V3/V4，唯一D/R表达SHA5561a91045ca9196183e6d4ae61c9dde76d85343e8397d880b5c4652a6b5e77f；全量反变换及同模型真实回读通过，154参数A无差异、B仅Crossover。没有重建、warm start或额外presolve。\n- V4在此冻结组内语义可推导，未发现必须放宽的冲突；合法Scheme A余量小于各预算，未启用V5。独立局部Fraction核算支持真实残差，详细剩余数值阻断见c07主报告。\n- 两个Run均资源保护无触发并全退出封存。C06旧备份缺口已依新授权补齐；A/B全部新增文件SHA/CRC/索引通过，云端原件/历史消费标记保留。122实例未关机/释放。\n- 唯一建议为成对原生回执和冻结表达的供应商定点复核；不自动对外提交私有模型或第三次优化。G6-05 PAUSED_BY_USER，仍C阶段，2920及新情景未授权。\n'''
for rel in ['research/05_baseline_evolution/20261011/BASELINE_EVOLUTION_LEDGER.md','research/STAGE2_PROJECT_LEDGER.md','research/05_baseline_evolution/20261011/b03_c00/C00_GO_NO_GO_CHECKLIST.md']:
 p=REPO/rel;s=p.read_text();assert '## C07 V4可靠性与有限补救收口' not in s;p.write_text(s+entry,encoding='utf-8')
files=[]
for p in sorted(O.rglob('*')):
 if p.is_file() and p.name!='C07_EVIDENCE_INDEX.json':files.append(dict(relative=p.relative_to(O).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
put(O/'C07_EVIDENCE_INDEX.json',dict(files=files,large_arrays_included=False,formal_V4_changed=False,optimization_calls=2,all_new_local_backups_verified=True))
print(json.dumps({'final_report':str(O/'C07_V4_RELIABILITY_AND_REMEDIATION_RESULT.md'),'evidence_files':len(files),'backups':{k:v['status'] for k,v in backup.items()}},indent=2))
