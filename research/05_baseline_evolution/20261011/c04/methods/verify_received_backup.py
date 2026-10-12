"""Safely validate/extract existing C03 archive; no model code is imported."""
from pathlib import Path,PurePosixPath
import gzip,tarfile,hashlib,json,os,time
BASE=Path('D:/ResearchWorkspaces/ASEAN' if os.name=='nt' else '/mnt/d/ResearchWorkspaces/ASEAN')
W=BASE/'work/c04_daily_pattern_20261012'
OLD=BASE/'work/c02r_c03_combined_20261012'
RUN='c02r_c03_daily122_20261012T044259Z_25e62c10'
archive=W/(RUN+'_COMPLETE_EVIDENCE.tar.gz')
dest=BASE/'outputs/c03_daily_diagnostic'/RUN/'cloud_run'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_text())
rec=read(W/'ARCHIVE_RECEPTION_RECEIPT.json');assert rec['status']=='ARCHIVE_SIZE_SHA_VERIFIED'
assert archive.stat().st_size==314868916 and sha(archive)==rec['archive_sha256']
uncompressed=0
with gzip.open(archive,'rb') as f:
    while b:=f.read(8*1024**2):
        uncompressed+=len(b);assert uncompressed<3*1024**3
assert not (W/'C04_BACKUP_RECEIPT.json').exists()
if dest.exists():assert (W/'LOCAL_VALIDATOR_BACKEND_SWITCH.json').exists()
dest.mkdir(parents=True,exist_ok=True)
reused=0;quarantined=[]
with tarfile.open(archive,'r:gz') as t:
    members=t.getmembers();seen=set();casefold=set()
    embedded_index=json.load(t.extractfile('BACKUP_INDEX.json'))
    expected={r['relative']:r['sha256'] for r in embedded_index['files']}
    for m in members:
        p=PurePosixPath(m.name)
        assert m.isfile() and not p.is_absolute() and '..' not in p.parts and '\\' not in m.name and ':' not in m.name and str(p)==m.name,m.name
        assert m.name not in seen and m.name.casefold() not in casefold,m.name
        assert all(x not in ('','.','..') and not x.endswith((' ','.')) for x in p.parts)
        seen.add(m.name);casefold.add(m.name.casefold())
    for m in members:
        out=dest/m.name;out.parent.mkdir(parents=True,exist_ok=True)
        if out.exists():
            identity=expected.get(m.name)
            if identity is None:identity=hashlib.sha256(t.extractfile(m).read()).hexdigest()
            if out.is_file() and not out.is_symlink() and out.stat().st_size==m.size and sha(out)==identity:
                reused+=1;continue
            # Preserve an interrupted new local copy, never touch a cloud original.
            q=W/'interrupted_local_extraction'/m.name
            assert out.resolve().is_relative_to(dest.resolve()) and q.resolve().is_relative_to(W.resolve())
            assert out.is_file() and not out.is_symlink() and not q.exists()
            q.parent.mkdir(parents=True,exist_ok=True);out.rename(q);quarantined.append(m.name)
        with t.extractfile(m) as src,out.open('xb') as f:
            for b in iter(lambda:src.read(8*1024**2),b''):f.write(b)
            f.flush();os.fsync(f.fileno())
seal=read(dest/'CLOUD_SEAL_COMPLETE.json');idx=read(dest/'BACKUP_INDEX.json')
assert seal['run_id']==RUN and sha(dest/'BACKUP_INDEX.json')==seal['index_sha256']=='eb80de5b50ff64d976d23066c514811fcc4f80f9b768f62ade1b6e1b4282d47d'
records=[]
for r in idx['files']:
    name=r['relative'];p=dest/name
    assert name in seen and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],name
    records.append({**r,'verified':True})
assert len(records)==seal['file_count']==17417
assert sum(x['bytes'] for x in records)==seal['bytes']==1946512966
refs=[]
for r in idx['immutable_references']:
    source=r.get('path','')
    if source.endswith('daily_365_unsolved.nc'):p=dest/'artifacts/daily_365_unsolved.nc'
    elif source.endswith('C03_RELEASE_MANIFEST.json'):p=OLD/'release/C03_RELEASE_MANIFEST.json'
    else:raise ValueError(('unrecognized immutable reference',r))
    assert sha(p)==r['sha256']
    refs.append({**r,'local_verified_path':str(p),'verified':True})
release=read(OLD/'release/C03_RELEASE_MANIFEST.json')
for name,r in release['files'].items():
    p=OLD/'release'/name
    assert p.is_relative_to(OLD/'release') and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],name
result=dict(status='LOCAL_BACKUP_SHA_VERIFIED',run_id=RUN,archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),gzip_full_stream_CRC='PASS',tar_paths_unique_regular_safe='PASS',tar_members=len(members),uncompressed_tar_bytes=uncompressed,indexed_files_verified=len(records),indexed_bytes=sum(x['bytes'] for x in records),BACKUP_INDEX_sha256=sha(dest/'BACKUP_INDEX.json'),immutable_references=refs,local_run=str(dest),cloud_originals_preserved=True,old_partial_preserved=True,verification_end_epoch=time.time(),transfer_receipt_sha256=sha(W/'ARCHIVE_RECEPTION_RECEIPT.json'),scope='new C04 transfer window; local verification after transfer',files=records)
with (W/'LOCAL_BACKUP_VERIFICATION.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
result['immutable_release_files_verified']=len(release['files'])
result['native_IO_resume']={'prior_complete_files_verified_and_reused':reused,'interrupted_local_copies_preserved':quarantined,'network_retries':0}
light={k:v for k,v in result.items() if k!='files'}
(W/'C04_BACKUP_RECEIPT.json').write_text(json.dumps(light,indent=2)+'\n')
print(json.dumps(light,indent=2))
