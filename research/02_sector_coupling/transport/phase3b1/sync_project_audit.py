"""One-time exact committed audit copy to the existing WSL research_audit checkout."""
from pathlib import Path
import subprocess,json,sys
ROOT=Path('/mnt/c/Users/20122/Documents/ChatGPT/ASEAN')
DEST=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit')
scope='research/02_sector_coupling/transport/phase3b1'
def git(repo,*args,raw=False):
 b=subprocess.check_output(['git','-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','-C',str(repo),*args]);return b if raw else b.decode().strip()
assert git(ROOT,'rev-parse','HEAD')==sys.argv[1]
assert git(DEST,'rev-parse','HEAD')=='ac98b363c20182b6ae9a354cedaef227fcee196a'
assert not git(DEST,'status','--porcelain')
files=git(ROOT,'ls-files','--',scope).splitlines();assert files
git(DEST,'switch','-c','codex/transport-phase3b1')
for name in files:
 assert name.startswith(scope+'/');p=DEST/name;assert not p.exists()
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(git(ROOT,'show','HEAD:'+name,raw=True))
git(DEST,'add','-f','--',*files);git(DEST,'diff','--cached','--check')
git(DEST,'commit','-m','audit: trace transport boundaries sources and carbon scope')
assert not git(DEST,'status','--porcelain')
for name in files:assert git(ROOT,'show','HEAD:'+name,raw=True)==git(DEST,'show','HEAD:'+name,raw=True)
record=dict(root_audit_commit=sys.argv[1],project_audit_commit=git(DEST,'rev-parse','HEAD'),project_audit_branch=git(DEST,'branch','--show-current'),project_audit_clean=True,audit_blob_matches=len(files),scope=scope)
(ROOT/'outputs/phase3b1_project_sync_receipt.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
