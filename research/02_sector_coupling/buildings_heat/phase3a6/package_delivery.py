"""Create a self-contained, hash-verified handoff; native Windows Git is authoritative."""
from pathlib import Path
import json,hashlib,subprocess,zipfile,sys
R=Path(__file__).resolve().parent;ROOT=R.parents[3];scope=R.relative_to(ROOT).as_posix()
sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*a,raw=False):
 b=subprocess.check_output(['git','-C',str(ROOT),*a]);return b if raw else b.decode().strip()
assert sys.platform=='win32'
assert not git('status','--porcelain','--',scope)
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
sync=json.loads((ROOT/'outputs/phase3a6_project_sync_receipt.json').read_text());assert sync['root_audit_commit']==git('rev-parse','HEAD')
old=ROOT/'outputs/phase3a5_buildings_e3_evidence_closure_20261002.zip'
assert sha(old.read_bytes())=='bd5292a19e4e451edae9a0d8b20e48697203ae710fceb3c825c8ecb93c2b4a37'
out=ROOT/'outputs/phase3a6_electricity_boundary_malaysia_e3_20261002.zip';assert not out.exists()
payload={}
with zipfile.ZipFile(old) as z:
 for n in z.namelist():
  if not n.endswith('/') and not n.upper().endswith('PACKAGE_MANIFEST.JSON'):payload[n]=z.read(n)
inherited=len(payload)
for n in git('ls-files','--',scope).splitlines():
 b=git('show','HEAD:'+n,raw=True);assert b==(ROOT/n).read_bytes();assert n not in payload;payload[n]=b
for source in json.loads((R/'data/SOURCE_REGISTRY.json').read_text()):
 p=(R/source['file']).resolve();n=p.relative_to(ROOT).as_posix();b=p.read_bytes();assert sha(b)==source['sha256']
 if n in payload:assert payload[n]==b
 else:payload[n]=b
# Include reviewed page/table previews as supplementary evidence, not model assets.
for p in sorted((R/'evidence/previews').glob('*.png')):payload[p.relative_to(ROOT).as_posix()]=p.read_bytes()
receipt=dict(**sync,prior_package_sha256=sha(old.read_bytes()),inherited_payload_files=inherited,root_tracked_clean=True,root_status_native_git=git('status','--porcelain'),solver_runs=0,E3_patch=False,accepted_scientific_inputs=0,validation=json.loads((R/'evidence/DELIVERY_VALIDATION.json').read_text()))
payload['provenance/PHASE3A6_DELIVERY_RECEIPT.json']=json.dumps(receipt,indent=2).encode()
payload['README_PHASE3A6.md']=(
 '# Phase3A6 Electricity Boundary Reconciliation + Malaysia E3 Prototype\n\n'
 'Start with `'+scope+'/PHASE3A6_READINESS.md`. All18 requested deliverables are in that directory.\n\n'
 'Boundary review YES; partial Malaysia prototype review YES; E3 production NO. No solves or model-input changes.\n'
 'Annual national E3 BLOCKED; snapshot NOT RUN; numeric useful-heat output unavailable. Unknown is not zero.\n'
 'Source discrepancies and all pending human confirmations are retained. No data choice was silently accepted.\n'
 'This package includes prior dependencies and available original files. Check PHASE3A6_PACKAGE_MANIFEST.json.\n'
 'Publisher source rights still apply; scientific evidence is not an automatic model-data replacement.\n').encode()
manifest=dict(phase='3A6',root_audit_commit=sync['root_audit_commit'],files=[dict(path=n,bytes=len(b),sha256=sha(b)) for n,b in sorted(payload.items())])
with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,b in sorted(payload.items()):z.writestr(n,b)
 z.writestr('PHASE3A6_PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))==len(payload)+1
 for r in manifest['files']:
  assert '..' not in Path(r['path']).parts and not r['path'].startswith('/')
  b=z.read(r['path']);assert sha(b)==r['sha256'] and len(b)==r['bytes']
receipt.update(package=str(out),package_sha256=sha(out.read_bytes()),package_bytes=out.stat().st_size,payload_files=len(payload),all_payload_hashes_verified=True)
(ROOT/'outputs/phase3a6_delivery_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='validation'},indent=2))
