"""C06 identity and one-factor gates; no environment or solver creation."""
from pathlib import Path
import os,sys,platform,base64,hashlib,time
from c02_common import read,write,sha,resources,resource_gate,versions
ROOT=Path('/root/autodl-tmp/SGP');HERE=Path(__file__).resolve().parent
IDENTITY='C06_BARCONVTOL_DAILY122_USER_20261012_V1'

def parameter_diff(base,actual,baseline='C03'):
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


def verify_release(expected):
    assert sha(HERE/'C06_RELEASE_MANIFEST.json')==expected
    m=read(HERE/'C06_RELEASE_MANIFEST.json')
    for rel,r in m['files'].items():
        p=HERE/rel;assert not p.is_symlink() and p.is_file() and p.resolve().is_relative_to(HERE)
        assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],rel
    assert read(HERE/'C06_APPROVAL_RECORD.json')['approved_by_user'] is True
    assert sha(HERE/'C03_EFFECTIVE_MODEL_PARAMETERS.json')=='9514025d6234626f26d0f7dca7f9cf8070de4d24360a64429edbed790b9432a2'
    assert sha(HERE/'C05_EFFECTIVE_MODEL_PARAMETERS.json')=='349d8ca34cc5f0e882a368d8bd239bc590950a004cc94eddce3dbcac71b20c42'
    assert sha(HERE/'V4_APPROVED.json')=='955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f'
    assert read(HERE/'C06_LOCAL_INTERFACE_TESTS.json')['status']=='PASS'
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
    active=[];names={'c05_native.py','c05_worker.py','c06_native.py','c06_worker.py','c03_native.py','combined_worker.py','c02r_build.py'}
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
    return s
