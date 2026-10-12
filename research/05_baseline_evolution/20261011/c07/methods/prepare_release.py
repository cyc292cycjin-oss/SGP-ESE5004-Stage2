"""Minimal C07 expression/coordinate adaptation of verified C06 production."""
from pathlib import Path
import json,hashlib,shutil,ast,subprocess,tarfile
W=Path(__file__).resolve().parent;OLD=W.parent/'c06_barconvtol_20261012/release';R=W/'release'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def replace(s,a,b):assert a in s,a;return s.replace(a,b)
def main():
 R.mkdir(exist_ok=False);m=read(OLD/'C06_RELEASE_MANIFEST.json');reuse=[]
 skip={'C06_APPROVAL_RECORD.json','C06_BARCONVTOL_AUTHORIZED_CODEX_INSTRUCTION.md','C06_CODEX_START_AUTHORIZATION.txt','C06_LOCAL_INTERFACE_TESTS.json'}
 for rel,r in m['files'].items():
  src=OLD/rel;assert sha(src)==r['sha256'] and src.stat().st_size==r['bytes']
  if rel in skip:continue
  dest=R/rel.replace('c06_','c07_');dest.parent.mkdir(exist_ok=True,parents=True)
  if rel.startswith('c06_'):dest.write_text(src.read_text().replace('c06_','c07_').replace('C06','C07').replace('BARCONVTOL','V4_RELIABILITY').replace('barconvtol','v4_reliability'))
  else:shutil.copyfile(src,dest)
  reuse.append({'source':rel,'C06_sha256':sha(src),'C07_relative':str(dest.relative_to(R))})
 shutil.copytree(W/'expression',R/'expression',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 shutil.copyfile(W/'C07_V4_APPLICABILITY.json',R/'C07_V4_APPLICABILITY.json')
 shutil.copyfile(W/'C07_EXPRESSION_STATIC_CHECK.json',R/'C07_EXPRESSION_STATIC_CHECK.json')
 shutil.copyfile(W.parent/'c06_barconvtol_20261012/analysis_view/EFFECTIVE_MODEL_PARAMETERS.json',R/'C06_EFFECTIVE_MODEL_PARAMETERS.json')
 p=R/'c07_checks.py';s=p.read_text();lo=s.index('def parameter_diff(');hi=s.index('\ndef verify_release(',lo)
 s=s[:lo]+'''def parameter_diff(base,actual,variant='A'):
    assert variant in ('A','B')
    if set(base)!=set(actual) or len(base)!=154:raise ValueError('154_PARAMETER_COVERAGE')
    rows=[];bad=[]
    for k,b in base.items():
        v=actual[k];kind='UNCHANGED'
        if v!=b:
            if k=='Crossover' and variant=='B' and b==0 and v==-1:kind='AUTHORIZED_CONDITIONAL_CROSSOVER'
            elif k=='TimeLimit' and 0<v<=min(3600,b):kind='FIXED_DEADLINE_PROTECTION'
            else:kind='UNAUTHORIZED';bad.append(k)
        rows.append({'parameter':k,'C06':b,'C07':v,'classification':kind})
    if actual['Crossover']!=(0 if variant=='A' else -1):bad.append('Crossover')
    if actual['Aggregate']!=1 or actual['BarConvTol']!=1e-9:bad.append('frozen_base')
    return {'status':'PASS' if not bad else 'FAIL','count':154,'variant':variant,'unauthorized':bad,'differences':[x for x in rows if x['classification']!='UNCHANGED'],'parameters':rows}

def conditional_b_gate(parent):
    from production_control import alive
    parent=Path(parent);a=read(parent/'AUTHORIZATION.json');assert a['variant']=='A'
    assert read(parent/'NATIVE_CALL_EXIT.json')['optimization_calls']==1 and read(parent/'NATIVE_CALL_EXIT.json')['native_return_code']==0
    raw=read(parent/'raw/vectors/RAW_RECEIPT.json');assert raw['native_status']==2 and raw['native_info']['SolCount']>0
    assert all(raw['vectors'][k]['status']=='SAVED_UNQUALIFIED' for k in ('X','Pi','RC'))
    assert read(parent/'NATIVE_TRANSFER.json')['status']=='EXACT_READBACK_PASS'
    assert read(parent/'C07_PARAMETER_DIFF.json')['status']=='PASS'
    assert read(parent/'C07_CANONICAL_MAPPING.json')['status']=='PASS'
    assert read(parent/'EXPRESSION_HASH_VERIFICATION.json')['status']=='PASS'
    post=read(parent/'postprocess/POSTPROCESS_RECEIPT.json');g=post['gates']
    assert not all(g.values()),'A_PASSED_B_FORBIDDEN'
    allowed={'full_matrix_and_column_bounds','independent_KKT','physical_dynamics','807_inventory','385_obligations'}
    failed={k for k,v in g.items() if v is not True};assert failed and failed<=allowed
    assert not (parent/'STOP_REQUEST.json').exists() and not (parent/'WORKER_FAILURE.json').exists()
    assert read(parent/'CLOUD_SEAL_COMPLETE.json')['run_id']==parent.name
    assert not read(parent/'GUARD_EXIT.json')['residual_live_pids']
    for name in ('PROCESS_IDENTITY.json','GUARD_READY.json'):assert not alive(read(parent/name))
    return {'status':'CONDITIONAL_B_AUTHORIZED_BY_ORIGINAL_USER_RULE','parent_run':parent.name,'failed_numerical_gates':sorted(failed),'parent_seal_sha256':sha(parent/'CLOUD_SEAL_COMPLETE.json')}
''' + s[hi:]
 s=s.replace("IDENTITY='C07_V4_RELIABILITY_DAILY122_USER_20261012_V1'","IDENTITY='C07_V4_RELIABILITY_DAILY122_USER_20261013_V1'")
 s=replace(s,"assert read(HERE/'C07_LOCAL_INTERFACE_TESTS.json')['status']=='PASS'","assert read(HERE/'C07_LOCAL_INTERFACE_TESTS.json')['status']=='PASS'\n    assert sha(HERE/'C06_EFFECTIVE_MODEL_PARAMETERS.json')=='f2f4bc219e3757dff6deda9035d67464e86e96e8ee9186427d2e27aced112f3c'\n    assert read(HERE/'C07_V4_APPLICABILITY.json')['scientific_decision_required'] is False")
 s=s.replace("names={'c05_native.py','c05_worker.py','c07_native.py','c07_worker.py'","names={'c05_native.py','c05_worker.py','c06_native.py','c06_worker.py','c07_native.py','c07_worker.py'")
 s=s.replace("    return s\n","    import shutil\n    shutil.copytree(HERE/'expression',run/'expression')\n    assert sha(run/'expression/C07_EXPRESSION_BINDING.json')==read(run/'AUTHORIZATION.json')['expression_sha256']\n    return s\n")
 p.write_text(s)
 # The only acceptance modification is an explicit raw-directory argument.
 p=R/'daily_acceptance.py';s=p.read_text();s=replace(s,'def postprocess(run,release,progress=lambda s:None):','def postprocess(run,release,progress=lambda s:None,raw_directory=None):')
 s=replace(s,"raw=run/'raw/vectors';rec=read(raw/'RAW_RECEIPT.json')","raw=Path(raw_directory) if raw_directory is not None else run/'raw/vectors';rec=read(raw/'RAW_RECEIPT.json')")
 p.write_text(s)
 p=R/'c07_worker.py';s=p.read_text();s=replace(s,'            postprocess(run,HERE,progress)', '''            from c07_expression_runtime import canonicalize
            canonical=canonicalize(run,a,progress)
            postprocess(run,HERE,progress,raw_directory=canonical/'vectors')''');p.write_text(s)
 p=R/'c07_native.py';s=p.read_text();s=replace(s,"expected=dict(read(HERE/'C03_EFFECTIVE_MODEL_PARAMETERS.json'),BarConvTol=1e-9)","expected=dict(read(HERE/'C06_EFFECTIVE_MODEL_PARAMETERS.json'),Crossover=0 if a['variant']=='A' else -1)")
 s=replace(s,"meta,arrays=open_problem(run/'bridge/math_problem',verify=True)","meta,arrays=open_problem(run/'bridge/math_problem',verify=True)\n        from c07_expression_runtime import expression_arrays\n        meta,arrays=expression_arrays(run,meta,arrays)")
 lo=s.index('        from c07_checks import parameter_diff');hi=s.index('        from c02_common import resource_gate',lo)
 s=s[:lo]+'''        from c07_checks import parameter_diff
        diff=parameter_diff(read(HERE/'C06_EFFECTIVE_MODEL_PARAMETERS.json'),effective,a['variant'])
        write(run/'C07_PARAMETER_DIFF.json',diff);assert diff['status']=='PASS'
        write(run/'C07_EXECUTION_METADATA.json',{'run_id':a['run_id'],'variant':a['variant'],'source_model_manifest_sha256':transfer['model_manifest_sha256'],'expression_sha256':a['expression_sha256'],'model_handle':str(backend.model.value),'ModelSense':backend.scalar('ModelSense',int),'ObjCon':backend.scalar('ObjCon',float),'old_candidate_warm_start':False})
''' +s[hi:]
 s=s.replace("'model_manifest_sha256':sha(run/'bridge/math_problem/MATH_PROBLEM.json'),'native_status'","'source_model_manifest_sha256':sha(run/'bridge/math_problem/MATH_PROBLEM.json'),'expression_sha256':authorization['expression_sha256'],'native_coordinate_space':'C07_NEW_D_R','native_status'")
 s=replace(s,"transfer.update(run_id=a['run_id'],","transfer.update(expression_sha256=a['expression_sha256'],input_space='C07_NEW_D_R',run_id=a['run_id'],")
 p.write_text(s)
 p=R/'c07_launch.py';s=p.read_text();s=replace(s,'def start(expected):','def start(expected,variant,parent=None):')
 s=replace(s,'    verify_release(expected);early=admission()',"    assert variant in ('A','B')\n    verify_release(expected);early=admission()\n    from c07_checks import conditional_b_gate\n    gate=conditional_b_gate(parent) if variant=='B' else None")
 s=s.replace("(IDENTITY+'_INTENT.json')","(IDENTITY+'_'+variant+'_INTENT.json')").replace("(IDENTITY+'_OPTIMIZE_CONSUMED.json')","(IDENTITY+'_'+variant+'_OPTIMIZE_CONSUMED.json')")
 s=s.replace("glob('c07_v4_reliability_daily122_*')","glob('c07'+variant.lower()+'_daily122_*')")
 s=s.replace("rid='c07_v4_reliability_daily122_'","rid='c07'+variant.lower()+'_daily122_'")
 s=replace(s,"    from production_control import limits_valid","    a.update(variant=variant,conditional_parent_run=parent,conditional_gate=gate,expression_sha256=sha(HERE/'expression/C07_EXPRESSION_BINDING.json'),proposed_algorithm_override={} if variant=='A' else {'Crossover':-1},comparison_baseline_run='c06_barconvtol_daily122_20261012T095705Z_321aa0f1')\n    a.pop('C05_disclosed_changes',None)\n    from production_control import limits_valid")
 s=replace(s,"if len(sys.argv)==3 and sys.argv[1]=='start':start(sys.argv[2])","if len(sys.argv) in (4,5) and sys.argv[1]=='start':start(sys.argv[2],sys.argv[3],sys.argv[4] if len(sys.argv)==5 else None)")
 p.write_text(s)
 shutil.copyfile(W/'c07_expression_runtime.py',R/'c07_expression_runtime.py')
 for n in ['C07_V4_RELIABILITY_EXECUTION_INSTRUCTION.md','C07_START_AUTHORIZATION.txt']:shutil.copyfile(W/'submission'/n,R/n)
 write(R/'C07_APPROVAL_RECORD.json',{'approved_by_user':True,'authority':'Direct C07 new execution confirmation, not C06 authorization reuse','instruction_sha256':sha(R/'C07_V4_RELIABILITY_EXECUTION_INSTRUCTION.md'),'max_optimize_calls_total':2,'sequential':'A; B only gated original OPTIMAL+complete+numerical V4 failure','per_run_native_seconds':3600,'per_run_total_seconds':7200,'V4_changed':False,'scientific_model_changed':False,'G6_05':'PAUSED_BY_USER'})
 # AST and isolated non-native parameter gate tests only, no solver import.
 tests=[];tree=ast.parse((R/'c07_checks.py').read_text());func=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='parameter_diff');ns={};exec(compile(ast.Module(body=[func],type_ignores=[]),'<parameter gate>','exec'),ns);check=ns['parameter_diff'];base=read(R/'C06_EFFECTIVE_MODEL_PARAMETERS.json')
 for name,ok in [('A_no_algorithm_change',check(base,base,'A')['status']=='PASS'),('B_only_crossover',check(base,dict(base,Crossover=-1),'B')['status']=='PASS'),('Aggregate0_reject',check(base,dict(base,Aggregate=0),'A')['status']=='FAIL'),('unauthorized_BarConvTol_reject',check(base,dict(base,BarConvTol=1e-10),'A')['status']=='FAIL'),('A_crossover_reject',check(base,dict(base,Crossover=-1),'A')['status']=='FAIL'),('time_extension_reject',check(base,dict(base,TimeLimit=3601),'A')['status']=='FAIL')]:
  assert ok,name;tests.append({'test':name,'status':'PASS'})
 nt=ast.parse((R/'c07_native.py').read_text());assert sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='GRBoptimize' for n in ast.walk(nt))==1
 unchanged=['production_control.py','adapter.py','basis_free.py','daily_physics.py','validation_dynamics.py','helpers/fixed_resource_acceptance.py','helpers/v4_algebra_extracted.py','V4_APPROVED.json','SOURCE_BINDING.json','license_binding.py']
 assert all(sha(R/n)==sha(OLD/n) for n in unchanged)
 for p in R.rglob('*.py'):compile(p.read_text(),str(p),'exec')
 write(R/'C07_LOCAL_INTERFACE_TESTS.json',{'status':'PASS','tests':tests,'one_optimize_call_site':True,'unchanged_scientific_and_protection_files':{n:sha(R/n) for n in unchanged},'native_calls':0,'remaining':'real WLS/native transfer/parameters/legal return/V4'})
 for r in reuse:r['C07_sha256']=sha(R/r['C07_relative']);r['unchanged']=r['C07_sha256']==r['C06_sha256']
 write(R/'C06_MODULE_REUSE.json',{'parent_git_commit':'6df356d2da4957c58d964fbd222bc5e1664db450','parent_manifest_sha256':sha(OLD/'C06_RELEASE_MANIFEST.json'),'files':reuse,'acceptance_change':'raw_directory parameter only, formal formulas and gates unchanged'})
 files={str(p.relative_to(R)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(R.rglob('*')) if p.is_file()}
 write(R/'C07_RELEASE_MANIFEST.json',{'release_id':'C07_V4_RELIABILITY_DAILY_V1','files':files,'expression_sha256':sha(R/'expression/C07_EXPRESSION_BINDING.json')})
 mh=sha(R/'C07_RELEASE_MANIFEST.json');remote='/root/autodl-tmp/SGP/incoming/c07_v4_reliability_122_20261013_'+mh[:8];arc=W/'C07_RELEASE.tar.gz'
 with tarfile.open(arc,'x:gz',compresslevel=6) as t:
  for p in sorted(R.rglob('*')):
   if p.is_file():t.add(p,arcname='release/'+str(p.relative_to(R)),recursive=False)
 write(W/'RELEASE_DELIVERY.json',{'archive':str(arc),'archive_bytes':arc.stat().st_size,'archive_sha256':sha(arc),'release_manifest_sha256':mh,'remote_control':remote,'remote_release':remote+'/release','payload_files':len(files)+1,'max_optimize_calls':2})
 print(json.dumps({'manifest_sha256':mh,'archive_bytes':arc.stat().st_size,'files':len(files)+1}))
if __name__=='__main__':main()
