"""Assemble minimal C05 wrapper around exact C03 production modules; no solver."""
from pathlib import Path
import json,hashlib,shutil,subprocess,ast
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c05_aggregate0_20261012')
OLD=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c02r_c03_combined_20261012/release')
B=Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run')
REPO=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
DEST=W/'release';DEST.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def out(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
orig=read(OLD/'C03_RELEASE_MANIFEST.json')
assert sha(OLD/'C03_RELEASE_MANIFEST.json')=='13a5b85ece564eaa4d9f5d554e454b5b68c714bc839a9ae7ecc5a913733f32fe'
for rel,r in orig['files'].items():assert sha(OLD/rel)==r['sha256'] and (OLD/rel).stat().st_size==r['bytes'],rel
names=['adapter.py','author_objective.py','basis_free.py','c02_common.py','daily_acceptance.py','daily_physics.py','license_binding.py','production_control.py','scatter.py','validation_dynamics.py','V4_APPROVED.json','LOCAL_INTERFACE_TESTS.json','NATIVE_PARAMETER_EVIDENCE.json','helpers/assembly_components.py','helpers/carrier_architecture.py','helpers/fixed_account_scope.py','helpers/fixed_accounts.py','helpers/fixed_resource_acceptance.py','helpers/v4_algebra_extracted.py']
parents=[]
for rel in names:
 p=OLD/rel;q=DEST/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 if p.suffix=='.py':
  blob=subprocess.check_output(['git','-C',str(REPO),'show','a3c1f5e97e03b99f4fa5fa885f6fe0747768d7d7:research/05_baseline_evolution/20261011/c02r_c03/code/'+rel]);assert hashlib.sha256(blob).hexdigest()==sha(p),rel
 parents.append({'relative':rel,'sha256':sha(p),'role':'EXACT_C03_REUSE'})
for name in ['C05_AGGREGATE0_CONDITIONAL_CODEX_INSTRUCTION.md','C05_CODEX_START_AUTHORIZATION.txt']:
 p=Path('/mnt/c/Users/20122/Desktop/10.11')/name;shutil.copyfile(p,DEST/name)
shutil.copyfile(B/'EFFECTIVE_MODEL_PARAMETERS.json',DEST/'C03_EFFECTIVE_MODEL_PARAMETERS.json')
assert sha(DEST/'C03_EFFECTIVE_MODEL_PARAMETERS.json')=='9514025d6234626f26d0f7dca7f9cf8070de4d24360a64429edbed790b9432a2'
assert len(read(DEST/'C03_EFFECTIVE_MODEL_PARAMETERS.json'))==154
idx=read(B/'BACKUP_INDEX.json');assert sha(B/'BACKUP_INDEX.json')=='eb80de5b50ff64d976d23066c514811fcc4f80f9b768f62ade1b6e1b4282d47d'
refs=[r for r in idx['files'] if r['relative'].startswith(('artifacts/','bridge/'))]
core=['BUILD_RESULT.json','bridge/BRIDGE_RECEIPT.json','bridge/math_problem/MATH_PROBLEM.json','bridge/math_problem/cost.npy','bridge/mapping/MAPPING_MANIFEST.json','artifacts/DAILY_V4_BINDING.json','artifacts/daily_365_unsolved.nc','artifacts/lp/MATH_PROBLEM.json','artifacts/mapping/LABELS.json']
out(DEST/'SOURCE_BINDING.json',{'baseline_run_id':'c02r_c03_daily122_20261012T044259Z_25e62c10','baseline_path':'/root/autodl-tmp/SGP/runs/c02r_c03_daily122_20261012T044259Z_25e62c10','baseline_BACKUP_INDEX_sha256':sha(B/'BACKUP_INDEX.json'),'baseline_parameters_sha256':sha(B/'EFFECTIVE_MODEL_PARAMETERS.json'),'core':{s:sha(B/s) for s in core},'files':refs,'file_count':len(refs),'bytes':sum(r['bytes'] for r in refs),'use':'read-only immutable references; not copied or rebuilt'})
out(DEST/'C05_APPROVAL_RECORD.json',{'scope':'C05_AGGREGATE0_SINGLE_DAILY_DIAGNOSTIC','approved_by_user':True,'basis':'Explicit C-05 formal execution authorization in current conversation; supersedes template pending status only','algorithm_override':{'Aggregate':0},'max_optimize_calls':1,'native_seconds_max':3600,'total_seconds_max':7200,'new_local_transfer_seconds_max':3600,'no_new_model_build':True,'no_retry':True,'preserve_old_records':True,'G6_05':'PAUSED_BY_USER','attachments':{s:sha(DEST/s) for s in ['C05_AGGREGATE0_CONDITIONAL_CODEX_INSTRUCTION.md','C05_CODEX_START_AUTHORIZATION.txt']}})
out(DEST/'C03_MODULE_REUSE.json',{'production_commit':'a3c1f5e97e03b99f4fa5fa885f6fe0747768d7d7','C04_delivery_commit':'4b76dc65662faef61ff429d3a299cc7db8bccd9b','baseline_release_manifest_sha256':sha(OLD/'C03_RELEASE_MANIFEST.json'),'files':parents})
s=(OLD/'c03_native.py').read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
replace("'C02R_C03_CONDITIONAL_SINGLE_DAILY_DIAGNOSTIC'","'C05_AGGREGATE0_SINGLE_DAILY_DIAGNOSTIC'")
replace("read(HERE/'FIRST_RUN_EFFECTIVE_MODEL_PARAMETERS.json')","dict(read(HERE/'C03_EFFECTIVE_MODEL_PARAMETERS.json'),Aggregate=0)")
replace("stage(run,'NATIVE');native_start=time.time()","stage(run,'NATIVE');native_start=time.time()")
replace("C03_NATIVE_OPTIMIZE_ENTERED.json","C05_NATIVE_OPTIMIZE_ENTERED.json")
replace("c03_native.main:lib.GRBoptimize(backend.model)","c05_native.main:lib.GRBoptimize(backend.model)")
replace("bind_license();lib=C.CDLL(str(dll));bind(lib);ok(lib.GRBemptyenv(C.byref(env)))","bind_license();lib=C.CDLL(str(dll));bind(lib)\n        lib.GRBversion.argtypes=[C.POINTER(C.c_int)]*3;lib.GRBversion.restype=None\n        vv=[C.c_int() for _ in range(3)];lib.GRBversion(*[C.byref(x) for x in vv]);assert [x.value for x in vv]==[12,0,3]\n        write(run/'NATIVE_VERSION.json',{'version':[x.value for x in vv],'library_sha256':sha(dll)})\n        ok(lib.GRBemptyenv(C.byref(env)))")
replace("write(run/'NATIVE_TRANSFER.json',transfer);write(run/'EFFECTIVE_MODEL_PARAMETERS.json',effective)","write(run/'NATIVE_TRANSFER.json',transfer);write(run/'EFFECTIVE_MODEL_PARAMETERS.json',effective)\n        from c05_checks import parameter_diff\n        diff=parameter_diff(read(HERE/'C03_EFFECTIVE_MODEL_PARAMETERS.json'),effective)\n        write(run/'C05_SINGLE_FACTOR_PARAMETER_DIFF.json',diff)\n        assert diff['status']=='PASS_SINGLE_ALGORITHM_FACTOR'\n        from c02_common import resource_gate,resources\n        resource_gate(resources(run))")
replace("write(folder/'RAW_RECEIPT.json',result)\n    for name,count", "write(folder/'RAW_RECEIPT.json',result)\n    if not isinstance(result['native_info'].get('SolCount'),int) or result['native_info']['SolCount']<=0:\n        result['vectors']={k:{'status':'NOT_AVAILABLE','reason':'NO_LEGAL_SOLUTION_COUNT'} for k in ('X','Pi','RC')}\n        write(folder/'RAW_RECEIPT.json',result)\n        write(root/'RAW_DURABLE.json',{'run_id':authorization['run_id'],'receipt_sha256':sha(folder/'RAW_RECEIPT.json'),'complete':False,'native_state_preserved':True,'qualification':'UNQUALIFIED'})\n        return result\n    for name,count")
ast.parse(s);(DEST/'c05_native.py').write_text(s)
out(W/'PREPARED_MODULE_BINDING.json',{'reused_modules':len(names),'immutable_input_files':len(refs),'no_old_launcher_copied':True,'c05_native_parent_sha256':sha(OLD/'c03_native.py'),'c05_native_sha256':sha(DEST/'c05_native.py')})
print('C03 exact modules verified; C05 native adaptation prepared; no native API executed')
