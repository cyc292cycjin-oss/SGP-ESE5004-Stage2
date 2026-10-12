"""New conditional authorization. Never invokes any historical launcher."""
from pathlib import Path
import sys,os,time,subprocess,uuid,platform,json,base64,hashlib,stat
from c02_common import read,write,sha,resources,resource_gate,versions
HERE=Path(__file__).resolve().parent;ROOT=Path('/root/autodl-tmp/SGP')
IDENTITY='C02R_C03_DAILY_122_COMBINED_20261012_V1'
DAILY=ROOT/'runs/c02_daily_build_20261012T025604Z_fcc0f784/artifacts/daily_365_unsolved.nc'

def verify():
    assert platform.node()=='autodl-container-21104cb00b-43be1fed'
    assert sys.executable=='/root/autodl-tmp/SGP/env/gate5/bin/python3.11'
    pub=Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().split()
    assert pub[0]=='ssh-ed25519' and base64.b64encode(hashlib.sha256(base64.b64decode(pub[1])).digest()).decode().rstrip('=')=='liZ36vNCsNcNdXeWs4f+g5ZIhPM/ZihP834vxs8Ulqc'
    files=read(HERE/'C03_RELEASE_MANIFEST.json')['files']
    for rel,r in files.items():
        p=HERE/rel;assert p.is_file() and not p.is_symlink() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],rel
    assert sha(DAILY)=='b2df7dc771d4759668988f7a0abd7ccfafacd976dff644f7acafd20aee50b9f2'
    assert sha(HERE/'V4_APPROVED.json')=='955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f'
    assert sha(HERE/'scheme_a/EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json')=='a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720'
    assert sha(HERE/'c01r/C00_DAILY_365_PROTOCOL_C01R_V1.md')=='661a81e532184003938213a3e81ad35bd4a687108332d14b3582bf7a8eac2856'
    assert read(HERE/'LOCAL_INTERFACE_TESTS.json')['status']=='PASS'
    assert versions()=={'pypsa':'0.30.3','linopy':'0.5.5','numpy':'1.26.4','scipy':'1.15.2','pandas':'2.3.1','xarray':'2025.1.2','netCDF4':'1.7.2','psutil':'7.0.0'}
    assert sha(HERE/'USER_COMBINED_AUTHORIZATION.md')=='db5f437777b731e996e304c3077ad77830e14c5dc0694f815d265050fbe36b4d'
    for name,h in read(HERE/'REUSE_BUILD_RECEIPTS.json').items():assert sha(DAILY.parent/name)==h,name
    resource_gate(resources(ROOT),start=True)
    # Daily chunked output + CSC bridge + RAW/original vectors + seal reserve.
    assert resources(ROOT)['disk_free']-10*1024**3>=8*1024**3
    import psutil
    for p in psutil.process_iter(['pid','cmdline']):
        cmd=p.info['cmdline'] or []
        if p.pid!=os.getpid() and any(Path(s).name in {'c02r_build.py','c03_native.py','combined_worker.py'} for s in cmd):raise RuntimeError('ACTIVE_DAILY_PROCESS_NO_DUPLICATE')
    return files

def start():
    verify()
    claimdir=ROOT/'c03_claims';claimdir.mkdir(exist_ok=True)
    intent=claimdir/(IDENTITY+'_INTENT.json');opt=claimdir/(IDENTITY+'_OPTIMIZE_CONSUMED.json')
    if intent.exists() or opt.exists():raise RuntimeError('AUTHORIZATION_PREVIOUSLY_RESERVED_NO_RETRY')
    now=time.time();rid='c02r_c03_daily122_'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime(now))+'_'+uuid.uuid4().hex[:8]
    run=ROOT/'runs'/rid
    a={'scope':'C02R_C03_CONDITIONAL_SINGLE_DAILY_DIAGNOSTIC','run_id':rid,'run_directory':str(run),'authorization_identity':IDENTITY,'release':str(HERE),'release_manifest_sha256':sha(HERE/'C03_RELEASE_MANIFEST.json'),'user_authorization_sha256':sha(HERE/'USER_COMBINED_AUTHORIZATION.md'),'started_epoch':now,'build_absolute_deadline_epoch':now+1800,'load_absolute_deadline_epoch':now+2700,'native_absolute_deadline_epoch':now+6300,'raw_absolute_deadline_epoch':now+6750,'post_absolute_deadline_epoch':now+7950,'absolute_deadline_epoch':now+9150,'maximum_native_seconds':3600,'native_exit_grace_seconds':120,'term_grace_seconds':30,'raw_save_seconds':300,'supervisor_lease_seconds':8,'soft_memory_limit_decimal_gb':65,'resource_limits':{'rss_bytes':75*1024**3,'cgroup_headroom_bytes':12*1024**3,'disk_free_bytes':8*1024**3},'daily_source':str(DAILY),'daily_source_sha256':sha(DAILY),'library_path':'/root/autodl-tmp/SGP/env/gate5/lib/libgurobi120.so','library_sha256':'af7c367e21efc6fe9d273f84cdc5dda3bf62edf8ddcb273be50be3b37a0cec3c','optimize_claim':str(opt),'auto_retry':False,'max_builds':1,'max_optimize_calls':1,'G6_05':'PAUSED_BY_USER','reused_build_evidence':{}}
    for name in ['SCHEME_A_DAILY_EXACT_GROUPS.json','C02_NETWORK_LP_DIFF_REGISTER.json','NETWORK_READBACK.json']:
        a['reused_build_evidence'][name]=sha(DAILY.parent/name)
    from production_control import limits_valid
    limits_valid(a)
    with intent.open('x') as f:json.dump(a,f);f.flush();os.fsync(f.fileno())
    control=HERE.parent/(rid+'_AUTHORIZATION.json');write(control,a)
    log=HERE.parent/(rid+'_supervisor.log')
    with log.open('xb') as out:
        child=subprocess.Popen([sys.executable,'-B',str(HERE/'combined_launch.py'),'supervise',str(control)],stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
    print(json.dumps({'run_id':rid,'run':str(run),'authorization':str(control),'supervisor_pid':child.pid,'t0':now,'absolute_deadline':now+9150,'detached':True}))

def supervise(path):
    from production_control import supervise as protect
    a=read(path);run=Path(a['run_directory'])
    try:protect([sys.executable,'-B',str(HERE/'combined_worker.py'),str(run)],run,a,require_cgroup=True,launch_closeout=False)
    finally:
        # Independent, bounded seal only after the verified worker and guard have exited.
        if (run/'GUARD_EXIT.json').exists() and not read(run/'GUARD_EXIT.json')['residual_live_pids']:
            remaining=min(1200,a['absolute_deadline_epoch']-time.time())
            if remaining>30:
                subprocess.run(['timeout','--signal=TERM','--kill-after=5s',str(remaining-5)+'s',sys.executable,'-B',str(HERE/'seal_run.py'),str(run)],check=False)
            else:write(run/'LOCAL_SYNC_PENDING.json',{'status':'LOCAL_SYNC_PENDING','reason':'CLOSEOUT_BUDGET','cloud_originals_preserved':True})
if __name__=='__main__':
    if sys.argv[1:]==['start']:start()
    elif len(sys.argv)==3 and sys.argv[1]=='supervise':supervise(Path(sys.argv[2]))
    else:raise SystemExit('explicit start or supervise required')
