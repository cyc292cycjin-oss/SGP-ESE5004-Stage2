"""C05 receipt-only synthesis. No arrays, model construction, network or solver calls."""
from pathlib import Path
import hashlib, json, re, shutil, datetime, subprocess

W = Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c05_aggregate0_20261012')
REPO = Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
REL = Path('research/05_baseline_evolution/20261011/c05')
OUT = REPO / REL
RUN = 'c05_aggregate0_daily122_20261012T074925Z_a39647d9'
BASE = 'c02r_c03_daily122_20261012T044259Z_25e62c10'
N = Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/c05_daily_diagnostic') / RUN / 'cloud_run'
B = Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/c03_daily_diagnostic') / BASE / 'cloud_run'
C4 = REPO / 'research/05_baseline_evolution/20261011/c04'
PRODUCTION = 'd6c48dbd95d12f0354561372e9a65d6e92511754'
assert subprocess.check_output(['git','-C',str(REPO),'branch','--show-current']).decode().strip() == 'codex/c05-aggregate0-daily-20261012'
assert subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD']).decode().strip() == PRODUCTION

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def utc(x): return datetime.datetime.fromtimestamp(x,datetime.timezone.utc).isoformat().replace('+00:00','Z')
def cp(src,dest):
    dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dest)

current = read(N/'raw/vectors/RAW_RECEIPT.json')
baseline = read(B/'raw/vectors/RAW_RECEIPT.json')
assert current['run_id'] == RUN and baseline['run_id'] == BASE
assert current['native_status'] == 12 and current['native_info']['SolCount'] == 0
assert current['GRBoptimize_return_code'] == 0
assert baseline['native_status'] == 2 and baseline['native_info']['SolCount'] == 1
assert current['model_manifest_sha256'] == baseline['model_manifest_sha256']
params = read(N/'EFFECTIVE_MODEL_PARAMETERS.json')
oldparams = read(B/'EFFECTIVE_MODEL_PARAMETERS.json')
assert len(params)==len(oldparams)==154
differences=[{'parameter':k,'C03':oldparams[k],'C05':v} for k,v in params.items() if v!=oldparams[k]]
assert differences == [{'parameter':'Aggregate','C03':1,'C05':0}]
auth = read(N/'AUTHORIZATION.json')
transfer = read(N/'NATIVE_TRANSFER.json')
entered = read(N/'C05_NATIVE_OPTIMIZE_ENTERED.json')
assert transfer['status']=='EXACT_READBACK_PASS'
assert transfer['native_model_handle']==entered['model_handle']
resources=[json.loads(s) for s in (N/'RESOURCE.jsonl').read_text().splitlines() if s.strip()]
seal=read(W/'C05_ARCHIVE_SOURCE_IDENTITY.json')
backup=read(W/'C05_LOCAL_BACKUP_RECEIPT.json')
assert backup['status']=='LOCAL_BACKUP_SHA_VERIFIED'
oldpost=read(B/'postprocess/POSTPROCESS_RECEIPT.json')
kkt=read(B/'postprocess/KKT.json')
pattern=read(C4/'evidence/C04_RECEIPT_PATTERN.json')
classif=read(C4/'evidence/C04_KKT_COLUMN_CLASSIFICATION.json')
tail=read(W/'monitor_snapshots/20261012T075221Z.json')

def log_stats(path):
    text=path.read_text()
    rows=[]
    for line in text.splitlines():
        m=re.fullmatch(r'\s*(\d+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+(\d+)s\s*',line)
        if m:
            a=m.groups(); rows.append(dict(iteration=int(a[0]),primal=float(a[1]),dual=float(a[2]),primal_residual=float(a[3]),dual_residual=float(a[4]),complementarity=float(a[5]),log_seconds=int(a[6])))
    def num(rx,typ=float): return typ(re.search(rx,text).group(1))
    p=re.search(r'Presolved: (\d+) rows, (\d+) columns, (\d+) nonzeros',text)
    return {'raw_log_sha256':sha(path),'log_values_are_rounded':True,
            'model_fingerprint':re.search(r'Model fingerprint: (\S+)',text).group(1),
            'presolve_seconds':num(r'Presolve time: ([\d.]+)s'),
            'presolved':dict(zip(['rows','columns','nnz'],map(int,p.groups()))),
            'ordering_seconds':num(r'Ordering time: ([\d.]+)s'),
            'dense_columns':num(r'Dense cols\s*:\s*(\d+)',int),
            'free_variables':num(r'Free vars\s*:\s*(\d+)',int),
            'factor_nnz_approx':num(r'Factor NZ\s*:\s*([\d.eE+]+)'),
            'iterations':rows,'last_iteration':rows[-1],
            'numerical_trouble': 'Numerical trouble encountered' in text}

logs={'C03':log_stats(B/'gurobi.log'),'C05':log_stats(N/'gurobi.log')}
samples=resources+seal['seal_guard']['samples']
rs={'run_id':RUN,'source_sha256':sha(N/'RESOURCE.jsonl'),'samples':len(resources),
    'first_sample_utc':utc(resources[0]['epoch']),'last_sample_utc':utc(resources[-1]['epoch']),
    'max_sample_interval_seconds':max(b['epoch']-a['epoch'] for a,b in zip(resources,resources[1:])),
    'sampled_worker_tree_peak_rss_bytes':max(x['rss_bytes'] for x in resources),
    'cgroup_lifetime_peak_start_bytes':resources[0]['cgroup'][0]['memory_peak'],
    'cgroup_lifetime_peak_end_bytes':max(c['memory_peak'] for x in samples for c in x['cgroup']),
    'cgroup_memory_current_sample_max_bytes':max(c['current'] for x in samples for c in x['cgroup']),
    'minimum_cgroup_headroom_bytes':min(x['cgroup_headroom_bytes'] for x in samples),
    'minimum_disk_free_bytes':min(x['disk_free_bytes'] for x in samples),
    'memory_events_observed':sorted(set(c['memory_events'] for x in samples for c in x['cgroup'])),
    'protection_reasons':[x['reason'] for x in samples if x['reason']],
    'peak_semantics':'RSS is sampled worker tree, may miss sub-sample peaks. cgroup peak is lifetime/cgroup shared statistic, not exclusive process peak.',
    'cpu_seconds_max_observed':max(x['cpu_seconds'] for x in resources),
    'start_epoch':auth['started_epoch'],'start_utc':utc(auth['started_epoch']),
    'native_runtime_seconds':current['native_info']['Runtime'],
    'load_readback_seconds':transfer['load_and_readback_seconds'],
    'seal_guard_end_epoch':seal['seal_guard']['ended_epoch'],
    'total_to_seal_guard_exit_seconds':seal['seal_guard']['ended_epoch']-auth['started_epoch'],
    'absolute_deadlines':{k:{'epoch':v,'UTC':utc(v),'from_t0_seconds':v-auth['started_epoch']} for k,v in auth.items() if 'deadline_epoch' in k},
    'stage_budget_seconds':{'load':900,'native':3600,'native_exit_TERM_graces':150,'raw':300,'post':1200,'seal':1050,'total':7200},
    'separate_transfer_seconds':read(W/'C05_LOCAL_TRANSFER_RECEIPT.json')['seconds'],
    'costs':'No billing read or cost trigger. Instance remains running; run duration is not full bill.'}
assert not rs['protection_reasons']
assert rs['total_to_seal_guard_exit_seconds'] < 7200
assert rs['minimum_disk_free_bytes'] >= 8*2**30
assert rs['minimum_cgroup_headroom_bytes'] >= 12*2**30
assert rs['sampled_worker_tree_peak_rss_bytes'] < 75*2**30

NA={'value':None,'status':'NOT_AVAILABLE_NO_LEGAL_COMPLETE_SOLUTION','improvement':'NOT_EVALUABLE'}
comparison={'classification':'C05_NUMERIC_NO_SOLUTION_NOT_ACCEPTED','baseline_run_id':BASE,'run_id':RUN,
 'production_commit':PRODUCTION,'model_manifest_sha256':current['model_manifest_sha256'],
 'same_model_handle_transfer_to_optimize':True,'new_build_count':0,'CSR_to_CSC_conversions':0,'warm_start':False,
 'native':{'C03':baseline,'C05':current},'numeric_parameter_count':154,'parameter_differences':differences,
 'C03_V4':oldpost,'C05_V4':{'status':'NOT_RUN_NO_COMPLETE_LEGAL_PRIMAL_DUAL','scientific_acceptance':'NOT_ACCEPTED','Pass':False},
 'physical_and_KKT_comparison':{
   'failed_accounts':{'C03':377,'C05':NA},'failed_obligation_groups':{'C03':111,'C05':NA},
   'matrix_failed_rows':{'C03':kkt['row_fail_count'],'C05':NA},'column_bounds_failed':{'C03':kkt['column_fail_count'],'C05':NA},
   'stationarity_failed_columns':{'C03':kkt['stationarity_fail_count'],'C05':NA},
   'free_RC_failed_items':{'C03':classif['sign_fail_count'],'C05':NA},
   'C03_stationarity_families':classif['stationarity_families'],
   'new_or_resolved_failed_assets':NA,
   'account_cardinality_groups':[dict(account_count=r['account_count'],groups=r['groups'],C03_failed=r['failed'],C05_failed=None,C05_status='NOT_AVAILABLE') for r in pattern['cardinality_table']],
   'C03_KKT_reference':kkt,'C05_KKT':NA},
 'costs':{'C03_known_scope':read(B/'postprocess/DUAL_COST_LEDGER.json'),
    'C05_original_scientific_EUR':None,'C05_V3_EUR':None,'C05_qualified_costs_available':False,
    'C05_native_unqualified_ObjVal':current['native_info']['ObjVal'],
    'interpretation':'Native ObjVal is preserved only as an unqualified scalar; SolCount=0, no cost reconciliation or optimality claim.'},
 'inference':{'verified':'Aggregate-only change changed presolve dimensions and returned numerical trajectory/status for this LP.',
    'not_proven':['Root cause of C03 physical violations','Mathematical infeasibility or unboundedness','Improvement/resolution of 377/111/4304/365 failures','New failure sets','Feasibility or PASS of the 2920-snapshot model'],
    'next_action':'STOP_FOR_USER_REVIEW_NO_FURTHER_OPTIMIZATION_AUTHORIZATION'},
 'backup':{'status':backup['status'],'archive_sha256':backup['archive_sha256'],'indexed_new_files':backup['indexed_files'],'immutable_references':backup['immutable_files']}}

evidence=OUT/'evidence'; evrun=evidence/'current_run'; evrun.mkdir(parents=True,exist_ok=True)
index=[]
for p in sorted(N.rglob('*')):
    if not p.is_file(): continue
    rel=p.relative_to(N)
    if rel.name=='gurobi.log':
        clean='\n'.join('[REDACTED: license registration metadata; original retained locally/cloud]' if 'Academic license ' in line else line for line in p.read_text().splitlines())+'\n'
        dest=evrun/'gurobi.redacted.log'; dest.write_text(clean,encoding='utf-8')
        index.append({'source_relative':str(rel),'source_bytes':p.stat().st_size,'source_sha256':sha(p),'published_relative':str(dest.relative_to(OUT)),'published_sha256':sha(dest),'redaction':'only license-registration metadata line; numerical log unchanged'})
    else:
        assert p.suffix in ('.json','.jsonl','.log') and p.stat().st_size < 4_000_000
        dest=evrun/rel; cp(p,dest)
        index.append({'source_relative':str(rel),'source_bytes':p.stat().st_size,'source_sha256':sha(p),'published_relative':str(dest.relative_to(OUT)),'published_sha256':sha(dest),'redaction':None})
for name in ['C05_ARCHIVE_SOURCE_IDENTITY.json','C05_LOCAL_BACKUP_RECEIPT.json','C05_LOCAL_TRANSFER_RECEIPT.json','C05_TRANSFER_WINDOW.json','DEPLOYMENT_RECEIPT.json','LAUNCH_ATTEMPT.json','LAUNCH_RECEIPT.json']:
    cp(W/name,evidence/name)
def redact_metadata(value):
    if isinstance(value,dict): return {k:redact_metadata(v) for k,v in value.items()}
    if isinstance(value,list): return [redact_metadata(v) for v in value]
    if isinstance(value,str): return '\n'.join('[REDACTED: license registration metadata]' if 'Academic license ' in line else line for line in value.split('\n'))
    return value
dump(evidence/'C05_TERMINAL_OBSERVATION.json',redact_metadata(tail))
for name in ['KKT.json','DUAL_COST_LEDGER.json','POSTPROCESS_RECEIPT.json']:
    cp(B/'postprocess'/name,evidence/'baseline_C03'/name)
cp(B/'raw/vectors/RAW_RECEIPT.json',evidence/'baseline_C03/RAW_RECEIPT.json')
for name in ['C04_RECEIPT_PATTERN.json','C04_BACKUP_RECEIPT.json']:
    cp(C4/'evidence'/name,evidence/'baseline_C04'/name)
text=(B/'gurobi.log').read_text()
(evidence/'baseline_C03/gurobi.redacted.log').write_text('\n'.join('[REDACTED: license registration metadata]' if 'Academic license ' in s else s for s in text.splitlines())+'\n')
dump(evidence/'C05_PUBLIC_EVIDENCE_PROVENANCE.json',{'original_run':str(N),'originals_unchanged':True,'files':index,'baseline_gurobi_original_sha256':sha(B/'gurobi.log'),'terminal_observation_original_sha256':sha(W/'monitor_snapshots/20261012T075221Z.json'),'terminal_observation_public_sha256':sha(evidence/'C05_TERMINAL_OBSERVATION.json'),'registration_metadata_removed_from_public_copy':True})
dump(evidence/'C05_LOG_TRAJECTORY_COMPARISON.json',logs)
dump(evidence/'C05_RESOURCE_AND_DEADLINE_SUMMARY.json',rs)
dump(OUT/'C05_BASELINE_RESULT_COMPARISON.json',comparison)
cp(N/'C05_SINGLE_FACTOR_PARAMETER_DIFF.json',OUT/'C05_SINGLE_FACTOR_PARAMETER_DIFF.json')
cp(Path(__file__),OUT/'methods/finalize_results.py')
cp(W/'verify_c05_backup.py',OUT/'methods/verify_c05_backup.py')

gib=lambda x:f'{x/2**30:.6f}'
newps=logs['C05']['presolved']; oldps=logs['C03']['presolved']
report=f'''# C05 Aggregate=0 日模型单因素诊断：真实终态

**结论：C05_NUMERIC_NO_SOLUTION_NOT_ACCEPTED。唯一一次优化已完成；云端封存和本地备份均通过。**

Run `{RUN}`。Gurobi 12.0.3 返回码0、模型 **Status=12 NUMERIC**、SolCount=0、24次Barrier、Runtime **81.595145秒**。没有合格日模型解；没有执行第二次优化、独立presolve、IIS或feasRelax。G6-05继续PAUSED_BY_USER；2920时段Gate6及其他情景未启动。

## 1. 科学与执行身份

本次实际生产代码为 `{PRODUCTION}`，独立分支 `codex/c05-aggregate0-daily-20261012`。基准C03代码 `a3c1f5e97e03b99f4fa5fa885f6fe0747768d7d7`，C04父提交 `4b76dc65662faef61ff429d3a299cc7db8bccd9b`；关联PR #13、#14，历史结果不改写。

实际复用17,369项、1,488,811,247字节的冻结输入，生产SHA检查通过；新网络构建0、CSR→CSC转换0、旧解warm start=false。`BUILD_RESULT.json`只是历史构建回执副本，其来源由IMMUTABLE_INPUTS明确标识，不表示本次重建。

| 身份 | SHA256 |
|---|---|
| 日CSC MATH_PROBLEM | `{current['model_manifest_sha256']}` |
| 日V3 cost | `c9a9717c664e2b3d5d4ca9b56848097f5231823465516113a13e00cb8f632d83` |
| 日D/R映射Manifest | `f5bdb465709c0840ad9c370f121b5f23d31f62310300ad7e47208b0b9d6d746e` |
| DAILY_V4_BINDING | `8c48d0735e6dcde870fdff589915aba57b55870994e75bc04b76d39e41c38459` |
| 父V4 | `955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f` |
| 未求解日NetCDF | `b2df7dc771d4759668988f7a0abd7ccfafacd976dff644f7acafd20aee50b9f2` |
| C05 Release Manifest | `9ad443c84c4a8271a153114f47bac496853181ee422c7d7dcf34ef2bf974787a` |
| C05实际参数 | `{sha(N/'EFFECTIVE_MODEL_PARAMETERS.json')}` |

实际规模2,450,005列、6,042,238行、11,403,496非零元。完整载入/逐值回读 **EXACT_READBACK_PASS**，耗时3.774589秒；交接与唯一调用记录为同一原生模型句柄。Scheme A、C01R、全部矩阵/界/标签、日目标offset和D/R保持原身份；未引入P2、科学变更或容差放宽。

154项原生数值参数逐项回读，仅Aggregate由1变0。TimeLimit3600、SoftMemLimit65十进制GB、MemLimit默认1e100均与C03相同。Method2/Crossover0/BarConvTol1e-6/NumericFocus0/FeasibilityTol1e-6/OptimalityTol1e-6/Threads4/Seed123/AggFill0/PreDual0/Presolve−1/DualReductions1/ScaleFlag−1/ObjScale0/历史200不变。完整差异表见[C05_SINGLE_FACTOR_PARAMETER_DIFF.json](C05_SINGLE_FACTOR_PARAMETER_DIFF.json)，不是只检查列出的参数。

## 2. 准入、唯一调用与保护

已核122实际容器身份、公钥、Python3.11.13及原生Gurobi12.0.3；有效CPU配额12核、cgroup90GiB（可见祖先与内核hierarchical限制）、开跑前磁盘27.349GiB。WLS文件只核元数据及绑定；生产GRBstartenv真实返回0。未读取或复制密钥/许可证内容，未重新安装环境。

独立Run/Release/授权/消费标记；准入时无同目的活跃任务，旧C03标记保留。同一模型仅执行一次GRBoptimize（NATIVE_TRANSFER→C05_NATIVE_OPTIMIZE_ENTERED→NATIVE_CALL_EXIT）。原生返回码0表示调用正常返回，不代表优化成功。

独立supervisor、guard及封存guard覆盖全程，不依赖浏览器/Codex；RSS75GiB、cgroup余量12GiB、盘8GiB保护有效。唯一必要控制兼容修订：原生截止后仅在原生已返回且RAW完整持久化时允许进入独立后处理预算；原STOP_REQUEST保留，资源/身份/其他异常仍停止。本次未触发此路径。12项局部无求解接口测试与实际运行分开记录。

| 阶段 | 固定预算/证据 |
|---|---|
| 生产t0 | {rs['start_utc']} |
| 载入、原生 | ≤900秒、≤3600秒；原生内TimeLimit实际回读3600 |
| 退出/TERM宽限、RAW、日V4、封存 | 150、300、1200、1050秒；共享7200秒固定上限 |
| 总绝对截止 | {utc(auth['absolute_deadline_epoch'])}（未延长） |
| 实际载入与精确回读 | {rs['load_readback_seconds']:.6f}秒 |
| 实际原生Runtime | {rs['native_runtime_seconds']:.6f}秒 |
| t0至封存guard退出 | {rs['total_to_seal_guard_exit_seconds']:.6f}秒 |
| worker进程树RSS采样最大 | {gib(rs['sampled_worker_tree_peak_rss_bytes'])}GiB |
| cgroup lifetime peak | {gib(rs['cgroup_lifetime_peak_start_bytes'])}→{gib(rs['cgroup_lifetime_peak_end_bytes'])}GiB |
| 最小cgroup余量 / 磁盘余量 | {gib(rs['minimum_cgroup_headroom_bytes'])} / {gib(rs['minimum_disk_free_bytes'])}GiB |

RSS为采样峰值，可能漏掉采样间短峰；cgroup峰值包含同组其他进程及既往运行，不能冒称Gurobi独占峰值。memory.events的max/oom/oom_kill均0；无资源/截止保护触发或受控终止。终态独立观察确认worker、supervisor、guard均退出，封存guard也退出。122仍保持运行，实例持续计费；未读取新账单，不以约96秒执行时长冒充整个实例费用。

## 3. 数值轨迹与C03对照

| 指标 | C03 Aggregate=1 | C05 Aggregate=0 |
|---|---:|---:|
| 模型指纹（辅助） | 0xadbe9ee0 | 0xadbe9ee0 |
| Presolve秒 | 10.79 | 8.06 |
| Presolve后行/列/非零 | {oldps['rows']:,}/{oldps['columns']:,}/{oldps['nnz']:,} | {newps['rows']:,}/{newps['columns']:,}/{newps['nnz']:,} |
| Free vars / Dense cols | 77,015 / 1,826 | 185,055 / 2,022 |
| 日志Factor NZ（近似） | 2.545e7 | 3.474e7 |
| Barrier次数 / Runtime秒 | 69 / 155.370943 | 24 / 81.595145 |
| 原生Status / SolCount | 2 OPTIMAL / 1 | 12 NUMERIC / 0 |
| 科学结果 | OPTIMAL_BUT_NOT_ACCEPTED | NOT_ACCEPTED；无合法完整解 |

C05第7次日志原始残差1.06e5、对偶残差2.72e3；第9次原始残差升为6.72e7。第14–24次日志停在原始残差7.07e5、对偶残差1.25e4、互补性5.56e10，随后“Numerical trouble encountered”。这些是日志四舍五入的求解器内部尺度指标，**不能替代原单位MW/MWh残差**。两次日志都有大目标系数/大边界警告。完整逐次提取见[evidence/C05_LOG_TRAJECTORY_COMPARISON.json](evidence/C05_LOG_TRAJECTORY_COMPARISON.json)。

**已验证：** 单一Aggregate改变了本次预处理后的规模及数值轨迹，关闭聚合没有产生可验收的解。**推论边界：** 本次不支持“单独关闭聚合即可解决C03失败”的预期；也没有证据把C03失败唯一归因于聚合、资源账户数或某个物理实现错误。NUMERIC不是INFEASIBLE(3)或INF_OR_UNBD(4)或UNBOUNDED(5)。日志的“may be infeasible or unbounded”及参数建议保留为原始文字，未作为数学结论或后续执行授权。[Gurobi12参考手册](https://docs.gurobi.com/_/downloads/optimizer/en/12.0/pdf/)、[原生模型Status/SolCount说明](https://docs.gurobi.com/projects/optimizer/en/12.0/reference/attributes/model.html)。

## 4. RAW与完整日V4的条件分支

先持久保存NATIVE_RETURN、RAW_RECEIPT、实际参数、日志及其SHA。SolCount0时生产安全门不提取数组，X/Pi/RC记为NOT_AVAILABLE/NO_LEGAL_SOLUTION_COUNT；这不表示逐个数组getter实际返回了10005。DualVio/ComplVio的属性查询实际返回10005，已原样保留。RAW_DURABLE明确native_state_preserved=true、complete=false。

ObjVal原始返回标量4.6484251002308625e14仅作为**未认证诊断值**保全；BoundVio=−1、ConstrVio=−1、MaxVio=0不能被解释为可行或零违规。没有合法完整向量，因此没有映射、独立残差计算、V4或NetCDF解导出；POSTPROCESS_NOT_RUN理由为NO_COMPLETE_LEGAL_PRIMAL_DUAL。此为用户批准的条件分支，不造partial解、不伪造验收失败计数。

| 日V4项目 | C03历史结果 | C05 |
|---|---|---|
| 全矩阵/列界 | 48,298行失败、列界0失败 | NOT_AVAILABLE |
| 807资源账户/385义务组 | 377/111失败 | NOT_AVAILABLE |
| 动态、前缀、累计绝对残差、Bus/转换/储能 | 物理验收失败 | NOT_AVAILABLE |
| stationarity | 4,304列失败（Line-s3,966、Link-p338） | NOT_AVAILABLE |
| 自由RC/对偶符号 | 365项失败，Line52 | NOT_AVAILABLE |
| 互补性/双目标差/KKT | 局部KKT不通过；相对双目标差1.968889e-7 | NOT_AVAILABLE |
| 原/V3双成本、FOM、NetCDF回读 | FOM/回读通过但科学失败 | NOT_AVAILABLE |
| 旧失败消失/新增失败资产 | 旧集合由C04核实 | 无法评估，不记为0 |

| 每组账户数 | 组数 | C03失败组数 | C05失败组数 |
|---|---:|---:|---|
| 1 |118|0|NOT_AVAILABLE|
| 2 |156|0|NOT_AVAILABLE|
| 3 |67|67|NOT_AVAILABLE|
| 4 |44|44|NOT_AVAILABLE|

C03原科学已知口径427,765,450,088.104 EUR，V3目标428,014,262,628.28937 EUR，均来自**未通过科学验收的旧候选**，并非完整已认证系统成本。C05没有可复算的合格原/V3成本，不能宣称成本改善、资源超用减少、Line/Link问题解决或日V4通过。没有对历史全年大矩阵或当前日矩阵开展额外扫描。

## 5. 云端与本地保全

云端Run：`/root/autodl-tmp/SGP/runs/{RUN}`；本地完整新证据：`D:\\ResearchWorkspaces\\ASEAN\\outputs\\c05_daily_diagnostic\\{RUN}\\cloud_run`。32项新增结果、195,688字节均按BACKUP_INDEX核SHA；另有索引与封存回执。原17,369项数学输入通过不可变引用复用；本地引用与此前C04已核SHA索引完全一致并核存在/大小，未重复旧大文件下载或全量重哈希。

现成新结果归档394,606字节，SHA256 `{backup['archive_sha256']}`。新独立60分钟窗口接收用时6.526404秒，下载次数1、重试0；大小、SHA、gzip CRC、成员/路径安全及全部新增文件SHA通过，**LOCAL_BACKUP_SHA_VERIFIED**。原云端LOCAL_SYNC_PENDING标记是封存时点历史记录，未改写；其后本地C05_LOCAL_BACKUP_RECEIPT构成已完成同步的新增证据。

原日志完整保留于云端与本地证据目录；GitHub/审阅ZIP中的日志副本仅移除一行许可证注册元数据，保留全部数值内容。发布来源、原始SHA、公开副本SHA及唯一删改项由C05_PUBLIC_EVIDENCE_PROVENANCE记录。未把矩阵、NetCDF、X/Pi/RC、许可证或凭据放入审阅ZIP/Git。

## 6. 交付与停止边界

证据级别：运行终态/交接/参数/资源/备份为真实回执验证；C03资产模式为复用已验收证据；唯一根因、原单位改善、完整LP可行性均未证明。诊断执行完成但科学验收NOT_ACCEPTED，Gate6 PASS=false。

保持现有科学输入、V3/V4、Scheme A及历史结论。后续唯一行动是用户与ChatGPT审阅本次结果后作出新的科学决策；**没有授权或执行第二个参数、更长预算、第二次optimize或其他情景**。G6-05暂停。实例不关机/释放，任务在GitHub和ZIP交付后停止。

逐文件证据见[C05_EVIDENCE_INDEX.json](C05_EVIDENCE_INDEX.json)；完整机器对照见[C05_BASELINE_RESULT_COMPARISON.json](C05_BASELINE_RESULT_COMPARISON.json)。实际最终提交、PR及审阅ZIP整体SHA由同轮发布/交付回执绑定，不能把生产代码提交误写成最终报告提交。
'''
(OUT/'C05_AGGREGATE0_DAILY_DIAGNOSTIC_RESULT.md').write_text(report,encoding='utf-8')

entry=f'''\n\n## C-05 单因素Aggregate=0真实诊断终态（2026-10-12）

**C05_NUMERIC_NO_SOLUTION_NOT_ACCEPTED；云端及本地保全完成。** 此项为用户后续明确授权，C04提议时的未授权状态与旧结果原件保留。

- 独立Run `{RUN}`；生产commit `{PRODUCTION}` 已push。复用C03现成日CSC，2,450,005列/6,042,238行/11,403,496非零；17,369输入SHA通过，构建0、CSR→CSC转换0。WLS原生启动和同模型完整EXACT_READBACK_PASS通过。
- 154项实际数值参数只有Aggregate 1→0；TimeLimit3600、SoftMemLimit65GB、MemLimit1e100不变。唯一调用返回码0、Status12 NUMERIC、SolCount0、24Barrier、81.595145秒。无重试；不是数学不可行/无界证明。
- 无合法完整X/Pi/RC；真实状态/质量属性/日志已先保存。日V4、377/111模式、4304 stationarity及365自由RC变化均NOT_AVAILABLE，不记零、不伪造PASS。没有新NetCDF解或合格双账成本。
- 固定总7200秒未延长；实际至封存guard退出{rs['total_to_seal_guard_exit_seconds']:.3f}秒。RSS采样{gib(rs['sampled_worker_tree_peak_rss_bytes'])}GiB，cgroup lifetime peak{gib(rs['cgroup_lifetime_peak_end_bytes'])}GiB，保护无触发，所有本次进程退出；122实例仍运行/计费。
- 云端新增32项封存；新独立60分钟窗口传输6.526404秒。394,606字节新归档SHA `{backup['archive_sha256']}`，大小/SHA/CRC/安全路径/逐项BACKUP_INDEX核验通过，LOCAL_BACKUP_SHA_VERIFIED。旧17,369项输入按不可变引用复用；历史LOCAL_SYNC_PENDING不覆盖。
- 报告、参数差异、完整条件验收状态和方法见 `research/05_baseline_evolution/20261011/c05/`。独立分支codex/c05-aggregate0-daily-20261012，关联PR #13/#14；真实结果commit/PR及同轮C05_AGGREGATE0_DAILY_DIAGNOSTIC_REVIEW.zip由发布回执记录。
- 科学结果NOT_ACCEPTED；不能进入2920/Integrated/Disconnected/DEC。G6-05保持PAUSED_BY_USER。用户本次唯一优化授权已消费；不自动改变第二个参数或再求解。交付后停止。
'''
for rel in ['research/05_baseline_evolution/20261011/BASELINE_EVOLUTION_LEDGER.md','research/STAGE2_PROJECT_LEDGER.md','research/05_baseline_evolution/20261011/b03_c00/C00_GO_NO_GO_CHECKLIST.md']:
    path=REPO/rel
    assert '## C-05 单因素Aggregate=0真实诊断终态' not in path.read_text()
    with path.open('a',encoding='utf-8') as f: f.write(entry)
    if path.name=='C00_GO_NO_GO_CHECKLIST.md':
        with path.open('a',encoding='utf-8') as f:
            f.write('\n当前GO/NO-GO：身份/交接/单因素/一次执行/状态保全/本地备份PASS；C05科学验收NOT_ACCEPTED_NO_SOLUTION；任何进一步优化NO-GO_NOT_AUTHORIZED。C03仍OPTIMAL_BUT_NOT_ACCEPTED。\n')

files=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file() and p.name!='C05_EVIDENCE_INDEX.json':
        assert p.suffix not in ('.npy','.nc','.npz','.so','.lic','.zip','.gz','.pyc')
        files.append({'relative':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':sha(p)})
dump(OUT/'C05_EVIDENCE_INDEX.json',{'production_commit':PRODUCTION,'run_id':RUN,'files':files,'self_excluded':True,'raw_originals_preserved':True})
print(json.dumps({'report':str(OUT/'C05_AGGREGATE0_DAILY_DIAGNOSTIC_RESULT.md'),'resource_summary':rs,'published_files':len(files)},ensure_ascii=False,indent=2))
