"""Snapshot the authorized resume boundary; read existing evidence, never solve."""
from pathlib import Path
import subprocess as sp, hashlib, json, shutil

R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
W=Path(__file__).resolve().parent
S=W/'stage'; E=W/'evidence'
START='4d944d67809d699e94e50f2b41d16b3679c65a82'
def git(*args):return sp.check_output(['git',*args],cwd=R,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert git('rev-parse','HEAD')==START and not git('status','--porcelain')
assert git('branch','--show-current')=='research/full-sc-baseline'
paths=['research_inputs/assembly_v1','research/04_model_assembly/gate4']
for rel in paths:shutil.copytree(R/rel,S/rel,dirs_exist_ok=True)
for rel in ['scripts_project/check_assembly_inputs.py','tests/research/test_assembly_input_freeze.py','configs/research/baseline.yaml','configs/research/composition.json']:
 p=S/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/rel,p)
hashes={str(p.relative_to(R)):sha(p) for folder in ['research_inputs/demand','scripts_project','configs/research'] for p in (R/folder).glob('*') if p.is_file()}
hashes['scripts/prepare_sector_network.py']=sha(R/'scripts/prepare_sector_network.py')
dump(E/'START.json',dict(head=START,branch=git('branch','--show-current'),remote_refs=git('ls-remote','origin'),preservation_hashes=hashes))
for rel in ['research/02_sector_coupling/transport/phase3b2/ACCOUNT_SOURCE_REVIEW.md','research/02_sector_coupling/transport/phase3b2/evidence/COUNTRY_ACCOUNT_OBSERVATIONS.json','research/02_sector_coupling/buildings_heat/evidence/UNSD_2019_BUILDINGS_ROWS.json','research/02_sector_coupling/buildings_heat_alignment/data/raw/buildings/aeo8.pdf']:
 p=R/rel
 if p.exists():shutil.copyfile(p,E/p.name)
registry=json.loads((R/'research_inputs/assembly_v1/registry.json').read_text())
keys=['InputID','Country','Year','Account','Carrier','Value','RawValue','RawUnit','Source','Locator','Representation','Reason']
examples=[{k:r.get(k) for k in keys} for r in registry['records'] if r['Country'] in ['SG','BN','TL'] and r['Year']==2019 and r['Account'] in ['InternationalShippingBunker','InternationalAviationBunker','DomesticShippingFuel','DomesticAviationFuel','TransportEmbeddedFuelParent']]
dump(E/'ACCOUNT_EXAMPLES.json',examples)
print(json.dumps({'head':START,'copied_evidence':[p.name for p in E.iterdir() if p.is_file()],'bunker_examples':examples},indent=2))
