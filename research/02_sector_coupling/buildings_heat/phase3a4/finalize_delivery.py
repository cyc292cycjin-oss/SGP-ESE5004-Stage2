"""Sync exact audit blobs, commit research layer, package and hash-check handoff.

One-time local delivery operation, to run in WSL after root audit is committed.
No model modification, solver invocation, history rewrite or remote push.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,zipfile
R=Path(__file__).resolve().parent;ROOT=R.parents[3]
AUDIT=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit')
paths=['research/02_sector_coupling/buildings_heat/phase3a4','data_registry/buildings_phase3a4']
def git(repo,*args,raw=False):
    data=subprocess.check_output(['git','-c','user.name=cyc292cycjin-oss','-c',
      'user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','-C',str(repo),*args])
    return data if raw else data.decode().strip()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert not git(ROOT,'status','--porcelain','--',*paths)
assert not git(AUDIT,'status','--porcelain')
resume='--resume-review-csv-tracking' in sys.argv
if resume:
    assert git(AUDIT,'rev-parse','HEAD')=='a672073eb7651b51d2ea1ad2ca65b34fae7246a8'
    assert git(AUDIT,'branch','--show-current')=='codex/buildings-phase3a4'
else:
    assert git(AUDIT,'rev-parse','HEAD')=='32df5c63c87e25f2ddbb2c04019d8be3ede726f9'
    git(AUDIT,'switch','-c','codex/buildings-phase3a4')
files=git(ROOT,'ls-files','--',*paths).splitlines()
for name in files:
    data=git(ROOT,'show','HEAD:'+name,raw=True)
    dest=AUDIT/name
    if dest.exists():
        assert resume and (dest.read_bytes()==data or name.endswith('/phase3a4/.gitignore') or name.endswith('/phase3a4/finalize_delivery.py')),name
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
git(AUDIT,'add','-f','--',*files);git(AUDIT,'diff','--cached','--check')
git(AUDIT,'commit','-m','audit: retain review CSVs under upstream ignore rules' if resume else 'audit: integrate approved buildings fixes and specify demand accounting closure')
assert not git(AUDIT,'status','--porcelain')
for name in files:assert git(ROOT,'show','HEAD:'+name,raw=True)==git(AUDIT,'show','HEAD:'+name,raw=True)
git(ROOT,'diff','--check','06e93c92c8412ec42b2eff1b66bedfeebdaf9010','HEAD','--',*paths)

old=ROOT/'outputs/phase3a3_buildings_heat_fixes_data_recovery_20261001.zip'
assert sha(old.read_bytes())=='7f638b804787cce017d84d932d050c18608cdeae9d083fc97c9e8bf46ab5dc6a'
out=ROOT/'outputs/phase3a4_buildings_accounting_closure_20261001.zip'
assert not out.exists(),'Do not overwrite an existing delivery'
payload={}
with zipfile.ZipFile(old) as z:
    for name in z.namelist():
        if name.endswith('/') or name.upper().endswith('PACKAGE_MANIFEST.JSON'):continue
        payload[name]=z.read(name)
inherited=len(payload)
for name in files:
    assert name not in payload,name
    payload[name]=git(ROOT,'show','HEAD:'+name,raw=True)
bundle=ROOT/'outputs/phase3a4_buildings_validation.bundle'
bundle_rec=json.loads((R/'evidence/INTEGRATION_BUNDLE.json').read_text())
assert sha(bundle.read_bytes())==bundle_rec['sha256']
payload['provenance/'+bundle.name]=bundle.read_bytes()
identity=json.loads((R/'evidence/FINAL_INTEGRATION_IDENTITY.json').read_text())
receipt=dict(root_audit_commit=git(ROOT,'rev-parse','HEAD'),project_audit_commit=git(AUDIT,'rev-parse','HEAD'),
  project_audit_branch=git(AUDIT,'branch','--show-current'),project_audit_clean=True,
  audit_blob_matches=len(files),integration=identity,prior_package_sha256=sha(old.read_bytes()),
  inherited_payload_files=inherited,solver_runs=0,new_scientific_inputs=0)
payload['provenance/PHASE3A4_DELIVERY_RECEIPT.json']=json.dumps(receipt,indent=2).encode()
manifest=dict(phase='3A-4',files=[dict(path=n,bytes=len(b),sha256=sha(b)) for n,b in sorted(payload.items())])
with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name,data in sorted(payload.items()):z.writestr(name,data)
    z.writestr('PHASE3A4_PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(payload)+1
    assert len(z.namelist())==len(set(z.namelist()))
    for row in manifest['files']:
        assert sha(z.read(row['path']))==row['sha256'],row['path']
        assert not row['path'].startswith('/') and '..' not in Path(row['path']).parts
receipt.update(package=str(out),package_sha256=sha(out.read_bytes()),package_bytes=out.stat().st_size,
               payload_files=len(payload),all_payload_hashes_verified=True,
               root_status=git(ROOT,'status','--porcelain'))
(ROOT/'outputs/phase3a4_delivery_receipt.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt,indent=2))
