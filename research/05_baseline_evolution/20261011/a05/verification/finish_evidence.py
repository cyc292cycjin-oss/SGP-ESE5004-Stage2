import json,hashlib,subprocess,math
from pathlib import Path
from collections import Counter,defaultdict
import netCDF4
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');D=Path('/mnt/d/ResearchWorkspaces/ASEAN');W=D/'work/a05_cross_border_audit_20261011'
F='b9be7d0ab788a4151346c098d2e657c7e94a22da';S='8883de6fb3e15767c632ac92f535e8a423e90b69'
def git(*a):return subprocess.check_output(['git','-C',str(R),*a])
def sha(b):return hashlib.sha256(b).hexdigest()
def clean(v):
 if isinstance(v,float) and not math.isfinite(v):return 'Infinity' if v>0 else '-Infinity' if v<0 else None
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [clean(x) for x in v]
 return v
def capture(c,p,ranges=None):
 b=git('show',c+':'+p);lines=b.decode().splitlines()
 return {'commit':c,'path':p,'sha256':sha(b),'blob_sha1':git('rev-parse',c+':'+p).decode().strip(),'snippets':[{'start_line':a,'end_line':min(z,len(lines)),'text':'\n'.join(f'{i+1}: {lines[i]}' for i in range(a-1,min(z,len(lines))))} for a,z in (ranges or [(1,len(lines))])]}
cap=json.loads((W/'CODE_CAPTURE.json').read_text())
extra=[]
for p in ['configs/research/integrated.yaml','configs/research/disconnected.yaml','configs/research/composition.json','scripts_project/check_research_carriers.py','scripts_project/carbon_architecture.py','scripts_project/selected_closure.py']:
 extra.append(capture(F,p))
for c in ['5bacad702ccfed17ad19ab510fa710651e966f2c','a3616a68ee44592af6527ca9024a90f1956646ae']:
 p='scripts/prepare_sector_network.py';t=git('show',c+':'+p).decode().splitlines();ranges=[]
 for i,l in enumerate(t):
  if l.startswith('def ') and any(k in l for k in ['hydrogen','storage_and_grids','co2','biomass','ammonia','shipping']):ranges.append((i+1,min(i+18,len(t))))
 extra.append(capture(c,p,ranges))
 if c.startswith('5bac'):
  extra.append(capture(c,'scripts/final_asean_adjustment.py',[(1,95),(290,350),(368,390)]))
  extra.append(capture(c,p,[(630,750)]))
  extra.append(capture(c,'scripts/add_export.py',[(65,151)]))
cap['supplementary_sources']=extra
decision=D/'research/02_sector_coupling/phase3c/PHASE3_RESEARCH_MODEL_DESIGN_CLOSEOUT.md'
cap['design_decision']={'path':str(decision),'sha256':sha(decision.read_bytes()),'text':decision.read_text()}
scheme_paths=['research_inputs/derived/exact_source_closure_a_max_account_v1_20261011/EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json','research/05_baseline_evolution/20261011/implementation_a_v1/evidence/STATIC_ACCEPTANCE_RECEIPT.json','research/05_baseline_evolution/20261011/implementation_a_v1/evidence/EXACT_SOURCE_CLOSURE_A_WHITELIST_DIFF.json']
cap['scheme_a_reused_evidence']=[]
for p in scheme_paths:
 try:b=git('show',S+':'+p)
 except subprocess.CalledProcessError:continue
 cap['scheme_a_reused_evidence'].append({'commit':S,'path':p,'sha256':sha(b),'receipt':json.loads(b)})
manifest=D/'outputs/phase4_gate4_final_closure_20261006/complete_network/FULLSC_ASSEMBLY_V1_NETWORK_MANIFEST.json'
mf=json.loads(manifest.read_text())
cap['frozen_network_manifest']={'path':str(manifest),'sha256':sha(manifest.read_bytes()),'selected_fields':{k:mf[k] for k in ['network_sha256','code_sha','policy_cap_enabled','actual_network_validation','artifact_role','constraint_hook_state','FullSystemCostComplete','FullSystemEmissionsComplete']}}
cap['frozen_network_manifest']['selected_fields']['actual_network_validation']={k:mf['actual_network_validation'][k] for k in ['checks','interconnect','carbon_events','pending_policy','fixed_accounts']}
cap['version_note']='The assembly manifest predates solver authorization; NOT_RUN there is its historical build status, not current Gate6 status.'
(W/'A05_SOURCE_AND_DECISION_EVIDENCE.json').write_text(json.dumps(clean(cap),ensure_ascii=False,indent=2,allow_nan=False)+'\n')

inv=json.loads((W/'A05_CROSS_BORDER_ASSET_INVENTORY.json').read_text());m=inv['models'][0]; pairs={}
for rec in m['cross_border_assets']:
 key=rec['component']+':'+ '-'.join(rec['countries']);p=rec['parameters'];a=pairs.setdefault(key,{'count':0,'ids':[],'sum_input_nominal_capacity':0.,'units':'MVA for AC Line; MW for DC Link, not a deliverable transfer certificate'})
 a['count']+=1;a['ids'].append(rec['id']);a['sum_input_nominal_capacity']+=p.get('s_nom',p.get('p_nom'))
path=D/'outputs/phase4_gate4_final_closure_20261006/complete_network/research_fullsc_2050_assembly_v1_unsolved.nc'
with netCDF4.Dataset(path) as n:
 def tab(typ):
  ids=n[typ+'_i'][:].tolist();out={i:{} for i in ids}
  for k in n.variables:
   if k.startswith(typ+'_') and '_t_' not in k and k!=typ+'_i' and n[k].dimensions==(typ+'_i',):
    for i,v in zip(ids,n[k][:].tolist()):out[i][k[len(typ)+1:]]=v
  return out
 b,l,loads,s=map(tab,['buses','links','loads','stores']);h2=[x for x in b if b[x]['carrier']=='H2'];coverage=[]
 for h in h2:
  edges=[(i,v) for i,v in l.items() if h in [v.get('bus'+str(j)) for j in range(4)]]
  ft=[(i,v) for i,v in edges if v.get('carrier')=='Fischer-Tropsch'];fc=[(i,v) for i,v in edges if v.get('carrier')=='H2 Fuel Cell']
  oil=ft[0][1]['bus1'] if ft else None
  outlets=[(i,v) for i,v in l.items() if v.get('bus0')==oil and v.get('carrier')=='oil final-energy accounting']
  destinations={v['bus1'] for i,v in outlets}
  demand=[i for i,v in loads.items() if v['bus'] in destinations]
  coverage.append({'h2_bus':h,'country':b[h]['country'],'location':b[h].get('location'),'incident_carriers':dict(Counter(v['carrier'] for i,v in edges)),'fuel_cell_ids':[i for i,v in fc],'FT_ids':[i for i,v in ft],'FT_oil_bus':oil,'oil_final_meter_count':len(outlets),'oil_final_load_count':len(demand),'example_oil_loads':demand[:2]})
 stores={'carrier_counts':dict(Counter(v.get('carrier','') for v in s.values())),'atmosphere':{i:v for i,v in s.items() if v.get('carrier')=='co2 atmosphere'}}
 atmospheric_interfaces=[];negative_or_reversible=[]
 for aid,v in l.items():
  for j in range(4):
   bus=v.get('bus'+str(j))
   if bus and b[bus].get('carrier')=='co2 atmosphere':
    coef=-1 if j==0 else v.get('efficiency' if j==1 else 'efficiency'+str(j),1)
    if coef and coef!=0:
     atmospheric_interfaces.append(aid)
     if coef<0 or v.get('p_min_pu',0)<0:negative_or_reversible.append({'id':aid,'coefficient':coef,'p_min_pu':v.get('p_min_pu',0)})
 result={'cross_border_country_pairs':pairs,'hydrogen_local_end_use_coverage':coverage,'hydrogen_summary':{'buses':len(h2),'with_fuel_cell':sum(bool(v['fuel_cell_ids']) for v in coverage),'with_FT':sum(bool(v['FT_ids']) for v in coverage),'with_FT_to_oil_Load_path':sum(v['oil_final_load_count']>0 for v in coverage),'direct_h2_loads':len(m['direct_h2_nh3_methanol_loads']),'warning':'Port reachability only. FT requires captured CO2 and electricity; no capacity/chronology/optimal-use claim.'},'stores':stores,'fuel_prices':{c:sorted({g['marginal_cost'] for g in m['external_or_fuel_generators'] if g['carrier']==c}) for c in ['coal','gas','lignite','oil']},'non_electric_country_check':m['non_electric_graph'],'no_solver_calls':True}
 result['atmosphere_interface_direction_check']={'nonzero_interfaces':len(atmospheric_interfaces),'negative_or_reversible':negative_or_reversible,'interpretation':'Atmosphere is not a withdrawable input port for any installed Link.'}
 (W/'A05_REACHABILITY_AND_BOUNDARIES.json').write_text(json.dumps(clean(result),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'pairs':pairs,'hydrogen':result['hydrogen_summary'],'stores':stores,'prices':result['fuel_prices'],'scheme_evidence_count':len(cap['scheme_a_reused_evidence']),'extra_sources':[(x['path'],len(x['snippets'])) for x in extra]},ensure_ascii=False,indent=2))
