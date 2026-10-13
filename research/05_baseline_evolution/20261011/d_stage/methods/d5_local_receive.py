"""D-5 本地接收核验（由 c09_local_receive.py 改写；仅 Windows 标准库，不连云端）。

重新核对归档（大小、SHA256、完整 gzip CRC 读取）、tar 成员安全，解压到 outputs/d_2920_diagnostic/<run_id>/cloud_run/（必须是新目录），
再核对 BACKUP_INDEX 与 CLOUD_SEAL_COMPLETE、云端归档回执、每个索引文件的大小/SHA256，以及不可变引用
（D-1 ARTIFACT_SHA_INDEX 由本地 d1_light 副本核对，SOURCE_BINDING/发布清单由本地 D5 发布包核对）。
"""
from pathlib import Path, PurePosixPath
import json, hashlib, gzip, tarfile, os, time, io, sys

W = Path(__file__).resolve().parents[1]; OUT = W.parents[1] / 'outputs/d_2920_diagnostic'
P = sys.argv[1] if len(sys.argv) > 1 else 'D5'
read = lambda p: json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''): h.update(b)
    return h.hexdigest()


def release_member(name):
    with tarfile.open(W / (P + '_RELEASE.tar.gz'), 'r:gz') as t: return t.extractfile('release/' + name).read()


def main():
    assert not (W / (P + '_LOCAL_BACKUP_RECEIPT.json')).exists(), 'ALREADY_RECEIVED'
    fetch = read(W / (P + '_FETCH_RECEIPT.json')); launch = read(W / (P + '_LAUNCH_RECEIPT.json')); d = read(W / (P + '_RELEASE_DELIVERY.json'))
    rid = launch['run_id']; archive = Path(fetch['path'])
    assert fetch['status'] == 'LOCAL_ARCHIVE_SHA_VERIFIED' and archive.name == rid + '_NEW_RESULTS.tar.gz'
    assert archive.stat().st_size == fetch['bytes'] and sha(archive) == fetch['sha256'], 'ARCHIVE_SHA'
    snaps = sorted((W / 'monitor_snapshots').glob(P + '_*.json')); cloud_receipt = read(snaps[-1]).get('_ARCHIVE_RECEIPT.json')
    assert cloud_receipt and cloud_receipt['sha256'] == fetch['sha256'] and cloud_receipt['bytes'] == fetch['bytes']
    with gzip.open(archive, 'rb') as f:
        while f.read(8 * 1024 * 1024): pass
    dest = OUT / rid / 'cloud_run'; dest.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, 'r:gz') as t:
        members = t.getmembers(); names = [m.name for m in members]
        assert len(names) == len(set(names)) == len(set(n.casefold() for n in names)) and sum(m.size for m in members) < 12 * 1024 ** 3
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
    imm = idx['immutable_references']
    assert sha(W / 'd1_light/ARTIFACT_SHA_INDEX.json') == imm['baseline_ARTIFACT_SHA_INDEX_sha256']
    assert hashlib.sha256(release_member('SOURCE_BINDING.json')).hexdigest() == imm['source_binding_sha256']
    assert hashlib.sha256(release_member(P + '_RELEASE_MANIFEST.json')).hexdigest() == imm['release_manifest_sha256'] == d['release_manifest_sha256']
    local_idx = {r['relative']: r for r in read(W / 'd1_light/ARTIFACT_SHA_INDEX.json')['files']}
    assert len(imm['files']) == len(local_idx) and all(local_idx[r['relative']] == r for r in imm['files'])
    out = dict(status='LOCAL_BACKUP_SHA_VERIFIED', run_id=rid, local_run=str(dest), archive_path=str(archive), archive_bytes=fetch['bytes'], archive_sha256=fetch['sha256'],
               BACKUP_INDEX_sha256=seal['index_sha256'], gzip_CRC='PASS', tar_path_member_integrity='PASS', indexed_files=len(idx['files']),
               indexed_bytes=sum(r['bytes'] for r in idx['files']), immutable_references=len(imm['files']),
               immutable_validation='D-1 artifact references equal the locally held, SHA-verified D-1 ARTIFACT_SHA_INDEX; source binding and release manifest equal the local D5 release',
               completed_epoch=time.time(), cloud_originals_preserved=True, files=idx['files'])
    (W / (P + '_LOCAL_BACKUP_RECEIPT.json')).write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in out.items() if k != 'files'}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
