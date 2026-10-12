"""Receipt-grounded C06 publication. Uses authenticated partial-recovery analysis view; archive backup remains pending.
No solver, model construction, remote mutation or acceptance threshold edits.
"""
from pathlib import Path
import json,hashlib,re,shutil,subprocess,datetime,collections
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c06_barconvtol_20261012')
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
REL=Path('research/05_baseline_evolution/20261011/c06');O=R/REL
ROOT=Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
RID=read(W/'LAUNCH_RECEIPT.json')['run_id']
N=W/'analysis_view'
B=ROOT/'c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run'
F=ROOT/'c05_daily_diagnostic/c05_aggregate0_daily122_20261012T074925Z_a39647d9/cloud_run'
PRODUCTION='34a34b69ef752d7809487ca609cd91e12f75bffd'
assert subprocess.run(['git','-C',str(R),'merge-base','--is-ancestor',PRODUCTION,'HEAD']).returncode==0
assert subprocess.check_output(['git','-C',str(R),'branch','--show-current']).decode().strip()=='codex/c06-barconvtol-daily-20261012'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def cp(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
def utc(v):return datetime.datetime.fromtimestamp(v,datetime.timezone.utc).isoformat().replace('+00:00','Z')
def redact(s):return '\n'.join('[REDACTED: license registration metadata; raw original retained]' if 'Academic license ' in v else v for v in s.split('\n'))
def clean(v):
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
 if isinstance(v,list):return [clean(x) for x in v]
 return redact(v) if isinstance(v,str) else v
def logstats(p):
 text=p.read_text();rows=[]
 for line in text.splitlines():
  m=re.fullmatch(r'\s*(\d+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+(\d+)s\s*',line)
  if m:
   a=m.groups();rows.append(dict(iteration=int(a[0]),primal=float(a[1]),dual=float(a[2]),primal_residual=float(a[3]),dual_residual=float(a[4]),complementarity=float(a[5]),log_seconds=int(a[6])))
 def num(rx,typ=float):return typ(re.search(rx,text).group(1))
 ps=re.search(r'Presolved: (\d+) rows, (\d+) columns, (\d+) nonzeros',text)
 return dict(raw_log_sha256=sha(p),rounded_log_values=True,model_fingerprint=re.search(r'Model fingerprint: (\S+)',text).group(1),
  presolve_seconds=num(r'Presolve time: ([\d.]+)s'),presolved=dict(zip(['rows','columns','nnz'],map(int,ps.groups()))),
  ordering_seconds=num(r'Ordering time: ([\d.]+)s'),dense_columns=num(r'Dense cols\s*:\s*(\d+)',int),free_variables=num(r'Free vars\s*:\s*(\d+)',int),
  factor_nnz_approx=num(r'Factor NZ\s*:\s*([\d.eE+]+)'),iterations=rows,last_iteration=rows[-1],numerical_trouble='Numerical trouble encountered' in text)
raw={k:read(p/'raw/vectors/RAW_RECEIPT.json') for k,p in [('C03',B),('C05',F),('C06',N)]}
assert raw['C06']['native_status']==2 and raw['C06']['native_info']['SolCount']==1
assert read(N/'NATIVE_CALL_EXIT.json')['optimization_calls']==1
post=read(N/'postprocess/POSTPROCESS_RECEIPT.json');oldpost=read(B/'postprocess/POSTPROCESS_RECEIPT.json')
kk={k:read(p/'postprocess/KKT.json') for k,p in [('C03',B),('C06',N)]}
phys={k:read(p/'postprocess/PHYSICAL_CHECKS.json') for k,p in [('C03',B),('C06',N)]}
ap=read(W/'C06_ALL_ACCOUNT_AND_GROUP_COMPARISON.json');ks=read(W/'C06_KKT_FAILURE_SET_COMPARISON.json');mf=read(W/'C06_MATRIX_ROW_FAMILY_COMPARISON.json')
auth=read(N/'AUTHORIZATION.json');transfer=read(N/'NATIVE_TRANSFER.json');ent=read(N/'C06_NATIVE_OPTIMIZE_ENTERED.json')
execution_meta=read(N/'C06_EXECUTION_METADATA.json')
assert execution_meta['ObjCon']==read(B/'bridge/math_problem/MATH_PROBLEM.json')['offset'] and execution_meta['ModelSense']==1
assert transfer['native_model_handle']==ent['model_handle'] and transfer['status']=='EXACT_READBACK_PASS'
pa=read(N/'C06_C03_C05_PARAMETER_COMPARISON.json');assert pa['status']=='PASS'
resources=[json.loads(l) for l in (N/'RESOURCE.jsonl').read_text().splitlines() if l.strip()]
seal=read(W/'C06_ARCHIVE_SOURCE_IDENTITY.json');backup=read(W/'C06_FINAL_BACKUP_STATUS.json');trans={'seconds':None}
assert backup['status']=='LOCAL_SYNC_PENDING'
samples=resources+seal['seal_guard']['samples']
rs=dict(run_id=RID,source_sha256=sha(N/'RESOURCE.jsonl'),samples=len(resources),
 sampled_worker_tree_peak_rss_bytes=max(r['rss_bytes'] for r in resources),
 cgroup_lifetime_peak_start_bytes=resources[0]['cgroup'][0]['memory_peak'],
 cgroup_lifetime_peak_end_bytes=max(c['memory_peak'] for r in samples for c in r['cgroup']),
 cgroup_current_sample_peak_bytes=max(c['current'] for r in samples for c in r['cgroup']),
 minimum_cgroup_headroom_bytes=min(r['cgroup_headroom_bytes'] for r in samples),minimum_disk_free_bytes=min(r['disk_free_bytes'] for r in samples),
 memory_events_observed=sorted({c['memory_events'] for r in samples for c in r['cgroup']}),protection_reasons=[r['reason'] for r in samples if r['reason']],
 peak_semantics='RSS is sampled process-tree peak. Cgroup peak is lifetime/shared, not exclusive Gurobi peak.',
 start_epoch=auth['started_epoch'],start_utc=utc(auth['started_epoch']),native_runtime_seconds=raw['C06']['native_info']['Runtime'],
 load_readback_seconds=transfer['load_and_readback_seconds'],total_to_seal_guard_exit_seconds=seal['seal_guard']['ended_epoch']-auth['started_epoch'],
 deadlines={k:{'epoch':v,'UTC':utc(v),'from_t0_seconds':v-auth['started_epoch']} for k,v in auth.items() if 'deadline_epoch' in k},
 stage_budgets_seconds={'load':900,'native':3600,'exit_TERM':150,'raw':300,'post':1200,'seal':1050,'total':7200},
 separate_transfer_seconds=trans['seconds'],costs='Instance stays running and billing. No billing-based stop or new resource purchase.')
assert not rs['protection_reasons'] and rs['total_to_seal_guard_exit_seconds']<7200
assert rs['minimum_disk_free_bytes']>=8*2**30 and rs['minimum_cgroup_headroom_bytes']>=12*2**30
resource_comparison={}
for k,p in [('C03',B),('C05',F),('C06',N)]:
 rr=[json.loads(l) for l in (p/'RESOURCE.jsonl').read_text().splitlines() if l.strip()]
 entry=read(p/(k+'_NATIVE_OPTIMIZE_ENTERED.json'))['epoch'];end=read(p/'NATIVE_CALL_EXIT.json')['returned_utc_epoch']
 native=[v for v in rr if entry<=v['epoch']<=end];assert len(native)>1
 resource_comparison[k]=dict(source_sha256=sha(p/'RESOURCE.jsonl'),native_enter_epoch=entry,native_return_epoch=end,native_samples=len(native),
  native_sampled_worker_tree_RSS_peak_GiB=max(v['rss_bytes'] for v in native)/2**30,
  whole_production_sampled_RSS_peak_GiB=max(v['rss_bytes'] for v in rr)/2**30,
  native_cgroup_current_sample_peak_GiB=max(c['current'] for v in native for c in v['cgroup'])/2**30,
  native_min_cgroup_headroom_GiB=min(v['cgroup_headroom_bytes'] for v in native)/2**30,
  native_cpu_sample_interval_seconds=native[-1]['epoch']-native[0]['epoch'],
  native_cpu_seconds_delta=native[-1]['cpu_seconds']-native[0]['cpu_seconds'],
  native_average_CPU_cores=(native[-1]['cpu_seconds']-native[0]['cpu_seconds'])/(native[-1]['epoch']-native[0]['epoch']),
  caveat='Native interval uses actual enter/return epochs; sampled process tree includes parent overhead; whole C03 window also includes build and is not directly comparable.')
logs={k:logstats(p/'gurobi.log') for k,p in [('C03',B),('C05',F),('C06',N)]}
l3={v['iteration']:v for v in logs['C03']['iterations']};l6={v['iteration']:v for v in logs['C06']['iterations']}
traj=[i for i in sorted(set(l3)&set(l6)) if any(l3[i][k]!=l6[i][k] for k in ('primal','dual','primal_residual','dual_residual','complementarity'))]
trajectory=dict(common_log_iterations=len(set(l3)&set(l6)),differing_rounded_numeric_iterations=traj,exact_internal_path_equivalence='NOT_PROVEN; rounded log equality does not prove bitwise trajectory equality')
metrics={key:{'C03':kk['C03'][key],'C06':kk['C06'][key],'C05':None,'C05_qualification':'NOT_AVAILABLE_SOLCOUNT_ZERO'} for key in kk['C03'] if isinstance(kk['C03'][key],(int,float)) and not isinstance(kk['C03'][key],bool)}
for k in ('C03','C06'):
 Z=max(1,abs(kk[k]['primal_objective']),abs(kk[k]['dual_objective_numeric']))
 for field in ('complementarity_l1','stationarity_weighted_l1'):
  metrics.setdefault(field+'_normalized',{'C05':None,'C05_qualification':'NOT_AVAILABLE_SOLCOUNT_ZERO'})[k]=kk[k][field]/Z
comparison=dict(classification='C06_EXECUTION_ACCEPTED_SCIENCE_NOT_ACCEPTED',run_id=RID,baseline_run_id=raw['C03']['run_id'],production_commit=PRODUCTION,
 source_model_identity=read(N/'IMMUTABLE_INPUTS.json'),parameters=pa,native=raw,resources=resource_comparison,C03_daily_V4=oldpost,C06_daily_V4=post,
 C05_daily_V4={'status':'NOT_AVAILABLE_SOLCOUNT_ZERO','scientific_pass':False},all_metric_comparison=metrics,
 accounts_and_obligations={'totals':ap['totals'],'account_failure_sets':ap['account_failure_sets'],'group_failure_sets':ap['group_failure_sets'],'cardinality':ap['cardinality'],'complete_evidence':'evidence/C06_ALL_ACCOUNT_AND_GROUP_COMPARISON.json'},
 KKT_failure_sets={'stationarity_transition':ks['stationarity_transition'],'sign_transition':ks['sign_transition'],'current_families':ks['stationarity_families'],'complete_evidence':'evidence/C06_KKT_FAILURE_SET_COMPARISON.json'},
 all_current_matrix_row_families=mf,trajectory_comparison=trajectory,
 costs={k:read(p/'postprocess/DUAL_COST_LEDGER.json') for k,p in [('C03',B),('C06',N)]},
 costs_C05={'status':'NOT_AVAILABLE_SOLCOUNT_ZERO','scientific_cost':None},
 objective_constant_EUR=execution_meta['ObjCon'],native_ObjVal_vs_independent_V3_EUR=post['costs']['adapted_objective']-raw['C06']['native_info']['ObjVal'],backup=backup,
 interpretation={'verified':'Single BarConvTol change improved several physical/error-count metrics but did not satisfy complete V4.',
 'not_proven':['Unique root cause of remaining failures','All residuals improve by requested tolerance factor','Unperturbed objective optimality','Full-system cost completeness','2920-snapshot feasibility or Gate6 PASS'],
 'next_action':'STOP_FOR_USER_AND_CHATGPT_REVIEW; no further optimization authorized'})


# Independently compare actual parameter dictionaries, not only a production PASS.
parameter_tables={k:read(p/'EFFECTIVE_MODEL_PARAMETERS.json') for k,p in [('C03',B),('C05',F),('C06',N)]}
assert all(len(t)==154 for t in parameter_tables.values())
assert set(parameter_tables['C03'])==set(parameter_tables['C05'])==set(parameter_tables['C06'])
parameter_rows=[dict(parameter=k,**{run:t[k] for run,t in parameter_tables.items()}) for k in sorted(parameter_tables['C03'])]
assert [r['parameter'] for r in parameter_rows if r['C03']!=r['C06']]==['BarConvTol']
assert [r['parameter'] for r in parameter_rows if r['C05']!=r['C06']]==['Aggregate','BarConvTol']
comparison['actual_154_parameters']=parameter_rows
comparison['physical_engineering_checks']={k:phys[k]['checks'] for k in ('C03','C06')}
comparison['independent_exact_forensics']='evidence/C06_EXACT_LOCAL_FORENSICS.json'
comparison['group_pattern']='evidence/C06_GROUP_PATTERN_AND_FREE_RC.json'
for key,row in metrics.items():
 a,b=row['C03'],row['C06'];row['C06_minus_C03']=b-a;row['C06_over_C03']=b/a if a else None
 if any(v in key for v in ('violation','fail_count','stationarity','dual_sign','complementarity','gap')):
  row['direction']='NUMERICALLY_UNCHANGED' if a==b else 'IMPROVED_LOWER_ERROR' if b<a else 'WORSENED_HIGHER_ERROR'
 else:row['direction']='ACCOUNTING_VALUE_NOT_ACCEPTANCE_DIRECTION'
dump(W/'C03_C05_C06_METRIC_COMPARISON.json',comparison)
dump(W/'C06_LOG_TRAJECTORY_COMPARISON.json',dict(logs=logs,C03_vs_C06=trajectory))
dump(W/'C06_RESOURCE_AND_DEADLINE_SUMMARY.json',rs)
dump(W/'C06_C03_C05_RESOURCE_COMPARISON.json',resource_comparison)
print(json.dumps(dict(status=comparison['classification'],backup=backup['status'],same_rounded_common_iterations=trajectory)))
