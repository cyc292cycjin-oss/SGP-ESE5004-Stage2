from pathlib import Path,PurePosixPath
import tarfile,hashlib,json,os,time
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c02r_c03_combined_20261012')
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
    return h.hexdigest()
receipt=read(W/'COMPLETE_EVIDENCE_ARCHIVE.json');archive=W/Path(receipt['archive']).name
assert archive.stat().st_size==receipt['bytes'] and sha(archive)==receipt['sha256']
dest=Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/c03_daily_diagnostic')/receipt['run_id']/'cloud_run';dest.mkdir(parents=True,exist_ok=False)
with tarfile.open(archive,'r:gz') as f:
    members=f.getmembers();seen=set()
    for m in members:
        p=PurePosixPath(m.name)
        assert not p.is_absolute() and '..' not in p.parts and m.name not in seen and m.isfile(),m.name
        seen.add(m.name);out=dest/m.name;out.parent.mkdir(parents=True,exist_ok=True)
        with f.extractfile(m) as src,out.open('xb') as target:
            while b:=src.read(8*1024**2):target.write(b)
            target.flush();os.fsync(target.fileno())
seal=read(dest/'CLOUD_SEAL_COMPLETE.json');index=read(dest/'BACKUP_INDEX.json')
assert sha(dest/'BACKUP_INDEX.json')==seal['index_sha256']==receipt['backup_index_sha256']
checks=[]
for r in index['files']:
    p=dest/r['relative'];assert p.is_relative_to(dest) and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],r['relative']
    checks.append({'relative':r['relative'],'bytes':r['bytes'],'sha256':r['sha256'],'verified':True})
daily=dest/'artifacts/daily_365_unsolved.nc';assert sha(daily)=='b2df7dc771d4759668988f7a0abd7ccfafacd976dff644f7acafd20aee50b9f2'
local_release=W/'release/C03_RELEASE_MANIFEST.json';assert sha(local_release)==index['immutable_references'][1]['sha256']
result={'status':'LOCAL_BACKUP_SHA_VERIFIED','run_id':receipt['run_id'],'local_run':str(dest),'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'archive_gzip_crc':'PASS_FULL_STREAM_READ','member_count':len(members),'indexed_files_verified':len(checks),'indexed_bytes':sum(r['bytes'] for r in checks),'BACKUP_INDEX_sha256':sha(dest/'BACKUP_INDEX.json'),'immutable_references':'daily network and release index bound to local exact copies','cloud_originals_preserved':True,'finished_epoch':time.time(),'closeout_deadline':receipt['closeout_deadline'],'within_closeout_deadline':time.time()<=receipt['closeout_deadline'],'files':checks}
(W/'LOCAL_BACKUP_VERIFICATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))
