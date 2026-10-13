"""Package D2_RELEASE.tar.gz (read-only block job) or D5_RELEASE.tar.gz (single main-LP solve) with per-file manifests.

python package_d2_d5.py d2
python package_d2_d5.py d5 <D-1 light evidence dir (extracted)>   # needs evidence/D2_CLOUD_READONLY_CHECKS.json from the cloud D-2 job
"""
from pathlib import Path
import hashlib, json, tarfile, io, sys

W = Path(__file__).resolve().parents[1]
sha = lambda b: hashlib.sha256(b).hexdigest()


def tar(files, name):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz', format=tarfile.PAX_FORMAT) as t:
        for k, v in sorted(files.items()):
            ti = tarfile.TarInfo('release/' + k); ti.size = len(v); ti.mtime = 0; ti.mode = 0o644; t.addfile(ti, io.BytesIO(v))
    blob = buf.getvalue(); (W / name).write_bytes(blob); return blob


if sys.argv[1] == 'd2':
    R = W / 'release_d2'; files = {p.name: p.read_bytes() for p in sorted(R.iterdir()) if p.is_file() and p.suffix == '.py'}
    assert set(files) == {'d2_job.py', 'block_tools.py', 'd5_decompose.py', 'adapter.py'}
    assert files['d5_decompose.py'] == (W / 'release_d5/d5_decompose.py').read_bytes() and sha(files['block_tools.py']) == sha((W / 'tools/block_tools.py').read_bytes())
    blob = tar(files, 'D2_RELEASE.tar.gz')
    (W / 'D2_RELEASE_MANIFEST.json').write_text(json.dumps({'files': {k: {'bytes': len(v), 'sha256': sha(v)} for k, v in files.items()}, 'archive_sha256': sha(blob), 'archive_bytes': len(blob)}, indent=1) + '\n')
    print(sha(blob), len(blob))
else:
    L = Path(sys.argv[2]); R = W / 'release_d5'
    checks = json.loads((W / 'evidence/D2_CLOUD_READONLY_CHECKS.json').read_text()); assert checks['status'] == 'PASS'
    (R / 'D5_EXPECTED.json').write_text(json.dumps(checks['expected_for_D5'], indent=1) + '\n')
    (R / 'D2_CLOUD_READONLY_CHECKS.json').write_bytes((W / 'evidence/D2_CLOUD_READONLY_CHECKS.json').read_bytes())
    idx_bytes = (L / 'ARTIFACT_SHA_INDEX.json').read_bytes(); idx = json.loads(idx_bytes); gates = (L / 'D1_BUILD_GATES.json').read_bytes()
    assert json.loads(gates)['status'] == 'D1_BUILD_GATES_PASS'
    launch = json.loads((W / 'D1_LAUNCH_RECEIPT.json').read_text())
    sb = {'baseline_run_id': launch['run_id'], 'baseline_path': launch['run'], 'baseline_ARTIFACT_SHA_INDEX_sha256': sha(idx_bytes),
          'core': {'D1_BUILD_GATES.json': sha(gates), 'BUILD_RESULT.json': sha((L / 'BUILD_RESULT.json').read_bytes())},
          'files': idx['files'], 'file_count': idx['file_count'], 'bytes': idx['bytes'], 'use': 'read-only immutable references; not copied or rebuilt'}
    (R / 'SOURCE_BINDING.json').write_text(json.dumps(sb, indent=1) + '\n')
    skip = lambda p: '__pycache__' in p.parts or p.suffix == '.pyc'
    files = {p.relative_to(R).as_posix(): p.read_bytes() for p in sorted(R.rglob('*')) if p.is_file() and not skip(p.relative_to(R)) and p.name != 'D5_RELEASE_MANIFEST.json'}
    assert json.loads(files['D5_LOCAL_TESTS.json'])['status'] == 'PASS'
    manifest = {'release': 'D5_GATE6_2920_EXACT_DECOMPOSITION_SINGLE_MAIN_LP', 'files': {k: {'bytes': len(v), 'sha256': sha(v)} for k, v in files.items()},
                'derived_from': {'C09 release manifest': '779b8e259f27118e32b77e06f9263b2676e872e72d46028b74e7fa3383077466', 'diffs': 'evidence/DIFF_D5_*.patch'}}
    mb = (json.dumps(manifest, indent=1, sort_keys=True) + '\n').encode(); (R / 'D5_RELEASE_MANIFEST.json').write_bytes(mb); files['D5_RELEASE_MANIFEST.json'] = mb
    blob = tar(files, 'D5_RELEASE.tar.gz'); tag = sha(mb)[:8]
    d = {'release_manifest_sha256': sha(mb), 'archive_bytes': len(blob), 'archive_sha256': sha(blob), 'payload_files': len(files),
         'remote_control': '/root/autodl-tmp/SGP/incoming/d5_main2920_122_20261013_' + sha(blob)[:8],
         'remote_release': '/root/autodl-tmp/SGP/incoming/d5_main2920_122_20261013_' + sha(blob)[:8] + '/release'}
    (W / 'D5_RELEASE_DELIVERY.json').write_text(json.dumps(d, indent=1) + '\n'); print(json.dumps(d, indent=1))
