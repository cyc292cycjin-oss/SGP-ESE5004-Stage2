"""Package exact committed Phase3C audit plus bounded historical dependencies.

Requires finished sync receipt. Verify every payload byte/hash after ZIP creation.
"""
from pathlib import Path
import json,hashlib,subprocess,sys,zipfile
R=Path(__file__).resolve().parent;ROOT=R.parents[2];scope=R.relative_to(ROOT).as_posix()
sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*a,raw=False):
    b=subprocess.check_output(['git','-C',str(ROOT),*a]);return b if raw else b.decode().strip()
assert sys.platform=='win32'
assert not git('status','--porcelain','--',scope)
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
sync=json.loads((ROOT/'outputs/phase3c_project_sync_receipt.json').read_text())
assert sync['root_audit_commit']==git('rev-parse','HEAD')
names=set(git('ls-files','--',scope).splitlines())
deps=json.loads((R/'evidence/DEPENDENCY_MANIFEST.json').read_text())
names.update(r['path'] for r in deps['dependencies'])
payload={}
for name in sorted(names):
    b=git('show','HEAD:'+name,raw=True);assert b==(ROOT/name).read_bytes();payload[name]=b
for p in sorted((R/'evidence/previews').glob('*.png')):payload[p.relative_to(ROOT).as_posix()]=p.read_bytes()
validation=json.loads((R/'evidence/DELIVERY_VALIDATION.json').read_text(encoding='utf8'))
assert validation['failed']==0 and validation['requested_deliverables']==11
receipt=dict(**sync,root_tracked_clean=True,root_status_native_git=git('status','--porcelain'),solver_runs=0,formal_model_changes=0,new_numeric_model_inputs=0,new_engineering_candidates=0,human_review_ready=True,phase3_research_model_design_closed=True,ready_to_enter_phase4_assembly=True,ready_for_first_fullsc_solve=False,validation=validation)
payload['provenance/PHASE3C_DELIVERY_RECEIPT.json']=json.dumps(receipt,ensure_ascii=False,indent=2).encode('utf8')
payload['README_PHASE3C.md']=(
    '# Phase3C Remaining Sector & Carrier Boundary Freeze\n\n'
    'Start with `'+scope+'/PHASE3_RESEARCH_MODEL_DESIGN_CLOSEOUT.md`.\n\n'
    'All 11 requested deliverables are in that directory: nine reports plus two CSVs.\n'
    'Phase3 design closed: YES. Ready to enter Phase4 assembly work: YES. Ready for first Full-SC solve: NO.\n'
    'No model assembly, solver, new model input acceptance, engineering candidate or policy change in this phase.\n'
    'Prior Buildings/Transport scope is inherited. Industry is a fixed core plus conditional qualified-service interface; no nonempty Mode C block is invented.\n'
    'Only cross-border electricity changes in the core comparison. Disconnected retains the regional Power cap; it is not automatically 11 separable country solves.\n'
    'Historical evidence is included to support review, not as current instructions. Do not rerun old one-time scripts or solves.\n'
    'Raw large archives and author/tutorial NetCDF files remain at recorded paths; bounded extracted evidence and fixed source files are included.\n'
    'Verify PHASE3C_PACKAGE_MANIFEST.json. Source rights remain with original owners. This package is not publicly published.\n'
    'Stop at Human Scientific Review. No Phase3D or Phase4 execution is started.\n'
).encode('utf8')
manifest=dict(phase='3C',root_audit_commit=sync['root_audit_commit'],files=[dict(path=n,bytes=len(b),sha256=sha(b)) for n,b in sorted(payload.items())])
out=ROOT/'outputs/phase3c_remaining_sector_carrier_freeze_20261003.zip';assert not out.exists()
with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name,b in sorted(payload.items()):z.writestr(name,b)
    z.writestr('PHASE3C_PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))==len(payload)+1
    for d in manifest['files']:
        assert '..' not in Path(d['path']).parts and not d['path'].startswith('/')
        b=z.read(d['path']);assert len(b)==d['bytes'] and sha(b)==d['sha256']
receipt.update(package=str(out),package_sha256=sha(out.read_bytes()),package_bytes=out.stat().st_size,payload_files=len(payload),all_payload_hashes_verified=True)
(ROOT/'outputs/phase3c_delivery_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='validation'},indent=2))
