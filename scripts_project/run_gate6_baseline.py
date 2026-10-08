"""Gate6 Baseline: default file preflight, explicit test/build/solve boundaries.

No execution authorization is included in the repository. Build/solve both
require a future human authorization bound to code, lock, tests and budget.
"""
import argparse,ast,datetime,hashlib,json,os,re,shutil,subprocess,sys,threading,time,traceback
from pathlib import Path
import numpy as np,pandas as pd,pypsa,linopy,highspy
from gate5_resources import sha,process_tree_sample
from gate5_cloud_resources import snapshot
from assembly_components import validate_hooks,check_global_constraints,install_research_constraint_hooks
from fixed_accounts import validate_exported_accounting
from inventory_audit_3h import audit,INPUT_SHA
from gate6_fixed_term_contract import contract
from gate6_result import write,consume
from lossless_gate5_lifecycle import bounded_build_allocator,trim
from fixed_inventory_scaling import FixedInventoryScaling
from execute_gate5_lossless import prepare_detached
from run_gate5_validation import hook_receipt
from precision_handoff import ok

CONFIG='configs/research/gate6_baseline_3h.json'
DATA=['results_project/assembly_v1/research_fullsc_2050_assembly_v1_unsolved.nc',
      'results_project/assembly_v1/final_allocation/allocation_manifest.json',
      'results_project/assembly_v1/final_allocation/allocations.npz',
      'research_inputs/assembly_v1/registry.json','research_inputs/assembly_v1/sources/BASE_RECONSTRUCTION.json']
GIB=1024**3
def require(ok,message):
    if not ok:raise ValueError(message)
def read(p):return json.loads(Path(p).read_text())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()

def code_closure(root):
    """Transitive local imports, including deferred imports; code travels in Git."""
    from run_gate6_no_solver_tests import REGRESSION
    folder=Path(root)/'scripts_project';pending=['run_gate6_baseline','test_gate6_baseline_3h','run_gate6_no_solver_tests']+[Path(p).stem for p in REGRESSION];seen=set()
    while pending:
        name=pending.pop();p=folder/(name+'.py')
        if name in seen or not p.is_file():continue
        seen.add(name)
        for node in ast.walk(ast.parse(p.read_text())):
            names=[node.module] if isinstance(node,ast.ImportFrom) else [x.name for x in node.names] if isinstance(node,ast.Import) else []
            pending.extend(x.split('.')[0] for x in names if x)
    return sorted('scripts_project/'+n+'.py' for n in seen)

def make_lock(root):
    root=Path(root);files=[]
    history_path='research/04_model_assembly/final_validation/GATE5_RUN_HISTORY.json'
    history=read(root/history_path);historical=next(r for r in history['runs'] if r['run_id']==history['latest_run_id'])['manifest']
    fixtures=[history_path,historical,str(Path(historical).parent/'RESOURCE_MONITOR.jsonl')]
    for rel in DATA+[CONFIG]+code_closure(root)+fixtures:
        p=root/rel;require(p.is_file(),'Missing dependency '+rel)
        files.append(dict(path=rel,size_bytes=p.stat().st_size,sha256=sha(p),role='FROZEN_RUNTIME_DATA' if rel in DATA else 'NO_SOLVER_REGRESSION_FIXTURE' if rel in fixtures else 'GIT_CODE_OR_CONFIG'))
    return dict(schema='GATE6_INPUT_LOCK_V1',gate='GATE6',input_sha256=INPUT_SHA,files=files,
        dependency_basis='Five scientific data reads in preflight/source audit; build, native mmap mapping and reload/export reuse the same frozen input plus generated run artifacts. Static transitive local import closure includes deferred postsolve and test code. Three separately labelled historical files are read ONLY by frozen no-solver resource regressions, never as Gate6 admission. Environment separately frozen. Historical 32-reference inventory is provenance, not this execution closure.',
        generated_at_run=['mapping/*.npy','mapping/MAPPING_MANIFEST.json','native_result/*.npy','native_result/NATIVE_QUALIFICATION.json','GATE6_* receipts'],
        external_paths_in_metadata='Historical provenance strings only; not opened by Gate6 runtime',
        environment={'python':'3.11.13','pypsa':'0.30.3','linopy':'0.5.5','highs':'1.11.0'})

def verify_lock(root,lock):
    require(lock.get('gate')=='GATE6' and lock.get('input_sha256')==INPUT_SHA,'Wrong Gate6 lock')
    expected=make_lock(root)
    require(lock['files']==expected['files'],'Execution dependency lock changed')

def validate_temporal(n):
    expected=pd.date_range('2013-01-01',periods=2920,freq='3h',name='snapshot')
    require(n.snapshots.equals(expected),'Expected original complete 2013/2920/3h snapshots')
    for col in ['objective','generators','stores']:
        w=n.snapshot_weightings[col].to_numpy()
        require(w.dtype==np.float64 and np.array_equal(w,np.full(2920,3.,dtype=np.float64)) and w.sum()==8760.,'Incorrect 3h weights '+col)

def validate_input(n):
    validate_temporal(n);validate_hooks(n);check_global_constraints(n);validate_exported_accounting(n)
    require(len(n.loads)==1737 and n.loads.source_account_id.nunique()==171,'Demand dimensions changed')
    require(int(n.buses.carrier.isin(['AC','DC']).sum())==100,'Geographical node count changed')
    require(n.meta['stock_uncertainty']['qualified_capacity_mw']==187400.4,'Stock boundary changed')
    require(len(n.meta['external_pending_fixed_accounts'])==807,'Fixed terms changed')
    require(sum(r['policy_weight'] is None for r in n.meta['physical_carbon_map'])==200,'Pending policy changed')
    require(n.meta['policy_enabled'] is False and n.meta['policy_cap_actually_enabled'] is False,'Baseline policy must be OFF')
    require(n.meta['scientific_results_allowed'] is False and not n.meta['FullSystemCostComplete'] and not n.meta['FullSystemEmissionsComplete'],'Scientific reporting boundary changed')
    require(n.meta['artifact_role']=='FULL_SC_RESEARCH_BASELINE_UNSOLVED','Not frozen unsolved input')
    require('lv_limit' in n.global_constraints.index,'Native lv_limit missing')
    require(not any(r['Gate4SwitchApplied'] for r in n.meta['electricity_interconnector_control_set']),'Topology intervention applied')

def environment():
    actual=dict(python='.'.join(map(str,sys.version_info[:3])),pypsa=pypsa.__version__,linopy=linopy.__version__,highs=highspy.Highs().version())
    require(actual==dict(python='3.11.13',pypsa='0.30.3',linopy='0.5.5',highs='1.11.0'),'Frozen environment mismatch')
    return actual

def preflight(root,source=None,verify=True):
    root=Path(root);cfg=read(root/CONFIG)
    require(cfg['input_sha256']==INPUT_SHA and cfg['policy_enabled'] is False,'Config identity changed')
    lock=read(root/cfg['lock']) if verify else make_lock(root)
    if verify:verify_lock(root,lock)
    source=Path(source) if source else root/cfg['input']
    require(sha(source)==INPUT_SHA,'Wrong frozen input SHA (daily/solved inputs are forbidden)')
    env=environment();n=pypsa.Network(source);validate_input(n)
    rounding=audit(n,root);fixed=contract(n)
    report=dict(status='PASS',gate='GATE6',scenario='BASELINE',input_sha256=sha(source),snapshots=2920,annual_hours=8760,
        geographical_nodes=100,accounts=171,loads=1737,stock_mw=187400.4,external_pending_terms=807,pending_policy_weights=200,
        policy_enabled=False,environment=env,code_sha=git(root,'rev-parse','HEAD'),
        full_optimization_model_built=False,solver_calls=0,presolve_calls=0,run_authorized=False,resource_budget_approved=False)
    del n;trim();return report,rounding,fixed,lock

def authorization(root,cfg,mode,out,path):
    require(path is not None,'Independent Gate6 authorization required before full build/solve')
    a=read(path)
    require(a.get('gate')=='GATE6' and a.get('scenario')=='BASELINE' and a.get('stage')==mode,'Old Gate5 or wrong-stage authorization rejected')
    require(a.get('human_authorized') is True and bool(a.get('human_decision_reference')) and a.get('max_attempts')==1,'Future explicit one-attempt human authorization required')
    require(a.get('budget_approved') is True and a.get('budget')==cfg['proposed_budget'],'Resource/time/cost budget not approved')
    require(a.get('input_sha256')==INPUT_SHA and a.get('code_sha')==git(root,'rev-parse','HEAD'),'Authorized scientific/code identity differs')
    require(not git(root,'status','--porcelain'),'Clean code tree required')
    require(a.get('input_lock_sha256')==sha(root/cfg['lock']),'Authorization lock differs')
    require(a.get('tests_sha256')==sha(root/cfg['tests']),'Authorization test evidence differs')
    tests=read(root/cfg['tests']);require(tests.get('status')=='PASS' and tests.get('solver_calls')==tests.get('presolve_calls')==0,'No-solver prerequisite missing')
    require(tests['input_lock_sha256']==sha(root/cfg['lock']),'Tests are stale for execution lock')
    for rel,digest in tests['tested_code_sha256'].items():require(sha(root/rel)==digest,'Tested code changed: '+rel)
    require(a.get('run_id')==out.name and re.fullmatch(r'[0-9a-f]{64}',a.get('authorization_id','')),'Invalid authorization identity/run')
    require(out.parent==Path('/root/autodl-tmp/SGP/runs') and out.name.startswith('cloud_gate6_'),'Gate6 cloud non-overwrite run directory required')
    require(not out.exists(),'Existing run cannot be overwritten')
    return a

def resource_admission(observation,budget):
    reasons=[]
    if observation['effective_available_bytes']<budget['start_available_gib']*GIB:reasons.append('CGroup available below proposed/approved start budget')
    if observation['effective_cpu_cores']<2:reasons.append('Fewer than 2 effective CPUs')
    if observation['disk']['free_bytes']<budget['start_disk_free_gib']*GIB:reasons.append('Insufficient data disk reserve')
    return dict(status='PASS' if not reasons else 'NOT_READY',reasons=reasons,observation=observation)

def guard_reason(observation,rss,elapsed,budget):
    if observation is None:return 'RESOURCE_MONITOR_UNAVAILABLE'
    if observation['effective_available_bytes']<budget['headroom_guard_gib']*GIB:return 'CGROUP_HEADROOM_GUARD'
    if rss>budget['tree_rss_limit_gib']*GIB:return 'PROCESS_TREE_RSS_GUARD'
    if elapsed>budget['wall_seconds']:return 'WALL_GUARD'
    if observation['disk']['free_bytes']<GIB:return 'DISK_EMERGENCY_GUARD'
    return None

def execute_native(owner,out,record,fidelity,identity,cfg,progress,before_run):
    require(fidelity['status']=='PASS','Exact transfer failed')
    h=owner[0]
    options=dict(threads=2,solver='ipm',run_crossover='on',presolve='on',time_limit=cfg['proposed_budget']['solver_seconds'])
    for key,val in options.items():ok(h.setOptionValue(key,val))
    ok(h.setOptionValue('output_flag',True));ok(h.setOptionValue('log_file',str(Path(out)/'gate6_solver.log')))
    before_run();h.run()  # Future independent Gate6 authorization only; trapped in tests.
    del h
    return consume(owner,out,record,identity,progress)

def execute(root,out,mode,auth_path):
    root=Path(root);out=Path(out).resolve();cfg=read(root/CONFIG)
    a=authorization(root,cfg,mode,out,auth_path)  # Must precede any full-scale build.
    report,identity,fixed,lock=preflight(root)
    observation=snapshot(out.parent.parent);ready=resource_admission(observation,a['budget'])
    require(ready['status']=='PASS','Fresh cloud admission failed')
    claim=out.parent.parent/'evidence'/('gate6_authorization_'+a['authorization_id']+'.consumed.json')
    with claim.open('x') as f:json.dump(dict(authorization=a,claimed_at=now(),stage=mode),f);f.flush();os.fsync(f.fileno())
    out.mkdir(exist_ok=False)
    shutil.copyfile(auth_path,out/'GATE6_EXECUTION_AUTHORIZATION.json')
    for name,obj in [('GATE6_INPUT_LOCK.json',lock),('GATE6_3H_ROUNDING_AUDIT.json',identity),('GATE6_PREFLIGHT.json',report),('GATE6_RESOURCE_ADMISSION.json',ready),('GATE6_FIXED_TERM_CONTRACT.json',fixed)]:write(out/name,obj)
    receipt=dict(gate='GATE6',scenario='BASELINE',run_id=out.name,code_sha=git(root,'rev-parse','HEAD'),input_sha256=INPUT_SHA,
        input_lock_sha256=sha(out/'GATE6_INPUT_LOCK.json'),status='STARTING',solver_calls=0,presolve_api_calls=0,formal_phase5_runs=0,pid=os.getpid(),started_at=now(),stage='input')
    done=threading.Event();started=time.monotonic();mutex=threading.Lock()
    def save():
        with mutex:write(out/'GATE6_RUN_MANIFEST.json',receipt)
    def progress(stage,*detail):receipt['stage']=stage;save()
    def monitor():
        with (out/'RESOURCE_MONITOR.jsonl').open('a',buffering=1) as f:
            while not done.wait(2):
                try:obs=snapshot(out.parent.parent);tree=process_tree_sample();rss=tree['process_tree_rss_bytes']
                except Exception:obs=None;rss=0
                elapsed=time.monotonic()-started;reason=guard_reason(obs,rss,elapsed,a['budget'])
                row=dict(at=now(),stage=receipt['stage'],elapsed_s=elapsed,tree_rss_bytes=rss,resources=obs,stop_reason=reason)
                f.write(json.dumps(row)+'\n')
                if reason:
                    receipt.update(status='STOPPED_RESOURCE_GUARD',reason=reason);save();write(out/'EXIT_STATUS.json',dict(exit_code=137,reason=reason));f.flush();os.fsync(f.fileno());os._exit(137)
    worker=threading.Thread(target=monitor,daemon=True);worker.start();save()
    try:
        source=root/cfg['input'];n=pypsa.Network(source);validate_input(n);progress('build')
        with bounded_build_allocator():n.optimize.create_model();before=set(n.model.constraints);install_research_constraint_hooks(n)
        hooks=hook_receipt(n,before);require(len(hooks['research_constraint_names'])==1003,'Hook attachment changed')
        write(out/'GATE6_HOOK_RECEIPT.json',hooks)
        receipt.update(full_optimization_model_built=True,variables=int(n.model.nvars),constraints=int(n.model.ncons))
        if mode=='build':receipt.update(status='BUILD_ONLY_COMPLETED',solve_authorized=False);return receipt
        scaling=FixedInventoryScaling(n,identity);no=[n];so=[scaling];del n,scaling
        progress('exact_transfer')
        native,record,fidelity=prepare_detached(no,so,source,INPUT_SHA,out,[],{},progress,result_directory=out)
        owner=[native];del native
        def before_run():
            receipt.update(status='SOLVING',solver_calls=1,stage='solve');save()
        result=execute_native(owner,out,record,fidelity,identity,cfg,progress,before_run)
        receipt.update(result);return receipt
    except BaseException as error:
        receipt.update(status='FAILED_ENGINEERING',error=str(error));(out/'failure_traceback.txt').write_text(traceback.format_exc());raise
    finally:
        done.set();worker.join(timeout=3);receipt['ended_at']=now();save()
        write(out/'EXIT_STATUS.json',dict(exit_code=0 if receipt['status'] in ['PASS','BUILD_ONLY_COMPLETED'] else 2,status=receipt['status'],solver_calls=receipt['solver_calls']))

def dispatch(root,out,mode='preflight',authorization_path=None,source=None):
    if mode in ('build','solve'):return execute(root,out,mode,authorization_path)
    require(mode in ('preflight','test'),'Unknown Gate6 mode')
    if mode=='test':
        from run_gate6_no_solver_tests import run
        return run(root,out)
    # Actual production-file preflight has a hard build/native-call trap.
    from unittest.mock import patch
    from pypsa.optimization.optimize import OptimizationAccessor
    with patch.object(OptimizationAccessor,'create_model',side_effect=AssertionError('Full build forbidden in preflight')),patch.object(highspy.Highs,'run',side_effect=AssertionError('NO SOLVE')),patch.object(highspy.Highs,'presolve',side_effect=AssertionError('NO PRESOLVE')):
        report,rounding,fixed,lock=preflight(root,source=source)
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    for name,obj in [('GATE6_PREFLIGHT.json',report),('GATE6_3H_ROUNDING_AUDIT.json',rounding),('GATE6_FIXED_TERM_CONTRACT.json',fixed),('GATE6_INPUT_LOCK.json',lock)]:write(out/name,obj)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['preflight','test','build','solve'],default='preflight');p.add_argument('--output',required=True,type=Path);p.add_argument('--authorization',type=Path);p.add_argument('--source',type=Path)
    args=p.parse_args();root=Path(__file__).resolve().parents[1]
    result=dispatch(root,args.output,args.mode,args.authorization,args.source)
    print(json.dumps({k:v for k,v in result.items() if k not in ['suites','tested_code_sha256']},indent=2))
