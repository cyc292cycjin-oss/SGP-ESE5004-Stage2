"""Read pinned model trees and retain bounded evidence; never modify/solve them."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parent
P=Path('/home/jin/research/SGP_ESE5004_Stage2')
trees={'P':(P/'phase2/paper_reference','5bacad702ccfed17ad19ab510fa710651e966f2c'),
 'U':(P/'phase2/upstream_sc_baseline','a3616a68ee44592af6527ca9024a90f1956646ae'),
 'V':(P/'phase3a4/buildings_accounting_validation','50a73d8f531132c5459174a55cac412d5f684462'),
 'R':(P/'phase2/research_model','a3616a68ee44592af6527ca9024a90f1956646ae')}
files=['config.default.yaml','configs/config.asean.yaml','configs/bundle_config.yaml','Snakefile',
 'scripts/build_demand_profiles.py','scripts/add_electricity.py','scripts/final_asean_adjustment.py',
 'scripts/prepare_sector_network.py','scripts/prepare_energy_totals.py','scripts/build_base_energy_totals.py','scripts/prepare_heat_data.py']
def git(p,*a):return subprocess.check_output(['git','-C',str(p),*a])
sha=lambda b:hashlib.sha256(b).hexdigest()
e=R/'evidence';e.mkdir(parents=True,exist_ok=True)
records=[]
for label,(p,expected) in trees.items():
    assert git(p,'rev-parse','HEAD').decode().strip()==expected
    assert not git(p,'status','--porcelain').strip()
    entry=dict(layer=label,path=str(p),commit=expected,clean=True,files=[])
    if label!='R':
        for name in files:
            b=git(p,'show',expected+':'+name)
            dest=e/'source_snapshot'/label/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
            entry['files'].append(dict(path=name,sha256=sha(b),bytes=len(b)))
    records.append(entry)
(e/'CODE_IDENTITY.json').write_text(json.dumps(records,indent=2))
calls=git(trees['U'][0],'grep','-n','-E','transmission_efficiency|electricity distribution grid','--','scripts')
(e/'DISTRIBUTION_CALLSITE_SEARCH.txt').write_bytes(calls)
classified=json.loads((R.parent.parent/'buildings_heat_alignment/data/processed/buildings/UNSD_2019_BUILDINGS_CLASSIFIED.json').read_text())
raw=[]
for name in sorted({r['source_file'] for r in classified}):
    p=P/'pypsa-asean/data/demand/unsd/data'/name
    raw.append(dict(filename=name,path=str(p),bytes=p.stat().st_size,sha256=sha(p.read_bytes())))
(e/'UNSD_RAW_IDENTITIES.json').write_text(json.dumps(raw,indent=2))
print(json.dumps(dict(trees=[{k:v for k,v in x.items() if k!='files'} for x in records],raw_files=raw)))
