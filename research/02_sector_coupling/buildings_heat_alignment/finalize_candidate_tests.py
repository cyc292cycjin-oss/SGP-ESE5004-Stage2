"""Finalize local unpushed candidate test files, retaining superseded SHA receipts.
Each patch has a distinct test path to avoid artificial merge conflicts. No main merge.
"""
from pathlib import Path
import json, shutil, subprocess, sys
R=Path(__file__).resolve().parent;records=json.loads((R/'evidence/CANDIDATE_COMMITS.json').read_text())
for record in records:
    repo=Path(record['worktree']);fix=record['fix'];d=repo/'research/02_sector_coupling/buildings_engineering_tests'
    # Delete only the exact harness authored by this audit, after verifying path containment.
    old=d/'check_candidate_fixes.py';assert old.resolve().is_relative_to(repo.resolve())
    target=d/f'check_{fix}.py';shutil.copy2(R/'check_candidate_fixes.py',target)
    if old.exists():old.unlink()
    rd=d/f'{fix}_README.md';generic=d/'README.md'
    rd.write_text(generic.read_text().replace('check_candidate_fixes.py',target.name))
    generic.unlink()
    for stage,src in [('before',repo.parent.parent/'phase2/upstream_sc_baseline'),('after',repo)]:
        output=R/f'evidence/{fix}_{stage}.json'
        done=subprocess.run([sys.executable,str(target),'--repo',str(src),'--fix',fix,'--output',str(output)],capture_output=True,text=True)
        (R/f'evidence/{fix}_{stage}.log').write_text(done.stdout+done.stderr)
        assert done.returncode==(1 if stage=='before' else 0)
        assert json.loads(output.read_text())['all_pass']==(stage=='after')
        shutil.copy2(output,d/output.name)
    def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
    git('add','-A','research/02_sector_coupling/buildings_engineering_tests')
    git('-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','commit','--amend','--no-edit')
    record['superseded_local_candidate_commit']=record['commit'];record['commit']=git('rev-parse','HEAD')
    record['test_file']=str(target.relative_to(repo));record['clean']=not bool(git('status','--porcelain'))
    (R/f'patches/{fix}.patch').write_bytes(subprocess.check_output(['git','-C',str(repo),'format-patch','-1','--stdout']))
(R/'evidence/CANDIDATE_COMMITS.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
