"""C07 identity and one-factor gates; no environment or solver creation."""
from pathlib import Path
import os,sys,platform,base64,hashlib,time
from c02_common import read,write,sha,resources,resource_gate,versions
ROOT=Path('/root/autodl-tmp/SGP');HERE=Path(__file__).resolve().parent
IDENTITY='C07_V4_RELIABILITY_DAILY122_USER_20261013_V1'

def parameter_diff(base,actual,variant='A'):
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

def verify_release(expected):
    assert sha(HERE/'C07_RELEASE_MANIFEST.json')==expected
    m=read(HERE/'C07_RELEASE_MANIFEST.json')
    for rel,r in m['files'].items():
        p=HERE/rel;assert not p.is_symlink() and p.is_file() and p.resolve().is_relative_to(HERE)
        assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],rel
    assert read(HERE/'C07_APPROVAL_RECORD.json')['approved_by_user'] is True
    assert sha(HERE/'C03_EFFECTIVE_MODEL_PARAMETERS.json')=='9514025d6234626f26d0f7dca7f9cf8070de4d24360a64429edbed790b9432a2'
    assert sha(HERE/'C05_EFFECTIVE_MODEL_PARAMETERS.json')=='349d8ca34cc5f0e882a368d8bd239bc590950a004cc94eddce3dbcac71b20c42'
    assert sha(HERE/'V4_APPROVED.json')=='955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f'
    assert read(HERE/'C07_LOCAL_INTERFACE_TESTS.json')['status']=='PASS'
    assert sha(HERE/'C06_EFFECTIVE_MODEL_PARAMETERS.json')=='f2f4bc219e3757dff6deda9035d67464e86e96e8ee9186427d2e27aced112f3c'
    assert read(HERE/'C07_V4_APPLICABILITY.json')['scientific_decision_required'] is False
    return m

def admission():
    import psutil
    assert platform.node()=='autodl-container-21104cb00b-43be1fed'
    assert sys.executable=='/root/autodl-tmp/SGP/env/gate5/bin/python3.11' and sys.version_info[:3]==(3,11,13)
    pub=Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().split()
    assert pub[0]=='ssh-ed25519' and base64.b64encode(hashlib.sha256(base64.b64decode(pub[1])).digest()).decode().rstrip('=')=='liZ36vNCsNcNdXeWs4f+g5ZIhPM/ZihP834vxs8Ulqc'
    v=versions();assert v=={'pypsa':'0.30.3','linopy':'0.5.5','numpy':'1.26.4','scipy':'1.15.2','pandas':'2.3.1','xarray':'2025.1.2','netCDF4':'1.7.2','psutil':'7.0.0'}
    r=resources(ROOT);resource_gate(r,start=True)
    assert r['disk_free']-4*1024**3>=8*1024**3 # raw/original/KKT/NetCDF+archive reserve; old inputs not copied
    from license_binding import bind_license
    lic=bind_license() # metadata/path only; no credential read
    active=[];names={'c05_native.py','c05_worker.py','c06_native.py','c06_worker.py','c07_native.py','c07_worker.py','c03_native.py','combined_worker.py','c02r_build.py'}
    for p in psutil.process_iter(['pid','cmdline','status']):
        cmd=p.info['cmdline'] or []
        if p.pid!=os.getpid() and any(Path(s).name in names for s in cmd):active.append(p.pid)
    assert not active,'ACTIVE_DAILY_TASK_NO_DUPLICATE'
    return {'hostname':platform.node(),'resources':r,'versions':v,'license_path_binding':lic,'active_daily_tasks':active,'new_output_reserve_bytes':4*1024**3,'epoch':time.time()}

def verify_inputs(run,progress):
    s=read(HERE/'SOURCE_BINDING.json');base=Path(s['baseline_path'])
    assert base==ROOT/'runs/c02r_c03_daily122_20261012T044259Z_25e62c10'
    assert sha(base/'BACKUP_INDEX.json')==s['baseline_BACKUP_INDEX_sha256']
    for rel,h in s['core'].items():assert sha(base/rel)==h,rel
    for j,r in enumerate(s['files']):
        p=base/r['relative'];real=p.resolve(strict=True)
        assert real.is_relative_to(ROOT) and real.is_file() and p.stat().st_size==r['bytes'],r['relative']
        assert sha(p)==r['sha256'],r['relative']
        if j%200==0:progress('IMMUTABLE_INPUT_SHA')
    for name in ('artifacts','bridge'):
        dest=run/name;assert not dest.exists() and not dest.is_symlink();dest.symlink_to(base/name,target_is_directory=True)
    write(run/'BUILD_RESULT.json',read(base/'BUILD_RESULT.json')) # historical receipt, explicitly NOT a new build
    write(run/'IMMUTABLE_INPUTS.json',{'status':'ALL_REFERENCED_INPUT_SHA_PASS','baseline':str(base),'source_binding_sha256':sha(HERE/'SOURCE_BINDING.json'),'file_count':len(s['files']),'bytes':s['bytes'],'core':s['core'],'baseline_BACKUP_INDEX_sha256':s['baseline_BACKUP_INDEX_sha256'],'read_only_directory_links':{'artifacts':str(base/'artifacts'),'bridge':str(base/'bridge')},'new_model_builds':0,'CSR_to_CSC_conversions':0,'old_candidate_warm_start':False})
    import shutil
    shutil.copytree(HERE/'expression',run/'expression')
    assert sha(run/'expression/C07_EXPRESSION_BINDING.json')==read(run/'AUTHORIZATION.json')['expression_sha256']
    return s
