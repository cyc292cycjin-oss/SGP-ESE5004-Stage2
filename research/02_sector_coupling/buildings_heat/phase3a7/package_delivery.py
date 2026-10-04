"""Package committed Phase3A7 reports plus retained dependencies; no model run."""
from pathlib import Path
import json,hashlib,subprocess,zipfile,sys
R=Path(__file__).resolve().parent;ROOT=R.parents[3];scope=R.relative_to(ROOT).as_posix()
sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*a,raw=False):
    b=subprocess.check_output(['git','-C',str(ROOT),*a]);return b if raw else b.decode().strip()
assert sys.platform=='win32'
assert not git('status','--porcelain','--',scope)
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
sync=json.loads((ROOT/'outputs/phase3a7_project_sync_receipt.json').read_text())
assert sync['root_audit_commit']==git('rev-parse','HEAD')
old=ROOT/'outputs/phase3a6_electricity_boundary_malaysia_e3_20261002.zip'
assert sha(old.read_bytes())=='85f6a344e84c12a5cf11dd3665b1849a86151feb2952908ef086364e00233c21'
out=ROOT/'outputs/phase3a7_buildings_boundary_closeout_20261002.zip';assert not out.exists()
payload={}
with zipfile.ZipFile(old) as z:
    assert z.testzip() is None
    for n in z.namelist():
        if not n.endswith('/') and not n.upper().endswith('PACKAGE_MANIFEST.JSON'):payload[n]=z.read(n)
inherited=len(payload)
for n in git('ls-files','--',scope).splitlines():
    b=git('show','HEAD:'+n,raw=True);assert b==(ROOT/n).read_bytes();assert n not in payload;payload[n]=b
# All direct audit dependencies must be present at their resolvable paths.
for dep in json.loads((R/'evidence/INPUT_MANIFEST.json').read_text(encoding='utf8')):
    n=(R/dep['path']).resolve().relative_to(ROOT).as_posix()
    assert n in payload and sha(payload[n])==dep['sha256'],n
for p in sorted((R/'evidence/previews').glob('*.png')):payload[p.relative_to(ROOT).as_posix()]=p.read_bytes()
receipt=dict(**sync,prior_package_sha256=sha(old.read_bytes()),inherited_payload_files=inherited,root_tracked_clean=True,root_status_native_git=git('status','--porcelain'),solver_runs=0,E3_patch=False,new_numeric_model_inputs=0,accepted_scientific_numeric_inputs=0,human_conceptual_boundary_frozen=True,validation=json.loads((R/'evidence/DELIVERY_VALIDATION.json').read_text(encoding='utf8')))
payload['provenance/PHASE3A7_DELIVERY_RECEIPT.json']=json.dumps(receipt,ensure_ascii=False,indent=2).encode('utf8')
payload['README_PHASE3A7.md']=(
    '# Phase3A7 Research electricity boundary and Buildings closeout\n\n'
    'Start with `'+scope+'/BUILDINGS_PHASE3_CLOSEOUT.md`. Six requested deliverables are in this directory.\n\n'
    'Human conceptual boundary frozen: YES. Buildings ready for next-sector scoping: YES.\n'
    'Numerical assembly verified: NO. New accepted numerical inputs: NONE. No Transport start, no E3 patch, no solve.\n'
    '22 country-sector accounts, 44 embedded space/water uses, 15 qualitative materiality entries. Missing is not zero.\n'
    'Prior reports remain historical evidence; Phase3A7 supersedes the requirement to complete universal E3 before further scoping.\n'
    'Shared total-energy, overlap, loss, allocation and comparison gates remain; thermal details are conditional local refinements.\n'
    'This package inherits Phase3A6 sources. Check PHASE3A7_PACKAGE_MANIFEST.json for all payload hashes.\n'
    'Original source rights still apply. Neither this package nor source availability implies numerical scientific acceptance.\n'
).encode('utf8')
manifest=dict(phase='3A7',root_audit_commit=sync['root_audit_commit'],files=[dict(path=n,bytes=len(b),sha256=sha(b)) for n,b in sorted(payload.items())])
with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for n,b in sorted(payload.items()):z.writestr(n,b)
    z.writestr('PHASE3A7_PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))==len(payload)+1
    for row in manifest['files']:
        assert '..' not in Path(row['path']).parts and not row['path'].startswith('/')
        b=z.read(row['path']);assert sha(b)==row['sha256'] and len(b)==row['bytes']
receipt.update(package=str(out),package_sha256=sha(out.read_bytes()),package_bytes=out.stat().st_size,payload_files=len(payload),all_payload_hashes_verified=True)
(ROOT/'outputs/phase3a7_delivery_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='validation'},indent=2))
