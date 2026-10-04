"""Archive committed closeout and its prior evidence; verify every payload hash."""
from pathlib import Path
import json,hashlib,subprocess,sys,zipfile
R=Path(__file__).resolve().parent;ROOT=R.parents[3];scope=R.relative_to(ROOT).as_posix()
sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*a,raw=False):
 b=subprocess.check_output(['git','-C',str(ROOT),*a]);return b if raw else b.decode().strip()
assert sys.platform=='win32'
assert not git('status','--porcelain','--',scope)
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
sync=json.loads((ROOT/'outputs/phase3b2_project_sync_receipt.json').read_text())
assert sync['root_audit_commit']==git('rev-parse','HEAD')
payload={}
for n in git('ls-files','--',scope,scope.replace('phase3b2','phase3b1')).splitlines():
 b=git('show','HEAD:'+n,raw=True);assert b==(ROOT/n).read_bytes();payload[n]=b
for p in sorted((R/'evidence/previews').glob('*.png')):payload[p.relative_to(ROOT).as_posix()]=p.read_bytes()
receipt=dict(**sync,root_tracked_clean=True,root_status_native_git=git('status','--porcelain'),solver_runs=0,formal_model_changes=0,isolated_functional_fixes=2,isolated_candidate_commits=3,new_numeric_model_inputs=0,human_review_ready=True,transport_research_scope_closed=True,transport_representation_frozen=True,transport_closed_for_fullsc_assembly=False,candidate=json.loads((R/'evidence/SHIPPING_CANDIDATE_IDENTITY.json').read_text()),validation=json.loads((R/'evidence/DELIVERY_VALIDATION.json').read_text(encoding='utf8')))
payload['provenance/PHASE3B2_DELIVERY_RECEIPT.json']=json.dumps(receipt,ensure_ascii=False,indent=2).encode('utf8')
payload['README_PHASE3B2.md']=(
 '# Phase3B-2 Transport Minimum Baseline & Closeout\n\n'
 'Start with `'+scope+'/TRANSPORT_PHASE3_CLOSEOUT.md`.\n\n'
 'All15 requested deliverables are in that directory. Human review ready: YES. Transport representation frozen by user: YES. Numerical implementation/model ready: NO.\n'
 'Two isolated shipping functional fixes plus Git byte-fidelity commit, not merged into the Future Research Model; 17 offline tests passed. No source quantity, policy or formal-model changes; no solve.\n'
 'Prior Phase3B1 artifacts are included as dependency evidence, not newly produced findings or instructions to run old scripts. Do not rerun old one-time scripts.\n'
 'Large original UNSD archives and author/tutorial NetCDF files remain at recorded paths and are not duplicated; extracted rows, source/version hashes and network observations are retained.\n'
 'Country-account source observations remain UNVERIFIED. Empty-subset zeros and actual missing cells are distinguished. Four domestic-navigation diesel rows excluded by by/in labels remain diagnostic, not replacement model values.\n'
 'Verify PHASE3B2_PACKAGE_MANIFEST.json. Original source rights apply; package not publicly published. Stop at Human Scientific Review; no further Transport deep-dive or experiment executed.\n'
).encode('utf8')
manifest=dict(phase='3B2',root_audit_commit=sync['root_audit_commit'],files=[dict(path=n,bytes=len(b),sha256=sha(b)) for n,b in sorted(payload.items())])
out=ROOT/'outputs/phase3b2_transport_minimum_baseline_closeout_20261003.zip';assert not out.exists()
with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,b in sorted(payload.items()):z.writestr(n,b)
 z.writestr('PHASE3B2_PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))==len(payload)+1
 for row in manifest['files']:
  assert '..' not in Path(row['path']).parts and not row['path'].startswith('/')
  b=z.read(row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256']
receipt.update(package=str(out),package_sha256=sha(out.read_bytes()),package_bytes=out.stat().st_size,payload_files=len(payload),all_payload_hashes_verified=True)
(ROOT/'outputs/phase3b2_delivery_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='validation'},indent=2))
