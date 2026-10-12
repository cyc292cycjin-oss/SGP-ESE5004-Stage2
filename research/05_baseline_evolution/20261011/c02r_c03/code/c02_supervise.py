"""Detached supervisor plus independent resource/deadline guard, no restart."""
from pathlib import Path
import os,sys,time,subprocess,signal,zipfile
from c02_common import *

def stop_target(i,deadline):
    if not same_identity(i):return {'identity_confirmed':False,'signals':[]}
    # Worker has its own session; no unrelated session or global Python signalling.
    assert i['sid']==i['pid']==i['pgid']
    signals=[]
    os.killpg(i['pgid'],signal.SIGTERM);signals.append({'signal':'TERM','at':time.time()})
    end=min(deadline,time.time()+3)
    while time.time()<end and same_identity(i):time.sleep(.1)
    if same_identity(i):os.killpg(i['pgid'],signal.SIGKILL);signals.append({'signal':'KILL','at':time.time()})
    return {'identity_confirmed':True,'signals':signals}

def guard(run):
    import psutil
    a=read(run/'BUILD_AUTHORIZATION.json'); ids=read(run/'PROCESS_IDENTITIES.json');peak=0;reason=None
    initial={r['path']:r['memory_events'] for r in a['initial_resources']['ancestors']}
    with (run/'RESOURCE_SAMPLES.jsonl').open('x',buffering=1) as log:
        while True:
            if not same_identity(ids['worker']):break
            try:
                p=psutil.Process(ids['worker']['pid']);rss=p.memory_info().rss+sum(x.memory_info().rss for x in p.children(recursive=True));peak=max(peak,rss)
                r=resources(run);r.update(rss_bytes=rss,peak_worker_tree_rss=peak);log.write(json.dumps(r)+'\n');log.flush()
                write(run/'GUARD_ALIVE.json',{'timestamp':time.time(),'deadline':a['deadline'],'peak_rss':peak})
                resource_gate(r)
                if rss>75*GIB:raise RuntimeError('RSS above 75 GiB')
                if time.time()>=a['deadline']-5:raise RuntimeError('absolute deadline exit margin')
                if not same_identity(ids['supervisor']):raise RuntimeError('supervisor identity lost')
                for row in r['ancestors']:
                    old=dict(line.split() for line in initial[row['path']].splitlines());new=dict(line.split() for line in row['memory_events'].splitlines())
                    if any(int(new.get(k,0))>int(old.get(k,0)) for k in ['oom','oom_kill','max']):raise RuntimeError('memory event increment')
            except Exception as e:reason=str(e);break
            time.sleep(.5)
    action=stop_target(ids['worker'],a['deadline']) if reason else None
    write(run/'GUARD_EXIT.json',{'reason':reason,'stop':action,'peak_rss_bytes':peak,'at':time.time()})
    if reason:write(run/'GUARD_FAILURE.json',{'status':'C02_BLOCKED_WITH_SPECIFIC_EVIDENCE','reason':reason})

def supervisor(run):
    root=Path(__file__).resolve().parent;a=read(run/'BUILD_AUTHORIZATION.json')
    log=(run/'worker.log').open('xb')
    worker=subprocess.Popen([sys.executable,'-B',str(root/'c02_worker.py'),str(run)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
    ids={'worker':identity(worker.pid),'supervisor':identity(os.getpid())};write(run/'PROCESS_IDENTITIES.json',ids)
    g=subprocess.Popen([sys.executable,'-B',str(__file__),str(run),'--guard'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
    ids['guard']=identity(g.pid);write(run/'ALL_PROCESS_IDENTITIES.json',ids)
    failure=None
    while worker.poll() is None:
        if g.poll() is not None or time.time()>=a['deadline']-5:
            failure='guard exited during worker or absolute deadline';stop_target(ids['worker'],a['deadline']);break
        heartbeat=run/'GUARD_ALIVE.json'
        if time.time()-a['t0']>15 and (not heartbeat.exists() or time.time()-read(heartbeat)['timestamp']>8):
            failure='guard heartbeat stale';stop_target(ids['worker'],a['deadline']);break
        time.sleep(.5)
    try:rc=worker.wait(timeout=max(.1,min(4,a['deadline']-time.time())))
    except subprocess.TimeoutExpired:rc=None
    try:g.wait(timeout=3)
    except subprocess.TimeoutExpired:pass
    write(run/'SUPERVISOR_EXIT.json',{'worker_returncode':rc,'guard_returncode':g.poll(),'failure':failure,'at':time.time(),'deadline':a['deadline'],'no_retry':True})
    if failure or rc!=0 or not (run/'BUILD_RESULT.json').exists():
        write(run/'C02_FINAL_STATUS.json',{'status':'C02_BLOCKED_WITH_SPECIFIC_EVIDENCE','reason':failure or 'worker failure/missing final receipt'})
    else:
        result=read(run/'BUILD_RESULT.json');write(run/'C02_FINAL_STATUS.json',{'status':result['status'],'all_writers_completed':g.poll() is not None,'actual_solution_acceptance':'NOT_RUN_NO_SOLUTION'})
    # Preserve cloud originals. Packaging is inside the same absolute deadline.
    if g.poll() is None or time.time()>=a['deadline']:
        write(run/'CLOUD_SEAL_PENDING.json',{'reason':'writer active or deadline reached','local_sync':'PENDING'});return
    files=[]
    for p in sorted(run.rglob('*')):
        if p.is_file() and p.suffix in {'.json','.jsonl','.log'} and 'mapping' not in p.parts and 'synthetic_checks' not in p.parts and 'lp' not in p.parts:
            if time.time()>=a['deadline']:write(run/'CLOUD_SEAL_PENDING.json',{'reason':'deadline','local_sync':'PENDING'});return
            files.append({'path':str(p.relative_to(run)),'bytes':p.stat().st_size,'sha256':sha(p)})
    write(run/'CLOUD_REVIEW_INDEX.json',{'files':files,'large_artifacts':'ARTIFACT_SHA_INDEX.json','local_sync':'PENDING','originals_retained':True})
    with zipfile.ZipFile(run/'C02_CLOUD_REVIEW.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
        for item in files:z.write(run/item['path'],item['path'])
        z.write(run/'CLOUD_REVIEW_INDEX.json','CLOUD_REVIEW_INDEX.json')
    with zipfile.ZipFile(run/'C02_CLOUD_REVIEW.zip') as z:assert z.testzip() is None
    write(run/'CLOUD_SEAL_COMPLETE.json',{'zip':'C02_CLOUD_REVIEW.zip','sha256':sha(run/'C02_CLOUD_REVIEW.zip'),'crc':'PASS','large_artifacts':'CLOUD_ONLY_LOCAL_SYNC_PENDING','at':time.time(),'deadline':a['deadline']})
if __name__=='__main__':
    run=Path(sys.argv[1]);guard(run) if '--guard' in sys.argv else supervisor(run)
