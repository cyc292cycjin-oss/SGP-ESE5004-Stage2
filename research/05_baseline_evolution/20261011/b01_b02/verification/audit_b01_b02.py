"""Read-only necessary-condition audit. No PyPSA Network, model or solver import.
Static port interpretation reused from A05. Bounded contiguous time-table read
(Load 40.6 MB) avoids repeated decompression; no CSC or solution vectors. Scheme A
is read from a pinned Git object, not installed into this audit branch.
"""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
import csv,hashlib,json,math,subprocess
import numpy as np
import netCDF4
ROOT=Path('/mnt/d/ResearchWorkspaces/ASEAN')
REPO=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
BASE=Path('research/05_baseline_evolution/20261011')
OUT=REPO/BASE/'b01_b02/evidence';OUT.mkdir(parents=True,exist_ok=True)
SCI='b9be7d0ab788a4151346c098d2e657c7e94a22da'
SCHEME='8883de6fb3e15767c632ac92f535e8a423e90b69'
PREFIX='research_inputs/derived/exact_source_closure_a_max_account_v1_20261011/'
NET=ROOT/'outputs/phase4_gate4_final_closure_20261006/complete_network/research_fullsc_2050_assembly_v1_unsolved.nc'
NETSHA='238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d'
def sha(b):return hashlib.sha256(b).hexdigest()
def clean(v):
 if isinstance(v,np.generic):v=v.item()
 if isinstance(v,float) and not math.isfinite(v):return 'Infinity' if v>0 else '-Infinity' if v<0 else None
 if isinstance(v,F):return {'exact':str(v),'approx':float(v)}
 if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [clean(x) for x in v]
 return v
def save(name,v):(OUT/name).write_text(json.dumps(clean(v),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
bindings={}
def read(rel):
 b=(REPO/BASE/rel).read_bytes();bindings[str(BASE/rel)]={'bytes':len(b),'sha256':sha(b)};return json.loads(b)
def obj(rel):
 b=subprocess.check_output(['git','-C',str(REPO),'show',SCHEME+':'+rel]);bindings[SCHEME+':'+rel]={'bytes':len(b),'sha256':sha(b)};return json.loads(b)
manifest=obj(PREFIX+'EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json')
assert bindings[SCHEME+':'+PREFIX+'EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json']['sha256']=='a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720'
recipe=obj(PREFIX+'carrier_fragment.json');accounts=obj(PREFIX+'external_pending_fixed_accounts.json')
assert bindings[SCHEME+':'+PREFIX+'carrier_fragment.json']['sha256']=='1b0ea897bc17d652a6ac5047935dc6af6c53536a51b197582b3567313d155e8e'
assert bindings[SCHEME+':'+PREFIX+'external_pending_fixed_accounts.json']['sha256']=='20d9d0dc2028f1ca4e07b8e4e02fe51fce3a4a357c0d86366076a528b9a2a8e0'
oldgroups=read('evidence/closure_repair/ALL_385_GROUPS_CLOSURE_LEDGER.json')['groups']
oldaccounts={r['asset']:r for r in read('evidence/A03_ACCOUNT_CROSSWALK.json')}
a03=read('evidence/A03_OBLIGATION_AUDIT_SUMMARY.json')
a05=read('a05/evidence/A05_CROSS_BORDER_ASSET_INVENTORY.json')['models'][0]
carbon=read('a06/evidence/BASELINE_CARBON_CONCLUSIONS.json')
static_receipt=obj(str(BASE/'implementation_a_v1/evidence/STATIC_ACCEPTANCE_RECEIPT.json'))
scheme_groups=[];sync=[];modified=[];acc={a['FixedAccountID']:a for a in accounts}
for g in oldgroups:
 D=F(g['annual_D_mwh']['exact']);Q=sum((F(acc[a['asset']]['QuantityMWh']) for a in g['accounts']),F(0))
 assert Q>=D
 scheme_groups.append({'bus':g['bus'],'load':g['load'],'D_MWh':D,'Q_prime_MWh':Q,'Q_prime_minus_D_MWh':Q-D,'account_ids':[a['asset'] for a in g['accounts']], 'old_D_minus_Q_MWh':g['D_minus_Q_mwh'], 'old_full_LP_certificate':g['complete_LP_certificate_available']})
 for a in g['accounts']:
  key=a['asset'];q=acc[key]['QuantityMWh'];pars=recipe['components']['Store:'+key]['params'];route=recipe['biomass_obligation_routes'][key]
  assert pars['e_nom']==pars['e_initial']==route['annual_cap_mwh']==q
  if F(q)!=F(a['Q_mwh_exact']):modified.append(key)
  sync.append({'asset':key,'resource_bus':acc[key]['ResourceBus'],'final_bus':g['bus'],'meter':acc[key]['Meter'],'Q_prime_MWh':q,'Q_prime_hex':q.hex(),'old_Q_hex':a['Q_mwh_hex'],'four_fields_equal':True,'NULL_price_preserved':acc[key]['UnitPriceEUR2020PerMWh'] is None,'NULL_physical_EF_preserved':acc[key]['PhysicalCO2_tPerMWh'] is None})
assert len(modified)==180 and len(sync)==807 and len(scheme_groups)==385
save('B01_SCHEME_A_SOURCE_BRIDGE.json',{'scope':'Source recipe only, not assembled network or LP','scheme_commit':SCHEME,'version_id':manifest['version_id'],'groups':scheme_groups,'accounts':sync,'modified_accounts':modified,'unchanged_accounts':627,'exact_all_D_le_Q_prime':True,'exact_equal_count':sum(F(g['Q_prime_minus_D_MWh'])==0 for g in scheme_groups),'static_acceptance_reused':static_receipt})
# Reuse A05's component-default convention; do not infer absent prices as zero.
DEFAULTS={};default_ids={}
for typ in ['buses','links','lines','generators','stores','loads','storage_units']:
 p=Path('/home/jin/miniforge3/envs/pypsa-earth/lib/python3.11/site-packages/pypsa/component_attrs')/(typ+'.csv');b=p.read_bytes();default_ids[typ]={'path':str(p),'sha256':sha(b)};DEFAULTS[typ]={}
 for r in csv.DictReader(b.decode().splitlines()):
  v=r['default']
  if v in ['n/a','NaN','nan']:v=None
  elif r['type']=='boolean':v=v.lower()=='true'
  elif r['type'] in ['float','int','static or series']:
   try:v=float(v)
   except ValueError:pass
  DEFAULTS[typ][r['attribute']]=v
def attr(t,r,k):return r.get(k,DEFAULTS[t].get(k))
def table(n,t):
 ids=list(n[t+'_i'][:]);rows={str(i):{'id':str(i)} for i in ids}
 for k in n.variables:
  if k.startswith(t+'_') and k!=t+'_i' and '_t_' not in k and n[k].dimensions==(t+'_i',):
   for i,v in zip(ids,n[k][:].tolist()):rows[str(i)][k[len(t)+1:]]=v
 return rows
series_reads=[]
with netCDF4.Dataset(NET,'r') as n:
 T={t:table(n,t) for t in DEFAULTS};buses=T['buses'];links=T['links'];stores=T['stores'];gens=T['generators'];loads=T['loads']
 weights={k:np.asarray(n['snapshots_'+k][:],dtype=np.float64) for k in ['objective','generators','stores']}
 assert all(len(w)==2920 and np.all(w==3.) for w in weights.values())
 country={b:r['country'] for b,r in buses.items() if r.get('country')}
 for _ in range(len(buses)):
  new={b:country[r['location']] for b,r in buses.items() if b not in country and r.get('location') in country}
  if not new:break
  country.update(new)
 def port(b,c):return {'bus':b,'carrier':buses[b]['carrier'],'country':country.get(b),'coefficient':c,'coefficient_hex':float(c).hex()}
 ports={};incidence=defaultdict(list)
 for key,r in links.items():
  ps=[]
  for j in range(5):
   b=r.get('bus'+str(j),'')
   if not b:continue
   c=-1. if j==0 else attr('links',r,'efficiency' if j==1 else 'efficiency'+str(j))
   if c:ps.append(port(b,c));incidence[b].append({'id':key,'coefficient':c,'carrier':r['carrier']})
  ports[key]=ps
 def bounds(t,r,nom):
  keys=[nom,nom+'_min',nom+'_max',nom+'_extendable']
  keys+=['p_min_pu','p_max_pu'] if t!='lines' and t!='stores' else ['s_max_pu'] if t=='lines' else ['e_initial','e_cyclic','e_min_pu','e_max_pu','standing_loss']
  return {k:attr(t,r,k) for k in keys}
 def effective_max(t,r,nom):return attr(t,r,nom+'_max') if attr(t,r,nom+'_extendable') else attr(t,r,nom)
 external={r['bus']:r for r in gens.values() if r.get('research_role')=='EXTERNAL_SUPPLY'};assert len(external)==400
 def unbounded_link(r):return bool(attr('links',r,'p_nom_extendable')) and math.isinf(attr('links',r,'p_nom_max')) and attr('links',r,'p_max_pu')>0 and attr('links',r,'p_min_pu')==0
 def external_ok(r):return bool(attr('generators',r,'p_nom_extendable')) and math.isinf(attr('generators',r,'p_nom_max')) and attr('generators',r,'p_max_pu')==1 and attr('generators',r,'p_min_pu')==0
 assert all(external_ok(r) for r in external.values())
 biomass={g['load']:g for g in scheme_groups};load_records=[];path_issues=[];resource_topology=[];aggregate=defaultdict(lambda: {'loads':0,'annual_MWh_float':0.,'maximum_individual_peak_MW':0.})
 li={str(k):i for i,k in enumerate(n['loads_t_p_set_i'][:])}
 load_array=np.asarray(n['loads_t_p_set'][:],dtype=np.float64)
 for key,r in loads.items():
  v=load_array[:,li[key]];assert np.all(np.isfinite(v)) and np.all(v>=0)
  car=r['carrier'];b=r['bus'];pmax=float(v.max());annual=float(np.dot(weights['generators'],v));mode=None;path=[]
  if key in biomass:
   g=biomass[key];assert np.all(v==v[0]) and F(float(v[0]))*8760==g['D_MWh']
   for sid in g['account_ids']:
    a=acc[sid];s=stores[sid];m=links[a['Meter']];ps=ports[a['Meter']]
    check=(s['bus']==a['ResourceBus'] and not attr('stores',s,'e_cyclic') and attr('stores',s,'standing_loss')==0 and attr('stores',s,'e_min_pu')==0 and attr('stores',s,'e_max_pu')==1 and attr('stores',s,'e_initial')==attr('stores',s,'e_nom')==oldaccounts[sid]['Q_mwh'] and len(ps)==2 and ps[0]['bus']==a['ResourceBus'] and ps[0]['coefficient']==-1 and ps[1]['bus']==b and ps[1]['coefficient']==1 and unbounded_link(m) and len(incidence[s['bus']])==1)
    assert check
    resource_topology.append({'asset':sid,'resource_bus':s['bus'],'meter':a['Meter'],'final_bus':b,'old_Q_MWh':s['e_nom'],'source_recipe_Q_prime_MWh':a['QuantityMWh'],'old_ports_and_store_structure_pass':check,'meter_bounds':bounds('links',m,'p_nom'),'store_bounds':bounds('stores',s,'e_nom')})
   assert set(x['id'] for x in incidence[b])=={acc[s]['Meter'] for s in g['account_ids']}
   path=g['account_ids'];mode='FINITE_EXCLUSIVE_RESOURCE_SOURCE_RECIPE_CLOSURE'
  elif car in ['oil','gas','coal']:
   incoming=[z for z in incidence[b] if z['coefficient']>0]
   assert len(incoming)==1
   m=links[incoming[0]['id']];src=external.get(m['bus0']);assert src and src['carrier']==car and unbounded_link(m) and m['efficiency']==1
   assert len([p for p in ports[m['id']] if p['coefficient']<0])==1
   path=[src['id'],m['id']];mode='PRICED_UNBOUNDED_LOCAL_EXTERNAL_AND_METER'
  elif car=='electricity':
   candidates=[links[z['id']] for z in incidence[b] if z['coefficient']>0 and z['carrier']=='CCGT']
   valid=[m for m in candidates if m['bus0'] in external and external[m['bus0']]['carrier']=='gas' and unbounded_link(m) and m['efficiency']>0 and len([p for p in ports[m['id']] if p['coefficient']<0])==1]
   assert len(valid)==1
   m=valid[0];path=[external[m['bus0']]['id'],m['id']];mode='LOCAL_GAS_CCGT_INPUT_CAPACITY_UNBOUNDED'
  else:path_issues.append(key)
  aggregate[car]['loads']+=1;aggregate[car]['annual_MWh_float']+=annual;aggregate[car]['maximum_individual_peak_MW']=max(aggregate[car]['maximum_individual_peak_MW'],pmax)
  load_records.append({'load':key,'bus':b,'country':country.get(b),'carrier':car,'annual_MWh_float':annual,'peak_MW':pmax,'minimum_MW':float(v.min()),'profile_sha256_float64_le':sha(v.astype('<f8').tobytes()),'mode':mode,'supply_path':path,'scope':'Path and individual source/rate necessary conditions only; no full LP feasibility claim'})
 del load_array
 series_reads.append({'field':'loads_t_p_set','shape':[2920,1737],'method':'one bounded contiguous 40.6MB input table, per-asset scalar summaries, immediately released','logical_bytes':2920*1737*8})
 assert not path_issues
 # Check finite/unbounded nominal envelopes and input profiles, without solving dispatch.
 bound_errors=[];capacity=[];positive_min=[]
 for typ,nom in [('links','p_nom'),('lines','s_nom'),('generators','p_nom'),('stores','e_nom'),('storage_units','p_nom')]:
  for key,r in T[typ].items():
   z=bounds(typ,r,nom);hi=effective_max(typ,r,nom);lo=z[nom+'_min'] if z[nom+'_extendable'] else z[nom]
   if lo is None or hi is None or lo<0 or hi<lo:bound_errors.append({'component':typ,'id':key,'bounds':z})
   if typ in ['links','generators','storage_units']:
    if z['p_min_pu']>z['p_max_pu']:bound_errors.append({'component':typ,'id':key,'bounds':z})
    if z['p_min_pu']>0:positive_min.append({'component':typ,'id':key,'p_min_pu':z['p_min_pu'],'fixed_nominal':z[nom]})
   capacity.append({'component':typ,'id':key,'carrier':r['carrier'],'bounds':z,'effective_nominal_upper':hi})
 profile=[]
 for field in ['generators_t_p_max_pu','storage_units_t_inflow']:
  ids=n[field+'_i'][:]
  series_array=np.asarray(n[field][:],dtype=np.float64)
  for j,key in enumerate(ids):
   v=series_array[:,j];assert np.isfinite(v).all()
   if (v<0).any():bound_errors.append({'id':str(key),'field':field,'minimum':float(v.min())})
   profile.append({'field':field,'id':str(key),'minimum':float(v.min()),'maximum':float(v.max()),'weighted_sum_3h':float(np.dot(weights['generators'],v)),'sha256_float64_le':sha(v.astype('<f8').tobytes())})
  del series_array
  series_reads.append({'field':field,'shape':list(n[field].shape),'method':'bounded contiguous compressed input read, per-column summaries only','logical_bytes':int(n[field].size*8)})
 # Include coupling metadata with an explicit safe whitelist, never full config.
 meta=json.loads(n.meta)
 selected_meta={k:meta[k] for k in ['store_power_rules','external_annual_caps','biomass_obligation_routes','battery_inverter_pairs','existing_resource_constraints','required_constraint_hooks','approved_global_constraints'] if k in meta}
 assert all(selected_meta['store_power_rules'][sid]=='discharge_only' for sid in acc)
 save('B01_RESOURCE_TOPOLOGY.json',{'accounts':resource_topology,'direction_hook':'all 807 discharge_only in frozen metadata','source_Q_changed_only_in_independent_recipe':True,'full_new_network_not_built':True})
 save('B01_LOAD_SUPPLY_PATHS.json',{'totals':dict(aggregate),'records':load_records,'unresolved_paths':path_issues,'all_paths_local_without_new_cross_border':True,'annual_adequacy_not_global_feasibility':True})
 save('B01_CAPACITY_AND_PROFILE_CHECK.json',{'capacity_records':capacity,'profiles':profile,'bound_conflicts':bound_errors,'positive_dispatch_minima':positive_min,'dynamic_link_bounds_or_efficiency':[k for k in n.variables if k.startswith('links_t_')],'selected_physical_hooks':selected_meta,'external_suppliers':[{'id':r['id'],'bus':r['bus'],'country':country.get(r['bus']),'carrier':r['carrier'],'bounds':bounds('generators',r,'p_nom'),'marginal_cost':r['marginal_cost']} for r in external.values()], 'limitations':['No simultaneous dispatch, ramp, KVL, shared resource envelope or all-row LP feasibility calculation','Finite renewable potential is not treated as an obligation to generate','External unlimited capacity is a model boundary, not a physical import forecast']})
 # Full multiport incident lists for all local captured-CO2/H2/oil buses.
 converted=[]
 for b,br in buses.items():
  if br['carrier'] not in ['co2 captured','H2','oil']:continue
  assets=[]
  for z in incidence[b]:
   r=links[z['id']];assets.append({'id':r['id'],'carrier':r['carrier'],'coefficient_on_this_bus':z['coefficient'],'ports':ports[r['id']],'bounds':bounds('links',r,'p_nom')})
  converted.append({'bus':b,'country':country.get(b),'carrier':br['carrier'],'links':assets,'stores':[{'id':s['id'],'bounds':bounds('stores',s,'e_nom')} for s in stores.values() if s['bus']==b],'generators':[{'id':g['id'],'bounds':bounds('generators',g,'p_nom')} for g in gens.values() if g['bus']==b],'loads':[r['id'] for r in loads.values() if r['bus']==b]})
 captured=[r for r in converted if r['carrier']=='co2 captured'];assert len(captured)==100
 arithmetic=[]
 for r in captured:
  assert not r['stores'] and not r['generators'] and not r['loads'] and len(r['links'])==2
  cc=next(z for z in r['links'] if z['carrier']=='SMR CC');ft=next(z for z in r['links'] if z['carrier']=='Fischer-Tropsch')
  a=F(cc['coefficient_on_this_bus']);b=-F(ft['coefficient_on_this_bus']);ratio=a/b
  h=next(F(p['coefficient']) for p in cc['ports'] if p['carrier']=='H2');ft_e=-next(F(p['coefficient']) for p in ft['ports'] if p['carrier'] in ['AC','DC']);oil=next(F(p['coefficient']) for p in ft['ports'] if p['carrier']=='oil')
  assert a>0 and b>0 and ratio>h
  arithmetic.append({'captured_bus':r['bus'],'SMR_CC':cc['id'],'FT':ft['id'],'capture_t_per_MWh_gas':a,'FT_t_per_MWh_H2':b,'FT_input_per_CC_gas':ratio,'additional_H2_per_CC_gas_if_no_fuelcell':ratio-h,'FT_electricity_per_CC_gas':ratio*ft_e,'FT_oil_per_CC_gas':ratio*oil,'interpretation':'At every snapshot a*s=b*f. h*s alone cannot supply FT H2; electrolysis or non-CC SMR and/or storage discharge are required. Cyclic store cannot supply annual net H2.'})
 atm=[b for b,r in buses.items() if r['carrier'] in ['co2','co2 atmosphere'] and b not in country];assert len(atm)==1
 ar=atm[0];atmo_edges=[{'id':z['id'],'coefficient':z['coefficient'],'p_min_pu':attr('links',links[z['id']],'p_min_pu'),'p_max_pu':attr('links',links[z['id']],'p_max_pu')} for z in incidence[ar]]
 atmo_stores=[{'id':r['id'],'bounds':bounds('stores',r,'e_nom'),'power_rule':selected_meta['store_power_rules'].get(r['id'])} for r in stores.values() if r['bus']==ar]
 save('B02_MULTIPORT_AND_CARBON_BALANCE.json',{'buses':converted,'captured_balance_exact_arithmetic':arithmetic,'atmosphere':{'bus':ar,'all_incident_links':atmo_edges,'stores':atmo_stores,'policy_cap':carbon['effective_carbon_cap_tco2_per_year']},'interpretation':'Positive Link-p only; negative port coefficients are simultaneous inputs, not outputs. No relaxation, new asset or flow assignment created.'})
 summary={'status':'B01_B02_COMPLETE_WITH_EXPLICIT_LIMITS','scheme_source_groups_D_le_Q_prime':385,'scheme_changed_accounts':len(modified),'frozen_loads':len(load_records),'supply_modes':dict(Counter(x['mode'] for x in load_records)),'load_totals':dict(aggregate),'resource_topology':len(resource_topology),'external_sources':len(external),'nominal_or_dispatch_bound_conflicts':len(bound_errors),'positive_minimum_dispatch_assets':positive_min,'captured_buses_without_store_and_only_SMRCC_FT':len(captured),'hydrogen_buses':sum(r['carrier']=='H2' for r in converted),'oil_buses':sum(r['carrier']=='oil' for r in converted),'exact_conversion_example':arithmetic[0],'no_solver_or_model_assembly':True,'full_LP_feasibility':'NOT_PROVEN','new_Scheme_A_network':'NOT_ASSEMBLED','G6_05':'PAUSED_BY_USER'}
 save('B01_B02_STATIC_SUMMARY.json',summary)
save('B01_B02_IDENTITY_AND_READ_SCOPE.json',{'audit_base_commit':'85397fdfd587a4e0cda298139b3c8f43fbbc6d6a','science_code':SCI,'scheme_commit':SCHEME,'scheme_version':manifest['version_id'],'source_bindings':bindings,'component_default_bindings':default_ids,'network':{'path':str(NET),'bytes':NET.stat().st_size,'sha256_reused':NETSHA,'policy':'Reuse existing frozen NetCDF identity and A05/A06 SHA evidence, do not rehash full historical network'},'time_series_reads':series_reads,'full_CSC_reads':0,'raw_solution_reads':0,'AutoDL_operations':0,'solver_calls':0,'new_network_builds':0})
print(json.dumps(clean(summary),ensure_ascii=False,indent=2))
