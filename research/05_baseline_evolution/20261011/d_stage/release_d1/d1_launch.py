"""D-1 one 2920 build authorization (build-only, 0 optimize calls) with the detached supervisor/guard chain. No retry."""
from pathlib import Path
import os,sys,time,uuid,json,subprocess,platform,base64,hashlib,tarfile
from c02_common import read,write,sha,resources,resource_gate,versions
HERE=Path(__file__).resolve().parent;ROOT=Path('/root/autodl-tmp/SGP')
IDENTITY='D1_GATE6_2920_SCHEME_A_BUILD_ONLY_USER_20261013_V1'
# Regular file behind the Gate6 worktree symlink .../gate6_capture_20261008T200734Z/results_project/assembly_v1/... (C02 resolved the same link).
SOURCE=ROOT/'inputs/repo/results_project/assembly_v1/research_fullsc_2050_assembly_v1_unsolved.nc'
SOURCE_SHA='238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d'
GIB=1024**3
BUILD_DISK_ESTIMATE=13*GIB   # 8x daily C02R build+bridge (1.49 GB) plus margin; checked against the unchanged 8 GiB floor


def verify_release(expected):
    assert sha(HERE/'D1_RELEASE_MANIFEST.json')==expected
    m=read(HERE/'D1_RELEASE_MANIFEST.json')
    for rel,r in m['files'].items():
        p=HERE/rel;assert not p.is_symlink() and p.is_file() and p.resolve().is_relative_to(HERE)
        assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],rel
    assert read(HERE/'D1_APPROVAL_RECORD.json')['approved_by_user'] is True
    assert sha(HERE/'V4_APPROVED.json')=='955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f'
    assert sha(HERE/'scheme_a/EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json')=='a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720'
    assert sha(HERE/'GATE6_3H_ROUNDING_AUDIT.json')=='c6f95ca9be8db91b17f3e0a6188935337cf23a3efdf1f57819db5c0e0e06fe56'
    assert sha(HERE/'EFFECTIVE_PERTURBATION_LEDGER.csv')=='0450345f1c6a89d89309c920c66d8f7286b84aac76597fa7bd9db19a5a988856'
    assert read(HERE/'D1_LOCAL_TESTS.json')['status']=='PASS'
    return m


def admission():
    import psutil
    assert platform.node()=='autodl-container-21104cb00b-43be1fed'
    assert sys.executable=='/root/autodl-tmp/SGP/env/gate5/bin/python3.11' and sys.version_info[:3]==(3,11,13)
    pub=Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().split()
    assert pub[0]=='ssh-ed25519' and base64.b64encode(hashlib.sha256(base64.b64decode(pub[1])).digest()).decode().rstrip('=')=='liZ36vNCsNcNdXeWs4f+g5ZIhPM/ZihP834vxs8Ulqc'
    v=versions();assert v=={'pypsa':'0.30.3','linopy':'0.5.5','numpy':'1.26.4','scipy':'1.15.2','pandas':'2.3.1','xarray':'2025.1.2','netCDF4':'1.7.2','psutil':'7.0.0'}
    assert SOURCE.is_file() and not SOURCE.is_symlink() and sha(SOURCE)==SOURCE_SHA
    r=resources(ROOT);resource_gate(r,start=True)
    assert r['disk_free']-BUILD_DISK_ESTIMATE>=8*GIB,'BUILD_DISK_PROJECTION_BELOW_FLOOR'
    names={'d1_build.py','d1_worker.py','c09_native.py','c09_worker.py','c07_native.py','c07_worker.py','c03_native.py','combined_worker.py','c02r_build.py','c02_worker.py'}
    active=[p.pid for p in psutil.process_iter(['pid','cmdline']) if p.pid!=os.getpid() and any(Path(s).name in names for s in (p.info['cmdline'] or []))]
    assert not active,'ACTIVE_TASK_NO_DUPLICATE'
    return {'hostname':platform.node(),'resources':r,'versions':v,'source_network':{'path':str(SOURCE),'sha256':SOURCE_SHA},'active_tasks':active,
            'build_disk_estimate_bytes':BUILD_DISK_ESTIMATE,'epoch':time.time()}


def start(expected):
    verify_release(expected);early=admission()
    claims=ROOT/'d_claims';claims.mkdir(exist_ok=True)
    intent=claims/(IDENTITY+'_BUILD_INTENT.json')
    if intent.exists():raise RuntimeError('D1_BUILD_AUTHORIZATION_ALREADY_RESERVED_NO_RETRY')
    if any((ROOT/'runs').glob('d1_build2920_*')):raise RuntimeError('PRIOR_D1_RUN_REQUIRES_RECONCILIATION')
    now=time.time();rid='d1_build2920_'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime(now))+'_'+uuid.uuid4().hex[:8]
    run=ROOT/'runs'/rid
    a={'scope':'D1_SINGLE_2920_SCHEME_A_BUILD_ONLY','run_id':rid,'run_directory':str(run),'authorization_identity':IDENTITY,'release':str(HERE),
       'release_manifest_sha256':expected,'user_authorization_sha256':sha(HERE/'D1_APPROVAL_RECORD.json'),'started_epoch':now,
       'source_network':str(SOURCE),'source_network_sha256':SOURCE_SHA,
       'build_phase_seconds':10800,'build_absolute_deadline_epoch':now+10800,
       'bridge_phase_seconds':3600,'load_absolute_deadline_epoch':now+14400,
       'maximum_native_seconds':1,'native_absolute_deadline_epoch':now+14401,'raw_save_seconds':300,'raw_absolute_deadline_epoch':now+14851,
       'post_phase_seconds':1800,'post_absolute_deadline_epoch':now+16651,'absolute_deadline_epoch':now+16951,
       'native_exit_grace_seconds':120,'term_grace_seconds':30,'supervisor_lease_seconds':8,'soft_memory_limit_decimal_gb':65,
       'resource_limits':{'rss_bytes':75*GIB,'cgroup_headroom_bytes':12*GIB,'disk_free_bytes':8*GIB},
       'auto_retry':False,'max_builds':1,'max_optimize_calls':0,'native_phase_used':False,'G6_05':'PAUSED_BY_USER','time_aggregation':'NONE','C01R_used':False}
    from d_production_control import limits_valid
    limits_valid(a)
    with intent.open('x') as f:json.dump(a,f);f.flush();os.fsync(f.fileno())
    control=HERE.parent/(rid+'_AUTHORIZATION.json');write(control,a);write(HERE.parent/(rid+'_ADMISSION.json'),early)
    with (HERE.parent/(rid+'_supervisor.log')).open('xb') as log:
        p=subprocess.Popen([sys.executable,'-B',str(HERE/'d1_launch.py'),'supervise',str(control)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    print(json.dumps({'run_id':rid,'run':str(run),'authorization':str(control),'supervisor_pid':p.pid,'t0':now,'absolute_deadline':a['absolute_deadline_epoch'],'detached':True,'max_builds':1,'max_optimize_calls':0}),flush=True)


def light_evidence(run):
    """Small receipts only (JSON/JSONL/logs <= 20 MB); arrays stay on the cloud, indexed by ARTIFACT_SHA_INDEX.json."""
    dest=HERE.parent/(run.name+'_LIGHT_EVIDENCE.tar.gz');part=dest.with_name(dest.name+'.partial');files=[]
    with tarfile.open(part,'x:gz') as t:
        for p in sorted(run.rglob('*')):
            if p.is_file() and not p.is_symlink() and p.suffix in ('.json','.jsonl','.log','.patch') and p.stat().st_size<=20*1024**2:
                t.add(p,arcname=str(p.relative_to(run)),recursive=False);files.append(str(p.relative_to(run)))
    with part.open('rb') as f:os.fsync(f.fileno())
    os.rename(part,dest)
    write(HERE.parent/(run.name+'_LIGHT_EVIDENCE_RECEIPT.json'),{'run_id':run.name,'archive':str(dest),'bytes':dest.stat().st_size,'sha256':sha(dest),'members':len(files),'completed_epoch':time.time()})


def supervise(path):
    from d_production_control import supervise as protect
    a=read(path);run=Path(a['run_directory'])
    try:protect([sys.executable,'-B',str(HERE/'d1_worker.py'),str(run)],run,a,require_cgroup=True,launch_closeout=False)
    finally:
        if (run/'GUARD_EXIT.json').exists() and not read(run/'GUARD_EXIT.json')['residual_live_pids'] and time.time()<a['absolute_deadline_epoch']-30:
            try:light_evidence(run)
            except Exception as e:write(HERE.parent/(run.name+'_LIGHT_EVIDENCE_FAILURE.json'),{'error':type(e).__name__,'detail':str(e),'cloud_originals_preserved':True})


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='start':start(sys.argv[2])
    elif len(sys.argv)==3 and sys.argv[1]=='supervise':supervise(Path(sys.argv[2]))
    else:raise SystemExit('explicit start + frozen release SHA, or supervise + authorization required')
