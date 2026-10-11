from pathlib import Path
import json,hashlib,subprocess,collections
from netCDF4 import Dataset
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');D=Path('/mnt/d/ResearchWorkspaces/ASEAN');E=R/'research/05_baseline_evolution/20261011/a06/evidence';B=R/'research/05_baseline_evolution/20261011/a05/evidence'
def read(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def norm(x):
 if isinstance(x,float) and (x==float('inf') or x==-float('inf')):return str(x)
 if isinstance(x,dict):return {k:norm(v) for k,v in x.items()}
 if isinstance(x,list):return [norm(v) for v in x]
 return x
net=read(E/'A06_NETWORK_STATIC_READOUT.json');facts={}
for label,m in net['models'].items():
 with Dataset(m['path']) as n:
  meta=json.loads(n.meta);selected={}
  for comp in ['stores','links','generators']:
   ids=n[comp+'_i'][:].tolist();car=n[comp+'_carrier'][:].tolist();ii=[i for i,c in enumerate(car) if ('co2' in c.lower() or c in ['SMR CC','Fischer-Tropsch','DAC','biomass','solid biomass','lignite','co2 stored'])]
   fields=['carrier','bus','bus0','bus1','bus2','bus3','e_nom','e_nom_min','e_nom_max','e_initial','e_cyclic','e_min_pu','e_max_pu','capital_cost','marginal_cost','p_nom','p_nom_min','p_nom_max','p_nom_extendable','efficiency','efficiency2','efficiency3','standing_loss']
   arrays={f:n[comp+'_'+f][:].tolist() for f in fields if comp+'_'+f in n.variables}
   selected[comp]=[{**{'id':ids[i]},**{f:v[i] for f,v in arrays.items()}} for i in ii]
  facts[label]={'selected_carbon_and_resource_static_fields':norm(selected),'default_policy':'Missing fields retain PyPSA0.30.3 defaults, recorded in A05 default-file hashes; null masked values are not prices.','snapshot_weight_totals':m['weights']}
  if label=='frozen2050':
   facts[label]['metadata_selected']={k:meta.get(k) for k in ['approved_coupling_paths','existing_stock_boundary','stock_boundary_decision','stock_uncertainty','unresolved_existing_assets_outside_v1','physical_carbon_map']}
   # materialized price qualification statuses only, not all source rows
   pq=meta.get('component_price_qualification',{});facts[label]['qualification_shape']=type(pq).__name__
 inv=read(B/'A05_CROSS_BORDER_ASSET_INVENTORY.json')
facts['a05_models_summary']=[{k:m[k] for k in ['label','source','component_counts','external_or_fuel_generators','resource_stores'] if k in m} for m in inv['models']]
save(E/'A06_RESOURCE_CARBON_BOUNDARIES.json',facts)
capture=read(E/'A06_SOURCE_CODE_AND_SAFE_CONFIG.json')
P='5bacad702ccfed17ad19ab510fa710651e966f2c';F='b9be7d0ab788a4151346c098d2e657c7e94a22da'
for c,p,ranges in [(P,'scripts/prepare_sector_network.py',[(3181,3220)]),(P,'scripts/_helpers.py',[(2540,2590)]),(F,'scripts_project/build_research_network.py',[(65,106)]),(F,'scripts_project/carrier_architecture.py',[(90,125)])]:
 b=subprocess.check_output(['git','-C',str(R),'show',c+':'+p]);ls=b.decode().splitlines();capture['snippets'].append({'commit':c,'path':p,'sha256':hashlib.sha256(b).hexdigest(),'snippets':[{'start':a,'end':min(z,len(ls)),'text':'\n'.join(f'{i+1}: {ls[i]}' for i in range(a-1,min(z,len(ls))))} for a,z in ranges]})
save(E/'A06_SOURCE_CODE_AND_SAFE_CONFIG.json',capture)
for label in facts:
 if label!='a05_models_summary':print(label,[(k,len(v)) for k,v in facts[label]['selected_carbon_and_resource_static_fields'].items()])
