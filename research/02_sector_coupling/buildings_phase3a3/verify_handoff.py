"""Read-only verification of the supplied Phase 3A-2 archive. No extraction."""
from pathlib import Path, PurePosixPath
import hashlib, json, zipfile

R = Path(__file__).resolve().parent
ROOT = R.parents[2]
D = Path('C:/Users/20122/Desktop/PyPSA建立')
name = 'phase3a2_buildings_heat_alignment_20261001.zip'
sha = lambda b: hashlib.sha256(b).hexdigest()
receipt = json.loads((ROOT/'outputs/phase3a2_delivery_receipt.json').read_text())
with zipfile.ZipFile(D/name) as z:
    names = z.namelist()
    manifest_name = next(n for n in names if n.endswith('PACKAGE_MANIFEST.json'))
    manifest = json.loads(z.read(manifest_name))
    (R/'evidence').mkdir(parents=True, exist_ok=True)
    # Record structure first; accept no unverified extraction or commands.
    payload = manifest.get('files', manifest.get('entries', []))
    if isinstance(payload, dict): payload = [dict(path=k, **v) for k,v in payload.items()]
    checks=[]
    for f in payload:
        p=f.get('path', f.get('archive_path'))
        content=z.read(p)
        checks.append(dict(path=p, hash_match=sha(content)==f['sha256'], bytes_match=len(content)==f.get('bytes',len(content))))
    readme_name=next(n for n in names if n.endswith('buildings_heat_alignment/README.md'))
    result=dict(archive=str(D/name),bytes=(D/name).stat().st_size,sha256=sha((D/name).read_bytes()),
      receipt_match=sha((D/name).read_bytes())==receipt['archive_sha256'],
      canonical_match=sha((D/name).read_bytes())==sha((ROOT/'outputs'/name).read_bytes()),
      entries=len(names),duplicate_names=len(names)!=len(set(names)),crc_error=z.testzip(),
      unsafe_paths=[n for n in names if PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts or '\\' in n or ':' in n],
      desktop_readme_byte_match=(D/'README.md').read_bytes()==z.read(readme_name),
      desktop_readme_text_match=(D/'README.md').read_text(encoding='utf-8-sig')==z.read(readme_name).decode('utf-8-sig').replace('\r\n','\n'),
      manifest_keys=list(manifest),payload_count=len(checks),payload_checks=checks)
    result['all_payload_hashes_match']=bool(checks) and all(c['hash_match'] and c['bytes_match'] for c in checks)
    (R/'evidence/HANDOFF_VERIFICATION.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='payload_checks'},ensure_ascii=False))
