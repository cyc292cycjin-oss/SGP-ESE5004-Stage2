"""Derive the C06 minimal entry changes from the SHA-verified C05 release."""
from pathlib import Path
import json,hashlib,shutil,subprocess,ast,tarfile,io
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c06_barconvtol_20261012')
OLD=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c05_aggregate0_20261012/release')
R=W/'release';R.mkdir(exist_ok=False)
REPO=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
BASE='54f23fdc7d78c3ef087806798b27d30369c6d961'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD']).decode().strip()==BASE
assert not subprocess.check_output(['git','-C',str(REPO),'status','--porcelain']).strip()
oldm=read(OLD/'C05_RELEASE_MANIFEST.json');reuse=[]
skip={'C05_AGGREGATE0_CONDITIONAL_CODEX_INSTRUCTION.md','C05_CODEX_START_AUTHORIZATION.txt','C05_APPROVAL_RECORD.json','C05_LOCAL_INTERFACE_TESTS.json'}
for rel,entry in oldm['files'].items():
 p=OLD/rel; assert p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256']
 gitbytes=subprocess.check_output(['git','-C',str(REPO),'show',BASE+':research/05_baseline_evolution/20261011/c05/release/'+rel]);assert hashlib.sha256(gitbytes).hexdigest()==sha(p)
 if rel in skip:continue
 out=R/rel.replace('c05_','c06_');out.parent.mkdir(parents=True,exist_ok=True)
 if rel.startswith('c05_'):out.write_text(p.read_text().replace('c05_','c06_').replace('C05','C06').replace('AGGREGATE0','BARCONVTOL').replace('aggregate0','barconvtol'))
 else:shutil.copyfile(p,out)
 reuse.append({'source':rel,'C05_sha256':sha(p),'C06_relative':str(out.relative_to(R))})

p=R/'c06_checks.py';s=p.read_text();lo=s.index('def parameter_diff(');hi=s.index('\ndef verify_release(',lo)
s=s[:lo]+'''def parameter_diff(base,actual,baseline='C03'):
    if baseline not in ('C03','C05'):raise ValueError('UNKNOWN_COMPARISON_BASE')
    if set(base)!=set(actual) or len(base)!=154:raise ValueError('154_PARAMETER_COVERAGE')
    rows=[];bad=[]
    for k,b in base.items():
        v=actual[k];changed=v!=b;kind='UNCHANGED'
        if changed:
            if k=='BarConvTol' and b==1e-6 and v==1e-9:kind='AUTHORIZED_BARRIER_TOLERANCE_CHANGE'
            elif baseline=='C05' and k=='Aggregate' and b==0 and v==1:kind='DISCLOSED_C05_TO_C03_BASELINE_RESTORATION'
            elif k=='TimeLimit' and 0<v<=3600 and v<=b:kind='AUTHORIZED_ABSOLUTE_DEADLINE_PROTECTION'
            else:kind='UNAUTHORIZED';bad.append(k)
        rows.append({'parameter':k,baseline:b,'C06':v,'changed':changed,'classification':kind})
    if actual['Aggregate']!=1 or base['Aggregate']!=(1 if baseline=='C03' else 0):bad.append('Aggregate_REQUIRED')
    if actual['BarConvTol']!=1e-9 or base['BarConvTol']!=1e-6:bad.append('BarConvTol_REQUIRED')
    return {'status':'FAIL' if bad else 'PASS_SINGLE_ALGORITHM_FACTOR' if baseline=='C03' else 'PASS_DISCLOSED_TWO_FACTOR_DIFFERENCE',
            'comparison_baseline':baseline,'count':len(rows),'unauthorized_differences':bad,'differences':[r for r in rows if r['changed']],'parameters':rows,'log_path_and_run_metadata':'not algorithm parameters'}

''' + s[hi:]
s=s.replace("names={'c06_native.py','c06_worker.py','c03_native.py'", "names={'c05_native.py','c05_worker.py','c06_native.py','c06_worker.py','c03_native.py'")
s=s.replace("assert sha(HERE/'V4_APPROVED.json')", "assert sha(HERE/'C05_EFFECTIVE_MODEL_PARAMETERS.json')=='349d8ca34cc5f0e882a368d8bd239bc590950a004cc94eddce3dbcac71b20c42'\n    assert sha(HERE/'V4_APPROVED.json')")
p.write_text(s)
p=R/'c06_launch.py';s=p.read_text().replace("'proposed_algorithm_override':{'Aggregate':0}","'proposed_algorithm_override':{'BarConvTol':1e-9},'C05_disclosed_changes':{'Aggregate':[0,1],'BarConvTol':[1e-6,1e-9]}")
p.write_text(s)
p=R/'c06_native.py';s=p.read_text().replace("expected=dict(read(HERE/'C03_EFFECTIVE_MODEL_PARAMETERS.json'),Aggregate=0)","expected=dict(read(HERE/'C03_EFFECTIVE_MODEL_PARAMETERS.json'),BarConvTol=1e-9)")
s=s.replace("'DualReductions','InfUnbdInfo'","'DualReductions','BarHomogeneous','InfUnbdInfo'")
needle="        assert diff['status']=='PASS_SINGLE_ALGORITHM_FACTOR'"
assert needle in s
s=s.replace(needle,needle+'''
        diff5=parameter_diff(read(HERE/'C05_EFFECTIVE_MODEL_PARAMETERS.json'),effective,baseline='C05')
        write(run/'C06_C05_PARAMETER_DIFF.json',diff5)
        combined={'status':'PASS' if diff['status']=='PASS_SINGLE_ALGORITHM_FACTOR' and diff5['status']=='PASS_DISCLOSED_TWO_FACTOR_DIFFERENCE' else 'FAIL','count':154,'C03_vs_C06':diff,'C05_vs_C06':diff5,'actual_parameters_sha256':sha(run/'EFFECTIVE_MODEL_PARAMETERS.json')}
        write(run/'C06_C03_C05_PARAMETER_COMPARISON.json',combined)
        assert combined['status']=='PASS'
        write(run/'C06_EXECUTION_METADATA.json',{'run_id':a['run_id'],'baseline_run_id':a['baseline_run_id'],'release':str(HERE),'log_path':str(run/'gurobi.log'),'input_manifest_sha256':transfer['model_manifest_sha256'],'model_handle':str(backend.model.value),'ModelSense':backend.scalar('ModelSense',int),'ObjCon':backend.scalar('ObjCon',float),'metadata_not_algorithm_parameters':True,'old_candidate_warm_start':False})''')
p.write_text(s)
c05params=Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/c05_daily_diagnostic/c05_aggregate0_daily122_20261012T074925Z_a39647d9/cloud_run/EFFECTIVE_MODEL_PARAMETERS.json')
shutil.copyfile(c05params,R/'C05_EFFECTIVE_MODEL_PARAMETERS.json')
for name in ['C06_BARCONVTOL_AUTHORIZED_CODEX_INSTRUCTION.md','C06_CODEX_START_AUTHORIZATION.txt']:
 shutil.copyfile(W/'submission'/name,R/name)
write(R/'C06_APPROVAL_RECORD.json',{'approved_by_user':True,'authority':'direct C06正式执行授权 in current conversation; attached pending proposal superseded','scope':'one new C06 BarConvTol=1e-9 versus C03; no model rebuild','max_optimize_calls':1,'maximum_native_seconds':3600,'maximum_production_seconds':7200,'separate_local_transfer_seconds':3600,'instruction_sha256':sha(R/'C06_BARCONVTOL_AUTHORIZED_CODEX_INSTRUCTION.md'),'start_authorization_sha256':sha(R/'C06_CODEX_START_AUTHORIZATION.txt'),'submission_manifest_sha256':sha(W/'submission/SUBMISSION_MANIFEST.json'),'original_C05_release_sha256':sha(OLD/'C05_RELEASE_MANIFEST.json'),'old_authorizations_preserved':True})

# Only changed parameter gates and wiring are tested here; no native API or solver.
tree=ast.parse((R/'c06_checks.py').read_text());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='parameter_diff')
ns={};exec(compile(ast.Module(body=[f],type_ignores=[]),'<isolated parameter gate>','exec'),ns);check=ns['parameter_diff']
base=read(R/'C03_EFFECTIVE_MODEL_PARAMETERS.json');base5=read(R/'C05_EFFECTIVE_MODEL_PARAMETERS.json');target=dict(base,BarConvTol=1e-9)
tests=[]
def test(name,ok):assert ok,name;tests.append({'test':name,'result':'PASS','kind':'NON_NATIVE_INTERFACE_ONLY'})
test('C03_only_BarConvTol',check(base,target)['status']=='PASS_SINGLE_ALGORITHM_FACTOR' and len(check(base,target)['differences'])==1)
test('C05_two_explicit_changes',check(base5,target,'C05')['status']=='PASS_DISCLOSED_TWO_FACTOR_DIFFERENCE' and len(check(base5,target,'C05')['differences'])==2)
test('C05_Aggregate0_leak_rejected',check(base,dict(target,Aggregate=0))['status']=='FAIL')
test('old_tolerance_rejected',check(base,base)['status']=='FAIL')
test('second_numeric_change_rejected',check(base,dict(target,NumericFocus=3))['status']=='FAIL')
test('TimeLimit_extension_rejected',check(base,dict(target,TimeLimit=3601))['status']=='FAIL')
try:check(base,{k:v for k,v in target.items() if k!='Seed'});raise AssertionError('missing accepted')
except ValueError:tests.append({'test':'missing_parameter_rejected','result':'PASS','kind':'NON_NATIVE_INTERFACE_ONLY'})
nt=ast.parse((R/'c06_native.py').read_text())
calls=[n for n in ast.walk(nt) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='GRBoptimize']
test('one_optimize_site_and_C03_parameter_source',len(calls)==1 and "expected=dict(read(HERE/'C03_EFFECTIVE_MODEL_PARAMETERS.json'),BarConvTol=1e-9)" in (R/'c06_native.py').read_text())
test('inherited_acceptance_and_protection_unchanged',all(sha(OLD/n)==sha(R/n) for n in ['production_control.py','daily_acceptance.py','daily_physics.py','basis_free.py','adapter.py','V4_APPROVED.json','SOURCE_BINDING.json']))
for p in R.rglob('*.py'):compile(p.read_text(),str(p),'exec')
write(R/'C06_LOCAL_INTERFACE_TESTS.json',{'status':'PASS','test_count':len(tests),'tests':tests,'native_calls':0,'solver_calls':0,'matrix_loads':0,'model_builds':0,'not_repeated':'old engineering and full science tests','requires_actual_execution':['WLS','all154 native parameters','exact CSC readback','one actual solve','legal vectors and complete V4 conditional branch']})
for row in reuse:
 row['C06_sha256']=sha(R/row['C06_relative']);row['unchanged']=row['C05_sha256']==row['C06_sha256']
write(R/'C05_MODULE_REUSE.json',{'parent_production_commit':'d6c48dbd95d12f0354561372e9a65d6e92511754','verified_git_commit':BASE,'files':reuse,'changes':'five c06 entry modules: namespace, run/claim identities, C03 BarConvTol override and dual parameter comparison; inherited protection/acceptance/mapping unchanged'})
files={str(p.relative_to(R)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(R.rglob('*')) if p.is_file()}
write(R/'C06_RELEASE_MANIFEST.json',{'release_id':'C06_BARCONVTOL_FROZEN_CSC_V1','parent_production_commit':'d6c48dbd95d12f0354561372e9a65d6e92511754','audit_base_commit':BASE,'scope':'SINGLE_DAILY_DIAGNOSTIC_NO_BUILD','files':files})
msha=sha(R/'C06_RELEASE_MANIFEST.json');remote='/root/autodl-tmp/SGP/incoming/c06_barconvtol_122_20261012_'+msha[:8]
arc=W/'C06_RELEASE.tar.gz'
with tarfile.open(arc,'x:gz',compresslevel=6) as t:
 for p in sorted(R.rglob('*')):
  if p.is_file():t.add(p,arcname='release/'+str(p.relative_to(R)),recursive=False)
write(W/'RELEASE_DELIVERY.json',{'archive':str(arc),'archive_bytes':arc.stat().st_size,'archive_sha256':sha(arc),'release_manifest_sha256':msha,'remote_control':remote,'remote_release':remote+'/release','payload_files':len(files)+1,'native_calls':0})
print(json.dumps({'tests':len(tests),'manifest_sha256':msha,'files':len(files)+1,'payload_bytes':arc.stat().st_size,'remote_control':remote}))
