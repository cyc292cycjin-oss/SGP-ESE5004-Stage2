"""Read only a bounded set of additional frozen-U blobs and model identities."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
R=Path(__file__).resolve().parent
U='/home/jin/research/SGP_ESE5004_Stage2/phase2/upstream_sc_baseline'
SHA='a3616a68ee44592af6527ca9024a90f1956646ae'
files=['scripts/build_industry_demand.py','scripts/build_base_industry_totals.py','scripts/build_industrial_distribution_key.py','scripts/add_export.py','scripts/solve_network.py']
rows=[]
for name in files:
    b=subprocess.check_output(['git','-C',U,'show',SHA+':'+name])
    p=R/'evidence/source/U'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    rows.append(dict(file=name,git_sha=SHA,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),path=p.relative_to(R).as_posix(),source_url='https://github.com/pypsa-meets-earth/pypsa-asean/blob/'+SHA+'/'+name))
(R/'evidence/EXTRA_SOURCE_MANIFEST.json').write_text(json.dumps(rows,indent=2))
prior=R.parent/'transport/phase3b2/evidence/MODEL_IDENTITY_AFTER.json'
models=json.loads(prior.read_text())['models']
for row in models:
    assert subprocess.check_output(['git','-C',row['path'],'rev-parse','HEAD']).decode().strip()==row['commit']
    assert not subprocess.check_output(['git','-C',row['path'],'status','--porcelain']).strip()
(R/'evidence/MODEL_IDENTITY_BEFORE.json').write_text(json.dumps(dict(checked_utc=datetime.now(timezone.utc).isoformat(),models=models,all_unchanged=True),indent=2))
print(json.dumps(dict(extra_frozen_blobs=len(rows),protected_layers_unchanged=len(models))))
