from pathlib import Path
import subprocess,json,hashlib,ast,sys,inspect
import pandas as pd,numpy as np,pypsa
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
W=Path('/mnt/c/Users/20122/Documents/ChatGPT/ASEAN/work/phase4_gate3');E=W/'evidence';E.mkdir(parents=True,exist_ok=True)
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def clean(x):
    if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,list):return [clean(v) for v in x]
    if isinstance(x,(np.bool_,)):return bool(x)
    if isinstance(x,(float,np.floating)) and not np.isfinite(x):return str(x)
    if isinstance(x,np.integer):return int(x)
    return x
head=git('rev-parse','HEAD');remote=git('ls-remote','origin')
assert git('branch','--show-current')=='research/full-sc-baseline' and not git('status','--porcelain')
assert head+'\trefs/heads/research/full-sc-baseline' in remote
gate2={str(p.relative_to(R)):sha(p) for folder in ['research_inputs/demand','scripts_project'] for p in (R/folder).rglob('*') if p.is_file() and (folder!='scripts_project' or ('demand' in p.name)) and '__pycache__' not in str(p)}
(E/'START.json').write_text(json.dumps({'head':head,'remote_refs':remote,'gate2_hashes':gate2},indent=2))
sys.path.insert(0,str(R/'scripts_project'));from phase4_static import config
cfg=config(R);(E/'EFFECTIVE_CONFIG.json').write_text(json.dumps(clean(cfg),indent=2,default=str))
p=Path('/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/results/baseline-aims-3H-tutorial/prenetworks/elec_s_50_ec_lv2.0__3h_2030_0.071_pre_adjusted.nc')
n=pypsa.Network(p)
tables={name:df.reset_index().rename(columns={df.index.name or 'index':'Name'}).to_dict('records') for name,df in [('Bus',n.buses),('Store',n.stores),('Link',n.links),('Generator',n.generators),('Load',n.loads),('Line',n.lines),('Transformer',n.transformers),('GlobalConstraint',n.global_constraints)]}
(E/'TUTORIAL_COMPONENTS.json').write_text(json.dumps(clean({'source':str(p),'sha256':sha(p),'evidence':'HISTORICAL_TUTORIAL_REFERENCE_NOT_CURRENT_RESEARCH_ASSEMBLY','tables':tables,'snapshot_weight_sums':n.snapshot_weightings.sum().to_dict()}),default=str))
for rel in ['scripts/prepare_sector_network.py','scripts/prepare_network.py','scripts/solve_network.py']:
    src=R/rel;target=E/'source'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(src.read_bytes())
from pypsa.optimization.global_constraints import define_primary_energy_limit
(E/'PYPSA_PRIMARY_ENERGY_FUNCTION.py').write_text(inspect.getsource(define_primary_energy_limit))
print('START',head,'NETWORK',sha(p),'COUNTRIES',n.buses.country.value_counts().to_dict())
for name,df in [('Bus',n.buses),('Store',n.stores),('Link',n.links),('Generator',n.generators),('Load',n.loads)]:print(name,len(df),df.carrier.value_counts().to_dict())
print('CONSTRAINTS',n.global_constraints.to_dict('index'))
print('BUS_SAMPLE',n.buses[['carrier','country','location']].head(8).to_dict('index'))
print('SECTOR_FLAGS',{k:cfg['sector'].get(k) for k in ['hydrogen','gas','oil','coal','lignite','ammonia','co2_network','biomass_transport','solid_biomass_potential','biogas_potential','co2_sequestration_potential','co2_sequestration_cost','dac']})
print('CO2',cfg['co2'])
