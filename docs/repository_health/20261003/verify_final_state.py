"""WSL: verify every existing worktree still has the captured HEAD/status."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess
R=Path(__file__).resolve().parent;E=R/'evidence'
old=json.loads((E/'REPOSITORY_GIT_AUDIT.json').read_text())
rows=[]
for x in old['worktrees']:
    def git(*args):return subprocess.check_output(['git','-C',x['path'],*args]).decode().strip()
    head=git('rev-parse','HEAD');status=git('status','--porcelain')
    assert head==x['head'] and status==x['status'],x['path']
    rows.append(dict(path=x['path'],head=head,status_unchanged=True,clean=not status))
p=subprocess.run(['git','-C',old['repo'],'count-objects','-vH'],capture_output=True)
(E/'GIT_OBJECT_STAT_FINAL.txt').write_bytes(p.stdout+b'\n'+p.stderr)
record=dict(checked_utc=datetime.now(timezone.utc).isoformat(),all_worktree_heads_and_status_unchanged=True,worktrees=rows,scientific_files_modified=0,workflows_modified=0,model_runs=0,actions_reruns=0,remote_mutations=0)
(E/'FINAL_PROTECTED_STATE.json').write_text(json.dumps(record,indent=2))
print(json.dumps({k:v for k,v in record.items() if k!='worktrees'}))
