"""Correct a README environment label; preserve the earlier validation commits."""
from pathlib import Path
import json,subprocess
R=Path(__file__).resolve().parent;P=R/'evidence/FIX_COMMITS.json'
records=json.loads(P.read_text())
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
for rec in records:
    repo=Path(rec['worktree']);fix=rec['fix']
    assert git(repo,'rev-parse','HEAD')==rec['validation_commit'] and not git(repo,'status','--porcelain')
    p=repo/f'research/02_sector_coupling/buildings_engineering_tests/phase3a3_{fix}/README.md'
    version=json.loads((R/f'evidence/{fix}_after.json').read_text())['pypsa']
    s=p.read_text();assert s.count('PyPSA 0.35')==1
    p.write_text(s.replace('PyPSA 0.35',f'PyPSA {version}'))
    git(repo,'add',str(p.relative_to(repo)))
    git(repo,'-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com',
      'commit','-m','docs: record measured PyPSA version for buildings tests')
    rec.update(branch_head=git(repo,'rev-parse','HEAD'),environment=version,
      documentation_correction='README previously labelled0.35; actual test receipts record0.30.3. No source/test/result change.')
    (R/f'patches/{fix}_validation.patch').write_bytes(subprocess.check_output(['git','-C',str(repo),'format-patch',rec['source_commit']+'..HEAD','--stdout']))
P.write_text(json.dumps(records,indent=2));print(json.dumps([{k:r[k] for k in ['fix','branch_head','environment']} for r in records]))
