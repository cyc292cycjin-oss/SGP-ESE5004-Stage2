"""Build D1_RELEASE.tar.gz (release/ prefix) with a per-file manifest; originals and caches excluded."""
from pathlib import Path
import hashlib, json, tarfile, io, sys

W = Path(__file__).resolve().parents[1]; R = W / 'release_d1'
sha = lambda b: hashlib.sha256(b).hexdigest()
skip = lambda p: '_c02r_original' in p.parts or '__pycache__' in p.parts or p.suffix == '.pyc'
files = {p.relative_to(R).as_posix(): p.read_bytes() for p in sorted(R.rglob('*')) if p.is_file() and not skip(p.relative_to(R)) and p.name != 'D1_RELEASE_MANIFEST.json'}
assert json.loads(files['D1_LOCAL_TESTS.json'])['status'] == 'PASS'
manifest = {'release': 'D1_GATE6_2920_SCHEME_A_BUILD_ONLY', 'files': {k: {'bytes': len(v), 'sha256': sha(v)} for k, v in files.items()},
            'derived_from': {'c02r_c03/code': 'a3c1f5e97e03b99f4fa5fa885f6fe0747768d7d7', 'production_control': 'C09 release (C07 lineage)', 'diffs': 'evidence/DIFF_*.patch'}}
mb = (json.dumps(manifest, indent=1, sort_keys=True) + '\n').encode(); (R / 'D1_RELEASE_MANIFEST.json').write_bytes(mb); files['D1_RELEASE_MANIFEST.json'] = mb
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz', format=tarfile.PAX_FORMAT) as t:
    for k, v in sorted(files.items()):
        ti = tarfile.TarInfo('release/' + k); ti.size = len(v); ti.mtime = 0; ti.mode = 0o644; t.addfile(ti, io.BytesIO(v))
blob = buf.getvalue(); (W / 'D1_RELEASE.tar.gz').write_bytes(blob)
tag = sha(mb)[:8]
d = {'release_manifest_sha256': sha(mb), 'archive_bytes': len(blob), 'archive_sha256': sha(blob), 'payload_files': len(files),
     'remote_control': '/root/autodl-tmp/SGP/incoming/d1_build2920_122_20261013_' + tag,
     'remote_release': '/root/autodl-tmp/SGP/incoming/d1_build2920_122_20261013_' + tag + '/release'}
(W / 'D1_RELEASE_DELIVERY.json').write_text(json.dumps(d, indent=1) + '\n')
print(json.dumps(d, indent=1))
