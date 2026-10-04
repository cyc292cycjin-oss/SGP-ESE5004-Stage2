"""Finish with read-only Git identity checks for the four protected layers."""
from pathlib import Path
import json,subprocess
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
before=json.loads((R/'evidence/MODEL_IDENTITY.json').read_text())
after=[]
for row in before:
 def git(*a):return subprocess.check_output(['git','-C',row['path'],*a]).decode().strip()
 assert git('rev-parse','HEAD')==row['commit']
 assert not git('status','--porcelain')
 after.append(row)
record=dict(checked_utc=datetime.now(timezone.utc).isoformat(),models=after,all_unchanged=True,method='Git HEAD and status only; no model import or solver')
(R/'evidence/MODEL_IDENTITY_AFTER.json').write_text(json.dumps(record,indent=2))
print(json.dumps(dict(protected_layers=len(after),all_unchanged=True)))
