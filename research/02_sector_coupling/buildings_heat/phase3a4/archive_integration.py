"""Create a reviewable Git bundle of the integration delta; no push or reset."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parent
ROOT=R.parents[3]
rec=json.loads((R/'evidence/INTEGRATION_RECEIPT.json').read_text())
identity=json.loads((R/'evidence/FINAL_INTEGRATION_IDENTITY.json').read_text())
bundle=ROOT/'outputs/phase3a4_buildings_validation.bundle'
assert not bundle.exists(),'Do not overwrite an existing history artifact'
args=['git','-C',rec['worktree'],'bundle','create',str(bundle),rec['base']+'..'+identity['branch']]
subprocess.run(args,check=True,capture_output=True)
v=subprocess.run(['git','-C',rec['worktree'],'bundle','verify',str(bundle)],check=True,capture_output=True,text=True)
out=dict(file='outputs/'+bundle.name,sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),bytes=bundle.stat().st_size,
         required_base=rec['base'],head=identity['combined_commit'],branch=identity['branch'],verify=v.stdout+v.stderr)
(R/'evidence/INTEGRATION_BUNDLE.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
