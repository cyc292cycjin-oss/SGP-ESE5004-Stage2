"""Archive the committed transport audit, including source copies and hashes."""
from pathlib import Path
import json,hashlib,subprocess,sys,zipfile
R=Path(__file__).resolve().parent;ROOT=R.parents[3];scope=R.relative_to(ROOT).as_posix()
sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*a,raw=False):
 b=subprocess.check_output(['git','-C',str(ROOT),*a]);return b if raw else b.decode().strip()
assert sys.platform=='win32'
assert not git('status','--porcelain','--',scope)
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
sync=json.loads((ROOT/'outputs/phase3b1_project_sync_receipt.json').read_text())
assert sync['root_audit_commit']==git('rev-parse','HEAD')
payload={}
for n in git('ls-files','--',scope).splitlines():
 b=git('show','HEAD:'+n,raw=True);assert b==(ROOT/n).read_bytes();payload[n]=b
for p in sorted((R/'evidence/previews').glob('*.png')):payload[p.relative_to(ROOT).as_posix()]=p.read_bytes()
receipt=dict(**sync,root_tracked_clean=True,root_status_native_git=git('status','--porcelain'),solver_runs=0,transport_model_changes=0,new_numeric_model_inputs=0,human_review_ready=True,transport_boundary_frozen=False,validation=json.loads((R/'evidence/DELIVERY_VALIDATION.json').read_text(encoding='utf8')))
payload['provenance/PHASE3B1_DELIVERY_RECEIPT.json']=json.dumps(receipt,ensure_ascii=False,indent=2).encode('utf8')
payload['README_PHASE3B1.md']=(
 '# Phase3B-1 Transport Boundary & Source Audit\n\n'
 'Start with `'+scope+'/PHASE3B1_TRANSPORT_READINESS.md`.\n\n'
 'All15 requested deliverables are in that directory. Human review ready: YES. Transport boundary/parameters accepted: NO.\n'
 'This is a read-only model audit. No transport patch, EV subtraction, carbon-policy change, new H2 network or model solve.\n'
 'The package contains frozen P/U code excerpts, retained small input copies, raw-row extractions, prior context copies and hashed network observations.\n'
 'Large original UNSD archives and author/tutorial NetCDF files remain at recorded paths and are not duplicated here; hashes and author retrieval references are retained.\n'
 '123 keyword-selected raw rows include non-terminal transactions; use documented per-account filters, not the candidate sum.\n'
 'Observed zeros/NaNs remain distinguished from missing data. All numeric model adoption and first-baseline options remain pending human review.\n'
 'Verify PHASE3B1_PACKAGE_MANIFEST.json. Original source rights apply; this archive has not been publicly published.\n'
).encode('utf8')
manifest=dict(phase='3B1',root_audit_commit=sync['root_audit_commit'],files=[dict(path=n,bytes=len(b),sha256=sha(b)) for n,b in sorted(payload.items())])
out=ROOT/'outputs/phase3b1_transport_boundary_source_audit_20261002.zip';assert not out.exists()
with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,b in sorted(payload.items()):z.writestr(n,b)
 z.writestr('PHASE3B1_PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))==len(payload)+1
 for row in manifest['files']:
  assert '..' not in Path(row['path']).parts and not row['path'].startswith('/')
  b=z.read(row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256']
receipt.update(package=str(out),package_sha256=sha(out.read_bytes()),package_bytes=out.stat().st_size,payload_files=len(payload),all_payload_hashes_verified=True)
(ROOT/'outputs/phase3b1_delivery_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='validation'},indent=2))
