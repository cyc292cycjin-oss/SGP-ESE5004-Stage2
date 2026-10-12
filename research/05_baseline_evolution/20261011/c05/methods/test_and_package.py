"""C05-only interface tests and explicit release freeze. Never calls native API."""
from pathlib import Path
import sys,json,hashlib,ast,ctypes as C,tempfile,tarfile,subprocess
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c05_aggregate0_20261012');R=W/'release'
sys.path.insert(0,str(R));sys.path.insert(0,str(R/'helpers'))
from c05_checks import parameter_diff
from c05_native import parameters
from production_control import phase_deadline,stop_blocks_stage
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
base=read(R/'C03_EFFECTIVE_MODEL_PARAMETERS.json');types=read(R/'NATIVE_PARAMETER_EVIDENCE.json')['parameters']
tests=[]
def passed(name):tests.append({'test':name,'result':'PASS','kind':'NON_NATIVE_INTERFACE_LOGIC'})
class Fake:
    def __init__(self):self.values=dict(base)
    def GRBsetintparam(self,env,key,value):self.values[key.decode()]=value;return 0
    GRBsetdblparam=GRBsetintparam
    def GRBgetintparam(self,env,key,p):C.cast(p,C.POINTER(C.c_int))[0]=int(self.values[key.decode()]);return 0
    def GRBgetdblparam(self,env,key,p):C.cast(p,C.POINTER(C.c_double))[0]=float(self.values[key.decode()]);return 0
lib=Fake();v=parameters(lib,None,dict(base,Aggregate=0),types,3600.,apply=True)
d=parameter_diff(base,v);assert d['status']=='PASS_SINGLE_ALGORITHM_FACTOR' and [x['parameter'] for x in d['differences']]==['Aggregate'];passed('154_parameters_only_Aggregate_change')
assert parameter_diff(base,dict(v,NumericFocus=1))['status']=='FAIL';passed('second_algorithm_change_rejected')
assert parameter_diff(base,dict(v,TSPort=base['TSPort']+1))['status']=='FAIL';passed('unexpected_runtime_numeric_parameter_rejected')
assert parameter_diff(base,dict(v,TimeLimit=3599.))['status']=='PASS_SINGLE_ALGORITHM_FACTOR';passed('authorized_deadline_reduction_classified')
assert parameter_diff(base,dict(v,TimeLimit=3601.))['status']=='FAIL';passed('TimeLimit_extension_rejected')
try:parameter_diff(base,{k:x for k,x in v.items() if k!='Method'})
except ValueError:passed('missing_parameter_rejected')
else:raise AssertionError('missing parameter admitted')
a={'load_absolute_deadline_epoch':900,'native_absolute_deadline_epoch':4500,'raw_absolute_deadline_epoch':4950,'post_absolute_deadline_epoch':6150,'absolute_deadline_epoch':7200}
for phase,start,want in [('BRIDGE',100,900),('NATIVE',1000,4500),('RAW_SAVE',2000,2300),('RAW_SAVE',4800,4950),('POSTPROCESS',3000,4200),('POSTPROCESS',6000,6150)]:
 assert phase_deadline({'phase':phase,'entered_epoch':start},a)==want
passed('phase_duration_and_absolute_cutoff_minimum')
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'source').mkdir();(p/'source/a').write_text('immutable');(p/'run').mkdir();(p/'run/link').symlink_to(p/'source',target_is_directory=True)
 assert [x.name for x in (p/'run').rglob('*')]==['link'];passed('seal_rglob_does_not_follow_immutable_directory_links')
 (p/'run/raw').mkdir();(p/'run/STOP_REQUEST.json').write_text(json.dumps({'reason':'PHASE_DEADLINE_NATIVE'}))
 assert stop_blocks_stage(p/'run','POSTPROCESS')
 (p/'run/NATIVE_CALL_EXIT.json').write_text('{}');(p/'run/raw/RAW_DURABLE.json').write_text('{"complete": true}')
 assert not stop_blocks_stage(p/'run','POSTPROCESS') and stop_blocks_stage(p/'run','BRIDGE')
 (p/'run/STOP_REQUEST.json').write_text('{"reason": "CGROUP"}');assert stop_blocks_stage(p/'run','POSTPROCESS')
 passed('only_native_deadline_after_complete_raw_allows_bounded_V4_not_resource_stop')
for p in R.rglob('*.py'):ast.parse(p.read_text())
for name in ['c05_worker.py','c05_launch.py']:
 tree=ast.parse((R/name).read_text());calls=[getattr(n.func,'attr','') for n in ast.walk(tree) if isinstance(n,ast.Call)]
 assert not set(calls)&{'optimize','solve','solve_model','create_model','presolve','computeIIS','feasRelax'}
 assert 'c02r_build.py' not in (R/name).read_text()
passed('dispatcher_no_model_build_or_solver_entry')
tree=ast.parse((R/'c05_native.py').read_text());calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='GRBoptimize'];assert len(calls)==1
assert not (R/'c03_native.py').exists() and not (R/'combined_launch.py').exists();passed('one_native_optimize_call_site_no_historical_launcher')
reuse=read(R/'C03_MODULE_REUSE.json')
for f in reuse['files']:assert sha(R/f['relative'])==f.get('derived_sha256',f['sha256'])
passed('inherited_mapping_V4_SHA_unchanged_control_patch_explicit')
result={'status':'PASS','tests':tests,'test_count':len(tests),'native_API_calls':0,'solver_calls':0,'new_model_builds':0,'full_CSC_loads':0,'scientific_acceptance':'NOT_RUN','requires_live_run':['WLS','native_version','154 real parameters','exact same-model readback','real returned vector science checks']}
(R/'C05_LOCAL_INTERFACE_TESTS.json').write_text(json.dumps(result,indent=2)+'\n')
# Exclude transient import caches. Freeze exact explicit payload file list.
files={str(p.relative_to(R)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(R.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='C05_RELEASE_MANIFEST.json'}
m={'release_id':'C05_AGGREGATE0_FROZEN_CSC_V1','parent_production_commit':reuse['production_commit'],'audit_base_commit':reuse['C04_delivery_commit'],'scope':'SINGLE_DAILY_DIAGNOSTIC_NO_BUILD','files':files,'max_optimize_calls':1,'immutable_data_copied':False,'no_warm_start':True}
(R/'C05_RELEASE_MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
release_sha=sha(R/'C05_RELEASE_MANIFEST.json');remote='/root/autodl-tmp/SGP/incoming/c05_aggregate0_122_20261012_'+release_sha[:8]
with tarfile.open(W/'C05_RELEASE.tar.gz','x:gz') as t:
 for rel in [*files,'C05_RELEASE_MANIFEST.json']:t.add(R/rel,arcname='release/'+rel,recursive=False)
delivery={'remote_control':remote,'remote_release':remote+'/release','release_manifest_sha256':release_sha,'archive_sha256':sha(W/'C05_RELEASE.tar.gz'),'archive_bytes':(W/'C05_RELEASE.tar.gz').stat().st_size,'payload_files':len(files)+1,'local_tests':result['test_count']}
(W/'RELEASE_DELIVERY.json').write_text(json.dumps(delivery,indent=2)+'\n')
print(json.dumps(delivery,indent=2))
