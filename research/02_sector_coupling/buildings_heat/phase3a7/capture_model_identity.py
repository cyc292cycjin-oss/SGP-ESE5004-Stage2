"""Read-only WSL Git identity check; never imports or runs model code."""
from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parent
prior=json.loads((R.parent/'phase3a6/evidence/LOSS_CODE_IDENTITY.json').read_text())
records=[]
for old in prior['protected_models']:
    def git(*args):
        return subprocess.check_output(['git','-C',old['path'],*args]).decode().strip()
    commit=git('rev-parse','HEAD');status=git('status','--porcelain')
    assert commit==old['commit'] and not status, (old['layer'],commit,status)
    records.append(dict(layer=old['layer'],path=old['path'],commit=commit,clean=True))
record=dict(protected_models=records,method='read-only Git HEAD and porcelain status',model_imports=0,solver_runs=0)
(R/'evidence/MODEL_IDENTITY.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
