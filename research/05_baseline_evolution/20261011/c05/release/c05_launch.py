"""One independent C05 authorization and detached C03 protection chain."""
from pathlib import Path
import os,sys,time,uuid,json,subprocess
from c02_common import read,write,sha
from c05_checks import ROOT,HERE,IDENTITY,verify_release,admission

def start(expected):
    verify_release(expected);early=admission()
    claims=ROOT/'c05_claims';claims.mkdir(exist_ok=True)
    intent=claims/(IDENTITY+'_INTENT.json');opt=claims/(IDENTITY+'_OPTIMIZE_CONSUMED.json')
    if intent.exists() or opt.exists():raise RuntimeError('C05_AUTHORIZATION_ALREADY_RESERVED_NO_RETRY')
    if any((ROOT/'runs').glob('c05_aggregate0_daily122_*')):raise RuntimeError('PRIOR_C05_RUN_REQUIRES_RECONCILIATION')
    now=time.time();rid='c05_aggregate0_daily122_'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime(now))+'_'+uuid.uuid4().hex[:8]
    run=ROOT/'runs'/rid
    a={'scope':'C05_AGGREGATE0_SINGLE_DAILY_DIAGNOSTIC','run_id':rid,'run_directory':str(run),'authorization_identity':IDENTITY,'release':str(HERE),'release_manifest_sha256':expected,'user_authorization_sha256':sha(HERE/'C05_APPROVAL_RECORD.json'),'started_epoch':now,'load_absolute_deadline_epoch':now+900,'native_absolute_deadline_epoch':now+4500,'raw_absolute_deadline_epoch':now+4950,'post_absolute_deadline_epoch':now+6150,'absolute_deadline_epoch':now+7200,'maximum_native_seconds':3600,'native_exit_grace_seconds':120,'term_grace_seconds':30,'raw_save_seconds':300,'supervisor_lease_seconds':8,'soft_memory_limit_decimal_gb':65,'resource_limits':{'rss_bytes':75*1024**3,'cgroup_headroom_bytes':12*1024**3,'disk_free_bytes':8*1024**3},'library_path':'/root/autodl-tmp/SGP/env/gate5/lib/libgurobi120.so','library_sha256':'af7c367e21efc6fe9d273f84cdc5dda3bf62edf8ddcb273be50be3b37a0cec3c','optimize_claim':str(opt),'auto_retry':False,'max_builds':0,'max_optimize_calls':1,'G6_05':'PAUSED_BY_USER','baseline_run_id':'c02r_c03_daily122_20261012T044259Z_25e62c10','input_binding_sha256':sha(HERE/'SOURCE_BINDING.json'),'proposed_algorithm_override':{'Aggregate':0},'seal_seconds_max':1050,'separate_local_transfer_seconds_max':3600}
    from production_control import limits_valid
    limits_valid(a)
    with intent.open('x') as f:json.dump(a,f);f.flush();os.fsync(f.fileno())
    control=HERE.parent/(rid+'_AUTHORIZATION.json');write(control,a);write(HERE.parent/(rid+'_ADMISSION.json'),early)
    with (HERE.parent/(rid+'_supervisor.log')).open('xb') as log:
        p=subprocess.Popen([sys.executable,'-B',str(HERE/'c05_launch.py'),'supervise',str(control)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    print(json.dumps({'run_id':rid,'run':str(run),'authorization':str(control),'supervisor_pid':p.pid,'t0':now,'absolute_deadline':a['absolute_deadline_epoch'],'detached':True,'max_optimize_calls':1}),flush=True)

def supervise(path):
    from production_control import supervise as protect
    a=read(path);run=Path(a['run_directory'])
    try:protect([sys.executable,'-B',str(HERE/'c05_worker.py'),str(run)],run,a,require_cgroup=True,launch_closeout=False)
    finally:
        if (run/'GUARD_EXIT.json').exists() and not read(run/'GUARD_EXIT.json')['residual_live_pids']:
            from c05_seal import guarded_seal
            guarded_seal(run)

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='start':start(sys.argv[2])
    elif len(sys.argv)==3 and sys.argv[1]=='supervise':supervise(Path(sys.argv[2]))
    else:raise SystemExit('explicit start + frozen release SHA, or supervise + authorization required')
