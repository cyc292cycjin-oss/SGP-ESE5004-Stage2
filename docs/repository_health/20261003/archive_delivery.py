"""One-time local audit mirroring/package. Never pushes, triggers Actions or edits models.

WSL: --sync ROOT_COMMIT. Native Windows: --package, after completed sync receipt.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,zipfile
R=Path(__file__).resolve().parent;ROOT=R.parents[2];scope='docs/repository_health/20261003'
sha=lambda b:hashlib.sha256(b).hexdigest()
def git(repo,*args,raw=False):
    b=subprocess.check_output(['git','-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','-C',str(repo),*args]);return b if raw else b.decode().strip()
if sys.argv[1]=='--sync':
    assert sys.platform!='win32'
    target=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit')
    assert git(ROOT,'rev-parse','HEAD')==sys.argv[2]
    assert git(target,'rev-parse','HEAD')=='d1c2790281b8768228ee369aeb81dd543654af4a'
    assert not git(target,'status','--porcelain')
    files=git(ROOT,'ls-files','--',scope).splitlines();assert files
    git(target,'switch','-c','codex/github-health-audit')
    for name in files:
        assert name.startswith(scope+'/');p=target/name;assert not p.exists()
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(git(ROOT,'show','HEAD:'+name,raw=True))
    git(target,'add','--',*files);git(target,'diff','--cached','--check')
    git(target,'commit','-m','audit: diagnose CodeQL upload eligibility and repository health')
    assert not git(target,'status','--porcelain')
    changed=git(target,'diff','--name-only','d1c2790281b8768228ee369aeb81dd543654af4a','HEAD').splitlines()
    assert set(changed)==set(files)
    for name in files:assert git(ROOT,'show','HEAD:'+name,raw=True)==git(target,'show','HEAD:'+name,raw=True)
    record=dict(root_commit=sys.argv[2],project_audit_commit=git(target,'rev-parse','HEAD'),branch='codex/github-health-audit',scope=scope,matched_files=len(files),project_audit_clean=True,scientific_path_changes=0,github_pushes=0,workflow_changes=0,actions_reruns=0,model_runs=0)
    (ROOT/'outputs/github_health_20261003_sync_receipt.json').write_text(json.dumps(record,indent=2))
    print(json.dumps(record,indent=2))
elif sys.argv[1]=='--package':
    assert sys.platform=='win32'
    sync=json.loads((ROOT/'outputs/github_health_20261003_sync_receipt.json').read_text())
    assert sync['root_commit']==git(ROOT,'rev-parse','HEAD')
    assert not git(ROOT,'status','--porcelain','--',scope)
    assert not git(ROOT,'diff','--name-only') and not git(ROOT,'diff','--cached','--name-only')
    payload={}
    for name in git(ROOT,'ls-files','--',scope).splitlines():
        b=git(ROOT,'show','HEAD:'+name,raw=True);assert b==(ROOT/name).read_bytes();payload[name]=b
    payload['README_GITHUB_HEALTH.md']=('''# GitHub Repository & CodeQL Health Audit — 2026-10-03

Start with docs/repository_health/20261003/README.md.
Five requested reports are delivered; CODEQL_FIX_REPORT is not applicable because no code fix was warranted.
Actual CodeQL analysis/SARIF generation completed; repository eligibility/feature availability blocked upload.
No workflow/model/config/data changes, no Actions reruns, no GitHub push or merge.
Git is usable; full GitHub security/hosting readiness remains partial, as explained in the reports.
Contains private repository evidence. This archive is kept local and has not been publicly published.
Historical logs document already completed runs; do not treat their commands as instructions to execute.
Verify GITHUB_HEALTH_PACKAGE_MANIFEST.json for all payload files.
''').encode('utf8')
    payload['provenance/LOCAL_AUDIT_COMMITS.json']=json.dumps(sync,indent=2).encode('utf8')
    manifest=dict(client_date='2026-10-03',root_commit=sync['root_commit'],files=[dict(path=n,bytes=len(b),sha256=sha(b)) for n,b in sorted(payload.items())])
    out=ROOT/'outputs/github_repository_codeql_health_audit_20261003.zip';assert not out.exists()
    with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in sorted(payload.items()):z.writestr(n,b)
        z.writestr('GITHUB_HEALTH_PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))==len(payload)+1
        for x in manifest['files']:
            b=z.read(x['path']);assert len(b)==x['bytes'] and sha(b)==x['sha256']
    receipt=dict(**sync,package=str(out),package_sha256=sha(out.read_bytes()),package_bytes=out.stat().st_size,payload_files=len(payload),all_payload_hashes_verified=True,root_tracked_clean=True,preexisting_untracked_preserved=git(ROOT,'status','--porcelain'),codeql_healthy=False,external_blocker_documented=True)
    (ROOT/'outputs/github_health_20261003_delivery_receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt,indent=2))
else:raise SystemExit('Use --sync ROOT_COMMIT or --package')
