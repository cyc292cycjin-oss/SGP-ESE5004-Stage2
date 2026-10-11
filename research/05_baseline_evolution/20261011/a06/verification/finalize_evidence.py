"""A06 deterministic static joins; reads only named sources, no model construction."""
from pathlib import Path
import json,hashlib,csv,io,subprocess,collections,math
from netCDF4 import Dataset
D=Path('/mnt/d/ResearchWorkspaces/ASEAN');R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');W=D/'work/a06_policy_cost_resource_audit_20261012'
A=R/'research/05_baseline_evolution/20261011/a06';E=A/'evidence';E.mkdir(parents=True,exist_ok=True)
B=R/'research/05_baseline_evolution/20261011/a05/evidence'
P='5bacad702ccfed17ad19ab510fa710651e966f2c';U='a3616a68ee44592af6527ca9024a90f1956646ae';F='b9be7d0ab788a4151346c098d2e657c7e94a22da'
def g(*a):return subprocess.check_output(['git','-C',str(R),*a])
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
sources={}
def ref(p):
 b=p.read_bytes();sources[str(p)]={'bytes':len(b),'sha256':sha(b)};return b
out=read(W/'NETWORK_STATIC_READOUT.json');cap=read(W/'SOURCE_CAPTURE.json')
# Only retain compact accounting summary; original source remains immutable.
for v in cap['safe_network_config'].values():
 if 'accounting_report' in v:
  x=v['accounting_report'];v['accounting_report']={k:y for k,y in x.items() if not isinstance(y,list)}
  for k,y in x.items():
   if isinstance(y,list):v['accounting_report'][k+'_count']=len(y)
spec=[(P,'scripts/_helpers.py',[(951,975),(1135,1220)]),(P,'scripts/add_transmission_projects.py',[(18,60)]),(P,'scripts/build_transmission_projects.py',[(270,365),(690,803)]),(P,'scripts/add_brownfield.py',[(230,277)]),(U,'scripts/prepare_sector_network.py',[(1408,1500),(3601,3662)]),(F,'scripts_project/price_basis.py',[(1,150)]),(F,'scripts_project/fixed_accounts.py',[(1,112)]),(F,'scripts_project/selected_closure.py',[(1,110)]),(F,'scripts_project/integrate_surviving_assets.py',[(165,185)])]
for c,p,ranges in spec:
 b=g('show',c+':'+p);ls=b.decode().splitlines();cap['snippets'].append({'commit':c,'path':p,'blob_sha1':g('rev-parse',c+':'+p).decode().strip(),'sha256':sha(b),'snippets':[{'start':a,'end':min(z,len(ls)),'text':'\n'.join(f'{i+1}: {ls[i]}' for i in range(a-1,min(z,len(ls))))} for a,z in ranges]})
projects=[]
for p in g('ls-tree','-r','--name-only',P,'data/transmission_projects').decode().splitlines():
 if '/AIMS/' not in p:continue
 b=g('show',P+':'+p);projects.append({'commit':P,'path':p,'sha256':sha(b),'rows':list(csv.DictReader(io.StringIO(b.decode('utf-8-sig'))))})
inventory=read(B/'A05_CROSS_BORDER_ASSET_INVENTORY.json')
e05=read(B/'A05_SOURCE_AND_DECISION_EVIDENCE.json')
extras=out['models']['author2050']['author2050_additional_electric_assets'];ids=['0','29','42','65','67','7','89','250878579-2_0_upgraded','Plentong - Woodlands','Khlong Ngae – Gurun 2','Telok Gong – Perawang','Kudat – Palawan','Peranap – Singapore','Singapore – Vietnam','Singapore – Cambodia']
selected=[x for x in extras if x['id'] in ids];assert len(selected)==15
for x in selected:
 x['classification']='input_project_with_historical_optimized_capacity';x['source_matches']=[]
 for p in projects:
  for row in p['rows']:
   if str(row.get('',row.get('name','')))==x['id'] or (x.get('tags') and row.get('tags')==x['tags']):x['source_matches'].append({'file':p['path'],'row':row})
save(E/'A06_AUTHOR2050_PROJECT_CLASSIFICATION.json',{'cross_border_selection_basis':'Reuse A05 exact Bus.country/location/port classification (7 AC + 8 DC); do not classify by names. Seven additional domestic DC records are excluded.','records':selected,'raw_project_sources':projects,'limitations':'Output p_nom_opt/s_nom_opt are read solely to distinguish result versus input. No dispatch imported, and no exact original preprocessing provenance claim for unmatched rows.'})
v3base=D/'work/final_local_closeout_20261010/AUTHOR_METHOD_ADAPTED_SCOPE_V3'
v3=json.loads(ref(v3base/'OBJECTIVE_DERIVATION.json'));ledgerbytes=ref(v3base/'EFFECTIVE_PERTURBATION_LEDGER.csv');assert sha(ledgerbytes)==v3['effective_ledger_sha256']
ledger=list(csv.DictReader(io.StringIO(ledgerbytes.decode())));summ={}
for row in ledger:summ.setdefault((row['component'],row['field']),[]).append(row)
summary=[{'component':c,'field':f,'records':len(rs),'nonzero_effective_increments':sum(float(x['effective_float64_increment'])!=0 for x in rs),'excluded_v2':sum(x['scope_v2_excluded']=='True' for x in rs),'excluded_v3':sum(x['scope_v3_excluded']=='True' for x in rs),'min':min(float(x['effective_float64_increment']) for x in rs),'max':max(float(x['effective_float64_increment']) for x in rs),'seed_values':sorted({x['seed'] for x in rs})} for (c,f),rs in summ.items()]
frozen=out['models']['frozen2050']
with Dataset(frozen['path'],'r') as n:
 meta=json.loads(n.meta)
 fields=['model_price_year','price_layer_sha256','price_method','selected_cost_decision','existing_cost_boundary','existing_stock_boundary','stock_boundary_decision','stock_uncertainty','unresolved_existing_assets_outside_v1','existing_annual_fixed_om_eur','external_fixed_account_method','FullSystemCostComplete','FullSystemEmissionsComplete','policy_enabled','policy_cap_actually_enabled','no_cap_assembly_v1','atmosphere_role']
 facts={k:meta.get(k) for k in fields};accounts=meta['external_pending_fixed_accounts'];facts['fixed_account_count']=len(accounts)
 facts['fixed_accounts_unknown_price_count']=sum(x['UnitPriceEUR2020PerMWh'] is None for x in accounts)
 facts['price_qualification_records']=meta.get('component_price_qualification')
 facts['price_qualification_type']=type(facts['price_qualification_records']).__name__
 if isinstance(facts['price_qualification_records'],list):facts['price_qualification_records']={'count':len(facts['price_qualification_records']),'status_counts':dict(collections.Counter(str(x.get('Status')) for x in facts['price_qualification_records']))}
save(E/'A06_COST_OBJECTIVE_EVIDENCE.json',{'v3_derivation':{k:v for k,v in v3.items() if k not in ['component_summary','exceptions','math_arrays_reused_by_reference','blocks']},'effective_ledger_verified_sha':sha(ledgerbytes),'effective_ledger_summary':summary,'frozen_meta':facts,'legacy_component_summary_warning':'V3 component_summary is inherited V2; use SHA-matched final effective ledger above. effective_ledger_path string is historical V2; resolve final file by effective_ledger_sha256.','prior_offset_and_FOM_audit':json.loads(ref(D/'work/author_method_preflight_20261010/SCIENTIFIC_BOUNDARY_AND_OBJECTIVE_AUDIT.json'))['objective'],'v3_local_audit':json.loads(ref(v3base/'SCOPE_V3_LOCAL_AUDIT.json')),'first_run_recorded_dual_costs_and_acceptance':json.loads(ref(D/'outputs/cloud_gate6/gate6_gurobi379_scope_v3_20261009T230330Z_0c53736d/V4_RECORDED_RESULT_SUMMARY.json'))})
for rel in ['work/final_scientific_approval_20261010/BASELINE_CARBON_CONCLUSIONS.json','work/final_scientific_approval_20261010/BASELINE_CARBON_MATRIX_AUDIT.json','work/final_scientific_approval_20261010/BASELINE_CARBON_CAPACITY_SUPPLEMENT.json']:
 p=D/rel;ref(p)
 # Matrix audit may be large; reuse bounded conclusions and explicit row identity, no rescan.
 if p.stat().st_size<100000:save(E/p.name,json.loads(p.read_text()))
for rel in ['research/04_model_assembly/gate4/MODEL_FACING_COST_YEAR_CHECK.md','research/04_model_assembly/gate4/CONFIG_MARGINAL_COST_SEMANTICS.md','research/04_model_assembly/gate3/evidence/phase3_design/CARBON_SCOPE_FREEZE.md','research_inputs/asset_survival/selected_closure_decisions.json']:
 b=g('show',F+':'+rel);cap.setdefault('historical_decision_documents',[]).append({'commit':F,'path':rel,'sha256':sha(b),'text':b.decode()})
for p in B.glob('*.json'):sources[str(p)]={'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'reuse':'A05 static audit, not rerun'}
save(E/'A06_NETWORK_STATIC_READOUT.json',out);save(E/'A06_SOURCE_CODE_AND_SAFE_CONFIG.json',cap);save(E/'A06_EXTERNAL_EVIDENCE_INDEX.json',{'files':sources,'frozen_scientific_commit':F,'branch_base':'4e00897199d28c72b35f6cff550b30ba94337e06','scheme_A_reference_commit':'8883de6fb3e15767c632ac92f535e8a423e90b69','big_array_policy':'All full NetCDF/CSC/X/Pi/RC identity hashes reused from prior verified indices; no new full matrix or vector scan.'})
