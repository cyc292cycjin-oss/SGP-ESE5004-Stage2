"""C09 local reception check after `c09_control.py fetch`. Windows stdlib only, no remote calls.

Re-verifies the fetched archive (size, SHA256, full gzip CRC read), checks tar member safety,
extracts into outputs/c09_daily_diagnostic/<run_id>/cloud_run/ (must not exist yet), then checks
BACKUP_INDEX against CLOUD_SEAL_COMPLETE and the cloud archive receipt, every indexed file's
size/SHA256, and the immutable references against the local C09 release and C04 baseline receipt.
"""
from pathlib import Path, PurePosixPath
import json, hashlib, gzip, tarfile, os, sys, time, io

W = Path(__file__).resolve().parents[1]
OUT = Path(r'D:\ResearchWorkspaces\ASEAN\outputs\c09_daily_diagnostic')
BASE = Path(r'D:\ResearchWorkspaces\ASEAN\outputs\c03_daily_diagnostic\c02r_c03_daily122_20261012T044259Z_25e62c10\cloud_run')
C04 = Path(r'D:\ResearchWorkspaces\ASEAN\work\c04_daily_pattern_20261012\C04_BACKUP_RECEIPT.json')
read = lambda p: json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''): h.update(b)
    return h.hexdigest()


def release_member(name):
    with tarfile.open(W / 'C09_RELEASE.tar.gz', 'r:gz') as t:
        return t.extractfile('release/' + name).read()


def main():
    assert not (W / 'C09_LOCAL_BACKUP_RECEIPT.json').exists(), 'ALREADY_RECEIVED'
    fetch = read(W / 'FETCH_RECEIPT.json'); launch = read(W / 'LAUNCH_RECEIPT.json'); d = read(W / 'RELEASE_DELIVERY.json')
    rid = launch['run_id']; archive = Path(fetch['path'])
    assert fetch['status'] == 'LOCAL_ARCHIVE_SHA_VERIFIED' and archive.name == rid + '_NEW_RESULTS.tar.gz'
    assert archive.stat().st_size == fetch['bytes'] and sha(archive) == fetch['sha256'], 'ARCHIVE_SHA'
    snaps = sorted((W / 'monitor_snapshots').glob('*.json'))
    cloud_receipt = read(snaps[-1]).get('_ARCHIVE_RECEIPT.json')
    assert cloud_receipt and cloud_receipt['sha256'] == fetch['sha256'] and cloud_receipt['bytes'] == fetch['bytes']
    with gzip.open(archive, 'rb') as f:
        while f.read(8 * 1024 * 1024): pass
    dest = OUT / rid / 'cloud_run'; dest.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, 'r:gz') as t:
        members = t.getmembers(); names = [m.name for m in members]
        assert len(names) == len(set(names)) == len(set(n.casefold() for n in names))
        assert sum(m.size for m in members) < 3 * 1024 ** 3
        for m in members:
            p = PurePosixPath(m.name)
            assert m.isfile() and not p.is_absolute() and '..' not in p.parts and ':' not in m.name and '\\' not in m.name
            assert all(x and not x.endswith(('.', ' ')) for x in p.parts)
        for m in members:
            p = dest / m.name; p.parent.mkdir(parents=True, exist_ok=True)
            with p.open('xb') as f, t.extractfile(m) as inp:
                while b := inp.read(8 * 1024 * 1024): f.write(b)
                f.flush(); os.fsync(f.fileno())
    idx = read(dest / 'BACKUP_INDEX.json'); seal = read(dest / 'CLOUD_SEAL_COMPLETE.json')
    assert idx['run_id'] == seal['run_id'] == rid
    assert sha(dest / 'BACKUP_INDEX.json') == seal['index_sha256'] == cloud_receipt['index_sha256']
    assert set(names) == {r['relative'] for r in idx['files']} | {'BACKUP_INDEX.json', 'CLOUD_SEAL_COMPLETE.json'}
    for r in idx['files']:
        p = dest / r['relative']; assert p.stat().st_size == r['bytes'] and sha(p) == r['sha256'], r['relative']
    imm = idx['immutable_references']; old = read(C04)
    assert old['status'] == 'LOCAL_BACKUP_SHA_VERIFIED'
    assert sha(BASE / 'BACKUP_INDEX.json') == imm['baseline_BACKUP_INDEX_sha256'] == old['BACKUP_INDEX_sha256']
    assert hashlib.sha256(release_member('SOURCE_BINDING.json')).hexdigest() == imm['source_binding_sha256']
    assert hashlib.sha256(release_member('C09_RELEASE_MANIFEST.json')).hexdigest() == imm['release_manifest_sha256'] == d['release_manifest_sha256']
    oldfiles = {r['relative']: r for r in read(BASE / 'BACKUP_INDEX.json')['files']}
    assert len(imm['files']) == 17369
    for r in imm['files']:
        assert oldfiles[r['relative']] == r and (BASE / r['relative']).stat().st_size == r['bytes']
    out = dict(status='LOCAL_BACKUP_SHA_VERIFIED', run_id=rid, local_run=str(dest), archive_path=str(archive),
               archive_bytes=fetch['bytes'], archive_sha256=fetch['sha256'], BACKUP_INDEX_sha256=seal['index_sha256'],
               gzip_CRC='PASS', tar_path_member_integrity='PASS', indexed_files=len(idx['files']),
               indexed_bytes=sum(r['bytes'] for r in idx['files']), immutable_references=len(imm['files']),
               immutable_validation='Exact match against prior SHA-verified C04 index, C09 release source binding/manifest and file size/existence; no historical bulk copy',
               completed_epoch=time.time(), cloud_originals_preserved=True, files=idx['files'])
    (W / 'C09_LOCAL_BACKUP_RECEIPT.json').write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in out.items() if k != 'files'}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
