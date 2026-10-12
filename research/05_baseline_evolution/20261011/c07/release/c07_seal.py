"""New-results-only seal. Inputs remain immutable references; bounded standalone guard."""
from pathlib import Path
import sys,os,time,subprocess,signal,tarfile,hashlib,json
from c02_common import read,write,sha,resources,resource_gate
from production_control import alive,ident,resources as process_resources
HERE=Path(__file__).resolve().parent

def gate(run,deadline):
    if time.time()>=deadline:raise TimeoutError('SEAL_FIXED_DEADLINE')
    resource_gate(resources(run))

def seal(run,deadline):
    a=read(run/'AUTHORIZATION.json');source=read(HERE/'SOURCE_BINDING.json')
    assert not read(run/'GUARD_EXIT.json')['residual_live_pids']
    assert not alive(read(run/'PROCESS_IDENTITY.json')) and not alive(read(run/'GUARD_READY.json'))
    files=[]
    for p in sorted(run.rglob('*')):
        gate(run,deadline)
        if p.is_symlink():
            assert p.parent==run and p.name in ('artifacts','bridge') and p.resolve()==Path(source['baseline_path'])/p.name
            continue
        if not p.is_file() or p.name in ('BACKUP_INDEX.json','CLOUD_SEAL_COMPLETE.json'):continue
        with p.open('rb') as f:os.fsync(f.fileno())
        files.append({'relative':str(p.relative_to(run)),'bytes':p.stat().st_size,'sha256':sha(p)})
    write(run/'BACKUP_INDEX.json',{'run_id':a['run_id'],'files':files,'cloud_originals_preserved':True,'local_sync':'LOCAL_SYNC_PENDING','immutable_references':{'baseline_path':source['baseline_path'],'baseline_BACKUP_INDEX_sha256':source['baseline_BACKUP_INDEX_sha256'],'source_binding_path':str(HERE/'SOURCE_BINDING.json'),'source_binding_sha256':sha(HERE/'SOURCE_BINDING.json'),'release_manifest_path':str(HERE/'C07_RELEASE_MANIFEST.json'),'release_manifest_sha256':a['release_manifest_sha256'],'files':source['files']},'qualification':'USE_POSTPROCESS_AND_NATIVE_RECEIPTS'})
    write(run/'CLOUD_SEAL_COMPLETE.json',{'run_id':a['run_id'],'index_sha256':sha(run/'BACKUP_INDEX.json'),'file_count':len(files),'bytes':sum(x['bytes'] for x in files),'epoch':time.time(),'local_sync':'LOCAL_SYNC_PENDING','no_solve_retry':True})
    dest=HERE.parent/(a['run_id']+'_NEW_RESULTS.tar.gz');part=dest.with_name(dest.name+'.partial')
    with tarfile.open(part,'x:gz',compresslevel=1) as t:
        for rel in [r['relative'] for r in files]+['BACKUP_INDEX.json','CLOUD_SEAL_COMPLETE.json']:
            gate(run,deadline);t.add(run/rel,arcname=rel,recursive=False)
    with part.open('rb') as f:os.fsync(f.fileno())
    gate(run,deadline);os.rename(part,dest)
    write(HERE.parent/(a['run_id']+'_ARCHIVE_RECEIPT.json'),{'run_id':a['run_id'],'archive':str(dest),'bytes':dest.stat().st_size,'sha256':sha(dest),'new_results_only':True,'index_sha256':sha(run/'BACKUP_INDEX.json'),'deadline_epoch':deadline,'completed_epoch':time.time()})

def guarded_seal(run):
    a=read(run/'AUTHORIZATION.json');deadline=min(time.time()+1050,a['absolute_deadline_epoch'])
    control=HERE.parent/(a['run_id']+'_SEAL_CONTROL.json')
    write(control,{'run':str(run),'deadline_epoch':deadline,'authorization_sha256':sha(run/'AUTHORIZATION.json')})
    # Separate detached guard supervises seal even if the original supervisor disappears.
    with (HERE.parent/(a['run_id']+'_seal_guard.log')).open('xb') as log:
        p=subprocess.Popen([sys.executable,'-B',str(HERE/'c07_seal.py'),'guard',str(control)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    p.wait()

def guard(control):
    cfg=read(control);run=Path(cfg['run']);a=read(run/'AUTHORIZATION.json');deadline=cfg['deadline_epoch']
    output=HERE.parent/(a['run_id']+'_SEAL_GUARD_RECEIPT.json');records=[];reason=None
    if time.time()>=deadline:
        write(output,{'status':'CLOUD_SEAL_PENDING','reason':'TOTAL_DEADLINE','retry':False});return
    with (HERE.parent/(a['run_id']+'_seal.log')).open('xb') as log:
        child=subprocess.Popen([sys.executable,'-B',str(HERE/'c07_seal.py'),'seal',str(run),str(deadline)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    expected=ident(child.pid,a['run_id']);term=None
    while child.poll() is None:
        now=time.time()
        try:r=process_resources(child.pid,run,a['resource_limits']);reason=r['reason'] or ('SEAL_DEADLINE' if now>=deadline-5 else None)
        except Exception:r={'epoch':now};reason='SEAL_MONITOR_UNAVAILABLE'
        records.append(r)
        if reason and term is None:
            if alive(expected):os.kill(child.pid,signal.SIGTERM)
            term=now
        if term is not None and (now-term>=5 or now>=deadline):
            if alive(expected):os.kill(child.pid,signal.SIGKILL)
        time.sleep(.25)
    write(output,{'status':'SEALED' if child.returncode==0 else 'CLOUD_SEAL_PENDING','exit_code':child.returncode,'identity':expected,'deadline_epoch':deadline,'ended_epoch':time.time(),'reason':reason,'samples':records,'retry':False})

if __name__=='__main__':
    if sys.argv[1]=='guard':guard(Path(sys.argv[2]))
    elif sys.argv[1]=='seal':seal(Path(sys.argv[2]),float(sys.argv[3]))
    else:raise SystemExit('guard or seal only')
