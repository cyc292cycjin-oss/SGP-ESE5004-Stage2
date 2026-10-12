"""Windows-native local verification of only new C05 files; old inputs referenced."""
from pathlib import Path,PurePosixPath
import json,hashlib,tarfile,gzip,os,time
W=Path(r'D:\ResearchWorkspaces\ASEAN\work\c05_aggregate0_20261012')
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
L=read(W/'LAUNCH_RECEIPT.json');RID=L['run_id']
SOURCE=read(W/'C05_ARCHIVE_SOURCE_IDENTITY.json');A=SOURCE['archive'];archive=W/(RID+'_NEW_RESULTS.tar.gz')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
assert archive.stat().st_size==A['bytes'] and sha(archive)==A['sha256']
with gzip.open(archive,'rb') as f:
 while f.read(8*1024**2):pass
dest=Path(r'D:\ResearchWorkspaces\ASEAN\outputs\c05_daily_diagnostic')/RID/'cloud_run';dest.mkdir(parents=True,exist_ok=False)
with tarfile.open(archive,'r:gz') as t:
 members=t.getmembers();names=[m.name for m in members];assert len(names)==len(set(names))
 for m in members:
  p=PurePosixPath(m.name)
  assert m.isfile() and not p.is_absolute() and '..' not in p.parts and ':' not in m.name and '\\' not in m.name
  assert all(x and not x.endswith(('.',' ')) for x in p.parts)
 for m in members:
  p=dest/m.name;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f,t.extractfile(m) as src:
   while b:=src.read(8*1024**2):f.write(b)
   f.flush();os.fsync(f.fileno())
index=read(dest/'BACKUP_INDEX.json');seal=read(dest/'CLOUD_SEAL_COMPLETE.json')
assert index['run_id']==seal['run_id']==RID
assert sha(dest/'BACKUP_INDEX.json')==seal['index_sha256']==A['index_sha256']
assert set(names)=={r['relative'] for r in index['files']}|{'BACKUP_INDEX.json','CLOUD_SEAL_COMPLETE.json'}
verified=[]
for r in index['files']:
 p=dest/r['relative'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],r['relative'];verified.append(dict(r,verified=True))
old=Path(r'D:\ResearchWorkspaces\ASEAN\outputs\c03_daily_diagnostic\c02r_c03_daily122_20261012T044259Z_25e62c10\cloud_run')
oldreceipt=read(Path(r'D:\ResearchWorkspaces\ASEAN\work\c04_daily_pattern_20261012\C04_BACKUP_RECEIPT.json'))
assert oldreceipt['status']=='LOCAL_BACKUP_SHA_VERIFIED'
imm=index['immutable_references'];assert sha(old/'BACKUP_INDEX.json')==imm['baseline_BACKUP_INDEX_sha256']==oldreceipt['BACKUP_INDEX_sha256']
assert sha(W/'release/SOURCE_BINDING.json')==imm['source_binding_sha256']
oldfiles={r['relative']:r for r in read(old/'BACKUP_INDEX.json')['files']}
assert len(imm['files'])==17369
for r in imm['files']:assert oldfiles[r['relative']]==r and (old/r['relative']).stat().st_size==r['bytes']
assert sha(W/'release/C05_RELEASE_MANIFEST.json')==imm['release_manifest_sha256']
rec={'status':'LOCAL_BACKUP_SHA_VERIFIED','run_id':RID,'archive_path':str(archive),'archive_bytes':A['bytes'],'archive_sha256':A['sha256'],'gzip_CRC':'PASS','tar_path_and_member_safety':'PASS','indexed_files':len(verified),'indexed_bytes':sum(r['bytes'] for r in verified),'BACKUP_INDEX_sha256':seal['index_sha256'],'local_run':str(dest),'immutable_files':len(imm['files']),'immutable_validation':'exact match against C04 SHA-verified original index and size/existence; no repeated old bulk download','baseline_local_run':str(old),'old_C04_receipt_sha256':sha(Path(r'D:\ResearchWorkspaces\ASEAN\work\c04_daily_pattern_20261012\C04_BACKUP_RECEIPT.json')),'old_originals_preserved':True,'completed_epoch':time.time(),'files':verified}
(W/'C05_LOCAL_BACKUP_RECEIPT.json').write_text(json.dumps(rec,indent=2)+'\n')
print(json.dumps({k:v for k,v in rec.items() if k!='files'},indent=2))
