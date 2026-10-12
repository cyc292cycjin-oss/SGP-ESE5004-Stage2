"""One authorized 60-minute reception window, existing sealed archives only.
No retries, no repacking, no historical input duplication. Windows stdlib only.
"""
from pathlib import Path,PurePosixPath
import json,subprocess,time,os,shlex,tarfile,gzip,sys
from local_control import W,SSH,PY,remote,save,sha
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
BASE=Path(r'D:\ResearchWorkspaces\ASEAN\outputs\c03_daily_diagnostic\c02r_c03_daily122_20261012T044259Z_25e62c10\cloud_run')

def verify(v,archive,source):
 rid=source['run_id'];assert archive.stat().st_size==source['bytes'] and sha(archive)==source['sha256']
 with gzip.open(archive,'rb') as f:
  while f.read(8*1024**2):pass
 dest=Path(r'D:\ResearchWorkspaces\ASEAN\outputs\c07_daily_diagnostic')/rid/'cloud_run'
 dest.mkdir(parents=True,exist_ok=False)
 with tarfile.open(archive,'r:gz') as t:
  members=t.getmembers();names=[x.name for x in members];assert len(names)==len(set(names)) and len(names)==len(set(x.casefold() for x in names))
  assert sum(x.size for x in members)<3*1024**3
  for m in members:
   p=PurePosixPath(m.name)
   assert m.isfile() and not p.is_absolute() and '..' not in p.parts and ':' not in m.name and '\\' not in m.name
   assert all(x and not x.endswith(('.',' ')) for x in p.parts)
  for m in members:
   p=dest/m.name;p.parent.mkdir(parents=True,exist_ok=True)
   with p.open('xb') as f,t.extractfile(m) as inp:
    while b:=inp.read(8*1024**2):f.write(b)
    f.flush();os.fsync(f.fileno())
 idx=read(dest/'BACKUP_INDEX.json');seal=read(dest/'CLOUD_SEAL_COMPLETE.json')
 assert idx['run_id']==seal['run_id']==rid
 assert sha(dest/'BACKUP_INDEX.json')==seal['index_sha256']==source['index_sha256']
 assert set(names)=={r['relative'] for r in idx['files']}|{'BACKUP_INDEX.json','CLOUD_SEAL_COMPLETE.json'}
 for r in idx['files']:
  p=dest/r['relative'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],r['relative']
 old=read(Path(r'D:\ResearchWorkspaces\ASEAN\work\c04_daily_pattern_20261012\C04_BACKUP_RECEIPT.json'))
 imm=idx['immutable_references'];assert old['status']=='LOCAL_BACKUP_SHA_VERIFIED'
 assert sha(BASE/'BACKUP_INDEX.json')==imm['baseline_BACKUP_INDEX_sha256']==old['BACKUP_INDEX_sha256']
 assert sha(W/'release/SOURCE_BINDING.json')==imm['source_binding_sha256']
 assert sha(W/'release/C07_RELEASE_MANIFEST.json')==imm['release_manifest_sha256']
 oldfiles={r['relative']:r for r in read(BASE/'BACKUP_INDEX.json')['files']}
 assert len(imm['files'])==17369
 for r in imm['files']:assert oldfiles[r['relative']]==r and (BASE/r['relative']).stat().st_size==r['bytes']
 out=dict(status='LOCAL_BACKUP_SHA_VERIFIED',run_id=rid,local_run=str(dest),archive_path=str(archive),archive_bytes=source['bytes'],archive_sha256=source['sha256'],BACKUP_INDEX_sha256=source['index_sha256'],gzip_CRC='PASS',tar_path_member_integrity='PASS',indexed_files=len(idx['files']),indexed_bytes=sum(r['bytes'] for r in idx['files']),immutable_references=len(imm['files']),immutable_validation='Exact match against prior SHA-verified C04 index, source binding and file size/existence; no repeated historical bulk copy',completed_epoch=time.time(),cloud_originals_preserved=True,files=idx['files'])
 save(v+'_LOCAL_BACKUP_RECEIPT.json',out);print(v+' LOCAL_BACKUP_SHA_VERIFIED',flush=True)

def receive(variants):
 d=read(W/'RELEASE_DELIVERY.json');sources={}
 for v in variants:
  if (W/(v+'_LOCAL_BACKUP_RECEIPT.json')).exists():
   q=read(W/(v+'_LOCAL_BACKUP_RECEIPT.json'));assert sha(Path(q['archive_path']))==q['archive_sha256'];continue
  run=read(W/(v+'_LAUNCH_RECEIPT.json'))['run_id']
  code=f'''from pathlib import Path
import json,sys,socket,hashlib
assert socket.gethostname()=='autodl-container-21104cb00b-43be1fed'
sys.path.insert(0,{d['remote_release']!r})
from production_control import alive
from c02_common import read,sha
r=Path('/root/autodl-tmp/SGP/runs')/{run!r};c=Path({d['remote_control']!r})
assert all(not alive(read(r/n)) for n in ['PROCESS_IDENTITY.json','SUPERVISOR_IDENTITY.json','GUARD_READY.json'])
assert read(c/({run!r}+'_SEAL_GUARD_RECEIPT.json'))['status']=='SEALED'
a=read(c/({run!r}+'_ARCHIVE_RECEIPT.json'));p=Path(a['archive']);assert p.stat().st_size==a['bytes'] and sha(p)==a['sha256']
a.update(inode=p.stat().st_ino,mtime_ns=p.stat().st_mtime_ns);print(json.dumps(a))'''
  sources[v]=remote(code,60)
 save('C07_TRANSFER_SOURCE_IDENTITIES.json',sources)
 if not sources:return
 t0=time.time();deadline=t0+3600
 save('C07_TRANSFER_WINDOW.json',dict(t0_epoch=t0,deadline_epoch=deadline,seconds=3600,authorization='C07 explicit user authorization separate new-results reception',automatic_retry=False,archives={k:v['run_id'] for k,v in sources.items()}))
 # Receive all archives before local extraction; local verification is not billed to the reception clock.
 for v,a in sources.items():
  archive=W/(a['run_id']+'_NEW_RESULTS.tar.gz');partial=archive.with_name(archive.name+'.partial')
  try:
   assert not archive.exists() and not partial.exists() and time.time()<deadline
   code=f'''from pathlib import Path
import sys,time
p=Path({a['archive']!r});s=p.stat();assert s.st_size=={a['bytes']} and s.st_ino=={a['inode']} and s.st_mtime_ns=={a['mtime_ns']}
with p.open('rb') as f:
 while time.time()<{deadline}:
  b=f.read(1024*1024)
  if not b:break
  sys.stdout.buffer.write(b);sys.stdout.buffer.flush()
'''
   print(v+' receiving '+str(a['bytes'])+' bytes; fixed deadline '+str(deadline),flush=True)
   with partial.open('xb') as f:
    r=subprocess.run(SSH+[PY+' -B -c '+shlex.quote(code)],stdout=f,stderr=subprocess.PIPE,timeout=max(1,deadline-time.time()));f.flush();os.fsync(f.fileno())
   assert r.returncode==0 and partial.stat().st_size==a['bytes'],'RECEPTION_INCOMPLETE_NO_RETRY'
   assert sha(partial)==a['sha256'],'ARCHIVE_SHA_MISMATCH'
   os.link(partial,archive) # retain successful reception evidence, no second data copy
   save(v+'_TRANSFER_COMPLETE.json',dict(run_id=a['run_id'],bytes=a['bytes'],sha256=a['sha256'],archive=str(archive),completed_epoch=time.time(),deadline_epoch=deadline))
   print(v+' reception SHA PASS',flush=True)
  except Exception as e:
   save(v+'_LOCAL_SYNC_PENDING.json',dict(status='LOCAL_SYNC_PENDING',error=type(e).__name__+': '+str(e),partial=str(partial),bytes=partial.stat().st_size if partial.exists() else 0,deadline_epoch=deadline,cloud_originals_preserved=True,no_retry=True))
   print(v+' LOCAL_SYNC_PENDING '+str(e),flush=True);break
 for v,a in sources.items():
  archive=W/(a['run_id']+'_NEW_RESULTS.tar.gz')
  if archive.exists():verify(v,archive,a)

if __name__=='__main__':receive(sys.argv[1:] or ['A','B'])
