"""Native Windows handoff packaging; no source mutation or model run.

Run after native root commit and WSL research_audit synchronization.
"""
from pathlib import Path
import json,hashlib,subprocess,zipfile,sys
R=Path(__file__).resolve().parent;ROOT=R.parents[3]
scope=R.relative_to(ROOT).as_posix()
sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*args,raw=False):
    b=subprocess.check_output(['git','-C',str(ROOT),*args]);return b if raw else b.decode().strip()
assert sys.platform=='win32','Native Git status is authoritative on this checkout'
assert not git('status','--porcelain','--',scope)
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
sync=json.loads((ROOT/'outputs/phase3a5_project_sync_receipt.json').read_text())
assert sync['root_audit_commit']==git('rev-parse','HEAD')
old=ROOT/'outputs/phase3a4_buildings_accounting_closure_20261001.zip'
assert sha(old.read_bytes())=='6ec8462b5862d1252cfe2679b3b681c0f09194f8b5be2beb4a610c8a4cc6be33'
out=ROOT/'outputs/phase3a5_buildings_e3_evidence_closure_20261002.zip'
assert not out.exists(),'Never overwrite a completed handoff'
payload={}
with zipfile.ZipFile(old) as z:
    for name in z.namelist():
        if name.endswith('/') or name.upper().endswith('PACKAGE_MANIFEST.JSON'):continue
        payload[name]=z.read(name)
inherited=len(payload)
files=git('ls-files','--',scope).splitlines()
for n in files:
    assert n not in payload,n
    data=git('show','HEAD:'+n,raw=True);assert data==(ROOT/n).read_bytes(),n
    payload[n]=data
reg=json.loads((R/'data/raw/buildings/SOURCE_REGISTRY.json').read_text(encoding='utf8'))
raw_added=0
for source in reg:
    if not source.get('file'):continue
    n=scope+'/'+source['file'];data=(ROOT/n).read_bytes();assert sha(data)==source['sha256']
    if n not in payload:payload[n]=data;raw_added+=1
receipt=dict(**sync,prior_package_sha256=sha(old.read_bytes()),inherited_payload_files=inherited,raw_source_files_added=raw_added,
  root_tracked_clean=True,root_status_native_git=git('status','--porcelain'),solver_runs=0,E3_patch=False,accepted_scientific_inputs=0,
  protected_model_identity=json.loads((R/'evidence/CODE_IDENTITY.json').read_text()),
  validation=json.loads((R/'evidence/DELIVERY_VALIDATION.json').read_text()))
payload['provenance/PHASE3A5_DELIVERY_RECEIPT.json']=json.dumps(receipt,indent=2).encode()
payload['README_PHASE3A5.md']=(
 '# Phase3A5 Buildings E3 Evidence Closure\n\n'
 'Start with `'+scope+'/BUILDINGS_PHASE3A5_READINESS.md`.\n\n'
 '12 requested deliverables are in that folder. Scientific gate: E3 IMPLEMENTATION READY = NO / BLOCKED.\n'
 'No E3 patch or model solves. All140 candidates remain UNVERIFIED / human PENDING.\n'
 'The package retains Phase3A4 dependencies and includes available source originals with SHA256.\n'
 'UNKNOWN is not zero. Parent totals, local samples and end-use children are not additive.\n'
 'Use PHASE3A5_PACKAGE_MANIFEST.json to verify every payload. Source license limits remain in SOURCE_REGISTRY.json.\n'
 'Raw sources are research evidence, never automatic model parameter replacements.\n').encode()
manifest=dict(phase='3A5',root_audit_commit=sync['root_audit_commit'],files=[dict(path=n,bytes=len(b),sha256=sha(b)) for n,b in sorted(payload.items())])
with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for n,b in sorted(payload.items()):z.writestr(n,b)
    z.writestr('PHASE3A5_PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(set(z.namelist()))==len(payload)+1
    for row in manifest['files']:
        assert '..' not in Path(row['path']).parts and not row['path'].startswith('/')
        data=z.read(row['path']);assert sha(data)==row['sha256'] and len(data)==row['bytes']
receipt.update(package=str(out),package_sha256=sha(out.read_bytes()),package_bytes=out.stat().st_size,payload_files=len(payload),all_payload_hashes_verified=True)
(ROOT/'outputs/phase3a5_delivery_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k not in ['protected_model_identity','validation']},indent=2))
