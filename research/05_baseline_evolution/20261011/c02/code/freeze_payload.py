from pathlib import Path
import json,hashlib,shutil,ast
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c02_daily_build_20261012');P=W/'payload';S=W/'upload_stage'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files={}
for p in sorted(P.rglob('*')):
    if not p.is_file() or '__pycache__' in p.parts or p.name=='PAYLOAD_MANIFEST.json':continue
    assert p.suffix in {'.py','.json','.csv','.md'} and p.stat().st_size<12_000_000
    if p.suffix=='.py':ast.parse(p.read_text())
    files[str(p.relative_to(P))]={'bytes':p.stat().st_size,'sha256':sha(p)}
manifest={'schema':'C02_BUILD_PAYLOAD_V1','build_id':'C02_DAILY_122_20261012_V1','files':files,'solver_authorized':False,'full_build_max':1,'deadline_seconds':1800}
(P/'PAYLOAD_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
S.mkdir(exist_ok=False)
for rel in list(files)+['PAYLOAD_MANIFEST.json']:
    d=S/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/rel,d)
receipt={'files':len(files)+1,'bytes':sum(r['bytes'] for r in files.values()),'manifest_sha256':sha(P/'PAYLOAD_MANIFEST.json'),'build_id':manifest['build_id']}
(W/'PAYLOAD_FREEZE.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
