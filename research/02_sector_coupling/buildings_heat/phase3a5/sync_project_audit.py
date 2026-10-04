"""One-time exact Git-blob copy into research_audit, invoked in WSL after root commit."""
from pathlib import Path
import subprocess,json,sys
ROOT=Path('/mnt/c/Users/20122/Documents/ChatGPT/ASEAN')
DEST=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit')
scope='research/02_sector_coupling/buildings_heat/phase3a5'
def git(repo,*args,raw=False):
    b=subprocess.check_output(['git','-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','-C',str(repo),*args])
    return b if raw else b.decode().strip()
assert git(ROOT,'rev-parse','HEAD')==sys.argv[1]
refresh='--refresh-exact-evidence-bytes' in sys.argv
assert git(DEST,'rev-parse','HEAD')==('fd2d7700ebf787e99061b273962438ea04f86afd' if refresh else 'b03b2218866f259e1e6223e5a07738e33fe44e4b')
assert not git(DEST,'status','--porcelain')
files=git(ROOT,'ls-files','--',scope).splitlines();assert files
assert all(n.startswith(scope+'/') for n in files)
if not refresh:git(DEST,'switch','-c','codex/buildings-phase3a5')
else:assert git(DEST,'branch','--show-current')=='codex/buildings-phase3a5'
for name in files:
    p=DEST/name;assert refresh or not p.exists(),name
    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(git(ROOT,'show','HEAD:'+name,raw=True))
git(DEST,'add','-f','--',*files)
git(DEST,'diff','--cached','--check')
git(DEST,'commit','-m','audit: preserve exact bytes for evidence text artifacts' if refresh else 'audit: trace buildings electricity boundary and E3 source evidence')
assert not git(DEST,'status','--porcelain')
for name in files:assert git(ROOT,'show','HEAD:'+name,raw=True)==git(DEST,'show','HEAD:'+name,raw=True)
record=dict(root_audit_commit=sys.argv[1],project_audit_commit=git(DEST,'rev-parse','HEAD'),project_audit_branch=git(DEST,'branch','--show-current'),
    project_audit_clean=True,audit_blob_matches=len(files),scope=scope)
(ROOT/'outputs/phase3a5_project_sync_receipt.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
