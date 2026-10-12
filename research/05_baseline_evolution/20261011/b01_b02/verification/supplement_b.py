"""Only small static metadata and pinned source excerpts; no model creation."""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter,defaultdict
import hashlib,json,subprocess,ast
import netCDF4,numpy as np,csv,math
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');B=R/'research/05_baseline_evolution/20261011';O=B/'b01_b02/evidence'
P=Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/phase4_gate4_final_closure_20261006/complete_network/research_fullsc_2050_assembly_v1_unsolved.nc')
def clean(x):
 if isinstance(x,np.ndarray):x=None if np.ma.is_masked(x) else x.item() if x.ndim==0 else x.tolist()
 if isinstance(x,np.generic):x=x.item()
 if isinstance(x,float) and not math.isfinite(x):return 'Infinity' if x>0 else '-Infinity' if x<0 else None
 if isinstance(x,F):return {'exact':str(x),'approx':float(x)}
 if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 return x
def save(name,v):(O/name).write_text(json.dumps(clean(v),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(b):return hashlib.sha256(b).hexdigest()
sources={}
for rel,needles in {
 'scripts_project/build_research_assets.py':['def build_fragment','for powertech','elif fuel','fixed resource'],
 'scripts_project/carrier_architecture.py':['def add_external_annual_caps','def add_storage_direction_constraints','ReportingCO2 atmosphere inventory'],
 'scripts_project/integrate_surviving_assets.py':['envelopes[key]','existing_resource_groups','def install_existing_asset_constraints'],
 'scripts_project/assembly_components.py':['def bind_loads','def install_research_constraint_hooks'],
 'scripts_project/build_research_network.py':['if any(n.stores.bus','for name in biomass'],
}.items():
 b=subprocess.check_output(['git','-C',str(R),'show','b9be7d0ab788a4151346c098d2e657c7e94a22da:'+rel]);lines=b.decode().splitlines();selected=[]
 for q in needles:
  hits=[i for i,l in enumerate(lines) if q in l]
  for i in hits:selected.append({'match':q,'line_1_based':i+1,'excerpt':[{'line':j+1,'text':lines[j]} for j in range(max(i-2,0),min(i+18,len(lines)))]})
 sources[rel]={'commit':'b9be7d0ab788a4151346c098d2e657c7e94a22da','sha256':sha(b),'excerpts':selected}
for rel,needles in {'optimization/constraints.py':['def define_storage_unit_constraints','def define_store_constraints','def define_nodal_balance_constraints'],'optimization/variables.py':['def define_spillage_variables']}.items():
 p=Path('/home/jin/miniforge3/envs/pypsa-earth/lib/python3.11/site-packages/pypsa')/rel;b=p.read_bytes();ls=b.decode().splitlines();tree=ast.parse(b);ex=[]
 for node in tree.body:
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and 'def '+node.name in needles:
   ex.append({'function':node.name,'start_line':node.lineno,'end_line':node.end_lineno,'lines':ls[node.lineno-1:node.end_lineno]})
 sources[str(p)]={'version':'0.30.3','sha256':sha(b),'excerpts':ex}
save('B_FROZEN_SOURCE_FORMULAS.json',sources)
with netCDF4.Dataset(P,'r') as n:
 meta=json.loads(n.meta);groups=meta.get('existing_resource_groups',{});gcheck=[]
 for name,g in groups.items():
  lo=F(0);cs=[]
  for c in g['candidates']:
   typ={'Link':'links','Generator':'generators','StorageUnit':'storage_units'}[c['ComponentType']];ids=n[typ+'_i'][:].tolist();i=ids.index(c['Name']);m=float(n[typ+'_p_nom_min'][i]) if typ+'_p_nom_min' in n.variables else 0.;fac=F(c['CapacityToMW']);lo+=F(m)*fac
   cs.append({'component':c['ComponentType'],'name':c['Name'],'capacity_to_MW':c['CapacityToMW'],'minimum':m})
  gcheck.append({'id':name,'meaning':g['meaning'],'source_limit_MW':g['source_limit_mw'],'existing_MW':g['existing_mw'],'new_build_limit_MW':g['new_build_limit_mw'],'sum_minimum_MW_exact':lo,'necessary_minimum_le_shared_limit':lo<=F(g['new_build_limit_mw']),'candidates':cs})
 # Transmission minimum volume is a necessary cap check, not KVL/load-flow proof.
 volume=F(0);rows=[];parent={}
 def find(x):
  parent.setdefault(x,x)
  if parent[x]!=x:parent[x]=find(parent[x])
  return parent[x]
 def join(x,y):parent[find(x)]=find(y)
 for typ,nom in [('lines','s_nom'),('links','p_nom')]:
  ids=n[typ+'_i'][:].tolist();cars=n[typ+'_carrier'][:].tolist();b0=n[typ+'_bus0'][:].tolist();b1=n[typ+'_bus1'][:].tolist()
  for i,key in enumerate(ids):
   if typ=='links' and cars[i] not in ['DC','B2B']:continue
   join(b0[i],b1[i])
   if typ=='links' and cars[i]!='DC':continue
   def val(f,d):return n[typ+'_'+f][i].item() if typ+'_'+f in n.variables and hasattr(n[typ+'_'+f][i],'item') else n[typ+'_'+f][i] if typ+'_'+f in n.variables else d
   ext=bool(val(nom+'_extendable',False));minimum=float(val(nom+'_min',0));length=float(val('length',0));v=F(minimum)*F(length) if ext else F(0);volume+=v
   rows.append({'id':key,'component':typ,'extendable':ext,'minimum':minimum,'length_km':length,'min_volume_MWkm':v})
 cap=json.loads((B/'a06/evidence/BASELINE_CARBON_CONCLUSIONS.json').read_text())['only_global_constraint']['rhs_mw_km']
 bids=n['buses_i'][:].tolist();bc=n['buses_carrier'][:].tolist()
 for b,c in zip(bids,bc):
  if c in ['AC','DC']:find(b)
 comps=defaultdict(list)
 for b in parent:comps[find(b)].append(b)
 su=[]
 for i,k in enumerate(n['storage_units_i'][:]):
  d={'id':str(k)}
  for f,default in [('carrier',''),('p_nom',0),('p_nom_extendable',False),('max_hours',1),('state_of_charge_initial',0),('cyclic_state_of_charge',False),('standing_loss',0),('efficiency_store',1),('efficiency_dispatch',1),('p_min_pu',-1),('p_max_pu',1)]:
   d[f]=n['storage_units_'+f][i] if 'storage_units_'+f in n.variables else default
  d['initial_within_nominal_energy']=0<=d['state_of_charge_initial']<=d['p_nom']*d['max_hours'];su.append(d)
 save('B_SHARED_CAPACITY_AND_STORAGE_NECESSARY_CHECKS.json',{'shared_resource_groups':gcheck,'transmission':{'minimum_volume_MWkm':volume,'cap_MWkm':cap,'headroom_at_minima_MWkm':F(cap)-volume,'minimum_volume_le_cap':volume<=F(cap),'rows':rows,'weak_electric_components':[sorted(v) for v in comps.values()],'warning':'Topology is weak AC/DC/B2B connectivity, not directed transfer capacity or KVL feasibility'},'storage_units':su,'safe_meta_keys':{'external_annual_caps':meta.get('external_annual_caps'),'required_constraint_hooks':meta.get('required_constraint_hooks')}})
 print(json.dumps(clean({'shared_groups':len(gcheck),'shared_minimum_failures':sum(not g['necessary_minimum_le_shared_limit'] for g in gcheck),'lv_min':volume,'lv_cap':cap,'weak_electric_components':len(comps),'storage_units':len(su),'initial_stock_failures':sum(not r['initial_within_nominal_energy'] for r in su)})))
