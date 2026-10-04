"""Read only four protected Git identities and the isolated candidate state."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess
R=Path(__file__).resolve().parent
old=json.loads((R.parent/'phase3b1/evidence/MODEL_IDENTITY_AFTER.json').read_text())['models']
rows=[]
for row in old:
    def git(*a): return subprocess.check_output(['git','-C',row['path'],*a]).decode().strip()
    assert git('rev-parse','HEAD')==row['commit']
    assert not git('status','--porcelain')
    rows.append(dict(**row,unchanged=True))
candidate=json.loads((R/'evidence/SHIPPING_CANDIDATE_IDENTITY.json').read_text())
assert subprocess.check_output(['git','-C',candidate['path'],'rev-parse','HEAD']).decode().strip()==candidate['commit']
assert not subprocess.check_output(['git','-C',candidate['path'],'status','--porcelain']).strip()
record=dict(checked_utc=datetime.now(timezone.utc).isoformat(),models=rows,all_unchanged=True,candidate_clean=True,method='Git HEAD/status only; no workflow or solver')
(R/'evidence/MODEL_IDENTITY_AFTER.json').write_text(json.dumps(record,indent=2))
print(json.dumps(dict(protected_layers=len(rows),all_unchanged=True,candidate_clean=True)))
