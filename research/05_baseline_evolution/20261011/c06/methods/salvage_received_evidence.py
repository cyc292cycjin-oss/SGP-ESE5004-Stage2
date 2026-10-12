"""Read only the existing verified-offset transfer pieces. No network operations.
Recover complete regular tar members to an independent partial-evidence directory.
This is not a complete archive/CRC verification and does not complete the backup.
"""
from pathlib import Path, PurePosixPath
import io, gzip, tarfile, json, hashlib, os, time
W=Path(r'D:\ResearchWorkspaces\ASEAN\work\c06_barconvtol_20261012')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
RID=read(W/'LAUNCH_RECEIPT.json')['run_id']
parts=[W/(RID+'_NEW_RESULTS.tar.gz.partial'),W/'C06_RESUME_SUFFIX.partial']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
assert parts[0].stat().st_size==27656192
assert sha(parts[0])=='6ad86139fb01d9435ed705b9a8aceabf8f8c80d12aa804ac9ea02690676de8b7'
assert read(W/'C06_RESUME_LOCAL_SYNC_PENDING.json')['prefix_bytes']==parts[0].stat().st_size
class Pieces(io.RawIOBase):
 def __init__(self): self.f=[p.open('rb') for p in parts];self.i=0
 def readable(self):return True
 def read(self,n=-1):
  if self.i==len(self.f):return b''
  b=self.f[self.i].read(n)
  if not b:self.i+=1;return self.read(n)
  return b
DEST=W/'recovered_partial_evidence'
DEST.mkdir(exist_ok=False)
records=[];error=None;pending=None;seen=set()
try:
 with gzip.GzipFile(fileobj=Pieces(),mode='rb') as gz,tarfile.open(fileobj=gz,mode='r|') as t:
  for m in t:
   p=PurePosixPath(m.name)
   assert m.isfile() and not p.is_absolute() and '..' not in p.parts and ':' not in m.name and '\\' not in m.name
   assert m.name not in seen and all(x and not x.endswith(('.',' ')) for x in p.parts)
   seen.add(m.name);target=DEST/m.name;target.parent.mkdir(parents=True,exist_ok=True)
   tmp=target.with_name(target.name+'.incomplete');count=0
   pending={'relative':m.name,'expected_bytes':m.size}
   with t.extractfile(m) as src,tmp.open('xb') as f:
    while b:=src.read(2**20):f.write(b);count+=len(b)
    f.flush();os.fsync(f.fileno())
   assert count==m.size
   tmp.rename(target)
   records.append({'relative':m.name,'bytes':count,'sha256':sha(target),'tar_member_complete':True})
   print(m.name,count,flush=True);pending=None
except Exception as e:error={'type':type(e).__name__,'message':str(e)}
source=read(W/'C06_ARCHIVE_SOURCE_IDENTITY.json')['archive']
rec={'status':'PARTIAL_ARCHIVE_MEMBERS_RECOVERED_NOT_FULL_BACKUP','run_id':RID,'local_directory':str(DEST),
 'source_archive':source,'pieces':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in parts],
 'received_compressed_bytes':sum(p.stat().st_size for p in parts),'missing_compressed_bytes':source['bytes']-sum(p.stat().st_size for p in parts),
 'member_records':records,'incomplete_member':pending,'termination':error,'archive_SHA256_verified':False,'gzip_CRC_verified':False,
 'remote_operations':0,'historical_partial_files_modified':False,'time':time.time()}
(W/'C06_PARTIAL_EVIDENCE_RECOVERY.json').write_text(json.dumps(rec,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in rec.items() if k not in ('member_records','pieces','source_archive')},indent=2))
