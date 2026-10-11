from pathlib import Path
import json,hashlib,collections,subprocess
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');D=Path('/mnt/d/ResearchWorkspaces/ASEAN');E=R/'research/05_baseline_evolution/20261011/a06/evidence';B=R/'research/05_baseline_evolution/20261011/a05/evidence'
def read(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def summarize(x):
 if isinstance(x,list):return {'count':len(x),'source_preserved_in_frozen_NetCDF':True}
 if isinstance(x,dict):return {k:summarize(v) for k,v in x.items()}
 return x
for fn in ['A06_COST_OBJECTIVE_EVIDENCE.json','A06_RESOURCE_CARBON_BOUNDARIES.json']:
 p=E/fn;x=read(p)
 if 'frozen_meta' in x:
  for k in ['stock_uncertainty','unresolved_existing_assets_outside_v1']:x['frozen_meta'][k]=summarize(x['frozen_meta'].get(k))
 else:x['frozen2050']['metadata_selected']=summarize(x['frozen2050']['metadata_selected'])
 save(p,x)
net=read(E/'A06_NETWORK_STATIC_READOUT.json')
for x in net['models'].values():
 for k,v in list(x['safe_meta'].items()):
  if isinstance(v,list):x['safe_meta'][k]={'count':len(v),'details':'See frozen source and existing A03 evidence; not recopied'}
save(E/'A06_NETWORK_STATIC_READOUT.json',net)
# Reused metadata and scientific results retain their original qualification.
links=[]
for rel in ['work/gate6_p2_terminal_forensics_20261011/G6_01_TO_G6_04_CLOSEOUT.json','work/gate6_p2_terminal_forensics_20261011/SECOND_RUN_EVIDENCE_VERIFICATION.json']:
 p=D/rel;b=p.read_bytes();j=json.loads(b);links.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'data':j})
src=read(B/'A05_SOURCE_AND_DECISION_EVIDENCE.json')
save(E/'A06_PRIOR_ACCEPTANCE_AND_IDENTITY.json',{'scheme_A_prior_SHA_verified_receipts':src['scheme_a_reused_evidence'],'second_P2_prior_evidence':links,'G6_05_current':'PAUSED_BY_USER; supersedes earlier AWAITING or granted-but-paused diagnostic records','scientific_results':'First OPTIMAL/V4 NOT_ACCEPTED; second INF_OR_UNBD/SolCount0. Source Scheme A not assembled.'})
c=read(E/'A06_COST_OBJECTIVE_EVIDENCE.json');checks=[]
def ck(n,v):assert v,n;checks.append({'check':n,'status':'PASS_VERIFIED'})
ck('Author2025 only lv_limit', [v['id'] for v in net['models']['author2025']['global_constraints']]==['lv_limit'])
gc=net['models']['author2050']['global_constraints'];ck('Author2050 CO2Limit =100Mt and primary_energy',gc[1]['id']=='CO2Limit' and gc[1]['constant']==100000000 and gc[1]['type']=='primary_energy')
ck('Frozen only lv_limit',[v['id'] for v in net['models']['frozen2050']['global_constraints']]==['lv_limit'])
ck('lv_limit identical 353746853.52332264 MWkm',all(m['global_constraints'][0]['constant']==353746853.52332264 for m in net['models'].values()))
ck('All three stored weighting vectors 2920x3=8760',all(len(m['weights'])==3 and all(v=={'count':2920,'sum':8760.,'min':3.,'max':3.} for v in m['weights'].values()) for m in net['models'].values()))
ck('Frozen carbon policy false',c['frozen_meta']['policy_enabled'] is False and c['frozen_meta']['policy_cap_actually_enabled'] is False)
ck('807 prices remain NULL',c['frozen_meta']['fixed_account_count']==807==c['frozen_meta']['fixed_accounts_unknown_price_count'])
ck('Known FOM constant exactly matches both receipts',c['frozen_meta']['existing_annual_fixed_om_eur']==8224491125.573893==c['v3_local_audit']['FOM_coefficient'])
ck('SCOPE_V3 cost and offset identity',c['v3_derivation']['adapted_objective']['sha256']=='6dffbe0e687fdd85f161c132d96ac846266e0a5864c5daacd3772dbeae2486b4' and c['v3_derivation']['adapted_objective']['offset']==-12788967.997821666)
ck('10628915 changed coefficients in retained receipt',c['v3_derivation']['changed_objective_columns']==10628915)
ls={(r['component'],r['field']):r for r in c['effective_ledger_summary']}
ck('917 Link marginal exclusions =12+807+98',ls['Link','marginal_cost']['excluded_v2']==819 and ls['Link','marginal_cost']['excluded_v3']==98 and ls['Link','marginal_cost']['nonzero_effective_increments']==2441)
ck('808 Store marginal exclusions =807+atmosphere',ls['Store','marginal_cost']['excluded_v2']==808 and ls['Store','marginal_cost']['nonzero_effective_increments']==296)
ck('Unknown price imputation absent in final objective',c['v3_derivation']['numeric_noise_on_unknown_fixed_accounts'] is False and c['v3_derivation']['unknown_scientific_prices_unchanged'] is True)
ck('FullSystemCostComplete false',c['frozen_meta']['FullSystemCostComplete'] is False and c['v3_derivation']['FullSystemCostComplete'] is False)
ck('Prior optimal candidate remains scientifically NOT_ACCEPTED',c['first_run_recorded_dual_costs_and_acceptance']['acceptance']['historical_gate6_pass'] is False)
proj=read(E/'A06_AUTHOR2050_PROJECT_CLASSIFICATION.json')['records'];ck('15 selected cross-border additions',len(proj)==15 and sum(v['component']=='lines' for v in proj)==7)
ck('15 historical output and input capacity fields distinct',all(('s_nom_opt' in v and 's_nom' in v) if v['component']=='lines' else ('p_nom_opt' in v and 'p_nom' in v) for v in proj))
for v in proj:
 if v['id']=='250878579-2_0_upgraded':v['classification']='upgrade_mechanism_plus_result; exact 1043MW raw-to-491.4MW processed reconciliation UNKNOWN'
 elif v['component']=='links':v['classification']='raw AIMS new-link project (planning/consideration), active input and historical optimized output'
 else:v['classification']='active planned-year AC input and historical optimized output; raw project-row join UNKNOWN'
save(E/'A06_AUTHOR2050_PROJECT_CLASSIFICATION.json',{**read(E/'A06_AUTHOR2050_PROJECT_CLASSIFICATION.json'),'records':proj})
save(E/'A06_VALIDATION_RECEIPT.json',{'status':'A06_COMPLETE_WITH_EXPLICIT_UNKNOWNS','checks':checks,'checks_passed':len(checks),'scope':'New static evidence checks only; old tests and full matrix scans not rerun','optimizer_calls':0,'model_builds':0,'AutoDL_operations':0,'G6_05':'PAUSED_BY_USER','not_certified':['full LP feasibility','economic comparability','net-zero','all author runtime hook constraints serialized']})
for label in ['author2025','author2050','frozen2050']:
 x=net['models'][label];print(label,'selected cost', {k:v for k,v in x['cost_summary_stored_fields_only']['links'].items() if k in ['SMR CC','Fischer-Tropsch','DC','CCGT']})
