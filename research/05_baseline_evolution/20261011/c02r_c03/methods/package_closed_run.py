"""Bounded archival of this already closed run; no solver code or cleanup."""
from pathlib import Path
import sys,time,json,hashlib,tarfile,os
root=Path('/root/autodl-tmp/SGP');run=root/'runs/c02r_c03_daily122_20261012T044259Z_25e62c10';control=root/'incoming/c02r_c03_122_20261012_13a5b85e'
sys.path.insert(0,str(control/'release'))
from c02_common import read,write,sha,resources
from production_control import alive
a=read(run/'AUTHORIZATION.json');deadline=min(a['absolute_deadline_epoch'],read(run/'SUPERVISOR_EXIT.json')['epoch']+1200);assert time.time()<deadline
for name in ['PROCESS_IDENTITY.json','GUARD_READY.json','SUPERVISOR_IDENTITY.json']:
    assert not alive(read(run/name)),name
seal=read(run/'CLOUD_SEAL_COMPLETE.json');assert sha(run/'BACKUP_INDEX.json')==seal['index_sha256']
index=read(run/'BACKUP_INDEX.json')
for ref in index['immutable_references']:assert sha(Path(ref['path']))==ref['sha256']
assert resources(run)['disk_free']>10*1024**3
p=control/(run.name+'_COMPLETE_EVIDENCE.tar.gz');assert not p.exists()
with tarfile.open(p,'x:gz',compresslevel=1) as tar:
    for f in sorted(run.rglob('*')):
        if time.time()>=deadline:raise TimeoutError('FIXED_CLOSEOUT_DEADLINE')
        if f.is_symlink():raise ValueError('UNEXPECTED_SYMLINK')
        if f.is_file():tar.add(f,arcname=str(f.relative_to(run)),recursive=False)
with p.open('rb') as f:os.fsync(f.fileno())
r={'run_id':run.name,'archive':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'backup_index_sha256':seal['index_sha256'],'closed_processes_verified':True,'cloud_originals_preserved':True,'created_epoch':time.time(),'absolute_deadline':a['absolute_deadline_epoch'],'closeout_deadline':deadline}
write(control/'COMPLETE_EVIDENCE_ARCHIVE.json',r);print(json.dumps(r))
