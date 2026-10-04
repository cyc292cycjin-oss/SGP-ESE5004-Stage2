"""Read-only final Git identity check; no workflow, model assembly or solver."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess
R=Path(__file__).resolve().parent
before=json.loads((R/'evidence/MODEL_IDENTITY_BEFORE.json').read_text())
rows=[]
for row in before['models']:
    def git(*a):return subprocess.check_output(['git','-C',row['path'],*a]).decode().strip()
    assert git('rev-parse','HEAD')==row['commit']
    assert not git('status','--porcelain')
    rows.append({**row,'unchanged':True})
shipping=json.loads((R.parent/'transport/phase3b2/evidence/SHIPPING_CANDIDATE_IDENTITY.json').read_text())
assert subprocess.check_output(['git','-C',shipping['path'],'rev-parse','HEAD']).decode().strip()==shipping['commit']
assert not subprocess.check_output(['git','-C',shipping['path'],'status','--porcelain']).strip()
record=dict(checked_utc=datetime.now(timezone.utc).isoformat(),models=rows,all_unchanged=True,shipping_candidate_commit=shipping['commit'],shipping_candidate_clean=True,method='Read-only Git HEAD/status, no workflow or solver')
(R/'evidence/MODEL_IDENTITY_AFTER.json').write_text(json.dumps(record,indent=2))
print(json.dumps(dict(protected_layers=len(rows),all_unchanged=True,shipping_candidate_clean=True)))
