"""Seal closed scientific products. No native or model dependency."""
from pathlib import Path
import sys,os,time,zipfile,json
from c02_common import read,write,sha
def main(run):
    a=read(run/'AUTHORIZATION.json');assert time.time()<a['absolute_deadline_epoch']
    assert not read(run/'GUARD_EXIT.json')['residual_live_pids']
    from production_control import alive
    assert not alive(read(run/'PROCESS_IDENTITY.json')) and not alive(read(run/'GUARD_READY.json'))
    files=[]
    for p in sorted(run.rglob('*')):
        if not p.is_file() or p.name in ('BACKUP_INDEX.json','CLOUD_SEAL_COMPLETE.json','REVIEW_EVIDENCE.zip'):continue
        if p.is_symlink():raise ValueError('UNEXPECTED_LINK_IN_RUN')
        if time.time()>=a['absolute_deadline_epoch']:raise TimeoutError('SEAL_DEADLINE')
        with p.open('rb') as f:os.fsync(f.fileno())
        files.append({'relative':str(p.relative_to(run)),'bytes':p.stat().st_size,'sha256':sha(p)})
    write(run/'BACKUP_INDEX.json',{'run_id':a['run_id'],'files':files,'cloud_originals_preserved':True,'local_sync':'LOCAL_SYNC_PENDING','immutable_references':[{'path':a['daily_source'],'sha256':a['daily_source_sha256']},{'path':a['release']+'/C03_RELEASE_MANIFEST.json','sha256':a['release_manifest_sha256']}],'qualification':'USE_POSTPROCESS_AND_NATIVE_RECEIPTS'})
    write(run/'CLOUD_SEAL_COMPLETE.json',{'run_id':a['run_id'],'index_sha256':sha(run/'BACKUP_INDEX.json'),'file_count':len(files),'bytes':sum(x['bytes'] for x in files),'epoch':time.time(),'local_sync':'LOCAL_SYNC_PENDING','no_solve_retry':True})
    with zipfile.ZipFile(run/'REVIEW_EVIDENCE.zip','x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(run.rglob('*')):
            if p.is_file() and p.suffix in ('.json','.jsonl','.log') and p.stat().st_size<20*1024**2:z.write(p,p.relative_to(run))
    with zipfile.ZipFile(run/'REVIEW_EVIDENCE.zip') as z:assert z.testzip() is None
if __name__=='__main__':main(Path(sys.argv[1]))
