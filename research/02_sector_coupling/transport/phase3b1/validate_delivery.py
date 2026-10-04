"""Validate new documentary deliverables, not a transport model or experiment."""
from pathlib import Path
import json,csv,hashlib,ast
R=Path(__file__).resolve().parent;ROOT=R.parents[3]
sha=lambda b:hashlib.sha256(b).hexdigest()
checks=[]
def check(label,value):
 assert value,label
 checks.append(label)
reports=['TRANSPORT_ARCHITECTURE_MAP','TRANSPORT_DEMAND_SOURCE_TRACE','TRANSPORT_ELECTRICITY_DOUBLE_COUNT_AUDIT','ROAD_TRANSPORT_AUDIT','RAIL_TRANSPORT_AUDIT','SHIPPING_AVIATION_AUDIT','TRANSPORT_H2_FUEL_INTERACTION','TRANSPORT_TEMPORAL_SPATIAL_AUDIT','TRANSPORT_CARBON_SCOPE_AUDIT','USER_INPUT_NEEDED_TRANSPORT','PHASE3B1_TRANSPORT_READINESS']
for n in reports:check(n+' delivered',(R/(n+'.md')).exists() and (R/(n+'.md')).stat().st_size>500)
names=['TRANSPORT_MODE_INVENTORY','TRANSPORT_DATA_PROVENANCE','TRANSPORT_MATERIALITY_REGISTER','TRANSPORT_FIRST_FULLSC_OPTIONS']
tables={}
for n in names:
 data=json.loads((R/f'data/{n}.json').read_text(encoding='utf8'))
 with (R/f'{n}.csv').open(encoding='utf-8-sig',newline='') as f:actual=list(csv.DictReader(f))
 check(n+' exact cell roundtrip',actual==data);tables[n]=data
inv,prov,mat,opt=[tables[n] for n in names]
check('inventory 18 unique mechanisms',len(inv)==len({r['ModeID'] for r in inv})==18)
check('scoped inventory classifications',all(r['Classification'] in ['EXPLICIT_CURRENT','SUPPORTED_NOT_ACTIVE','EMBEDDED','ABSENT','UNKNOWN'] and r['UActualFinalNetwork']=='UNKNOWN_NOT_BUILT_THIS_PHASE' for r in inv))
check('no invented input confirmation',len(prov)==146 and all(r['Status']=='UNVERIFIED' and r['HumanConfirmation']=='PENDING' and r['FinalCandidateValue']=='' for r in prov))
check('source-class controlled vocabulary',all(r['SourceClass'] in ['ASEAN_SPECIFIC','GLOBAL_HARMONIZED','EUROPE_INHERITED','DEFAULT','MANUAL_OVERRIDE','UNKNOWN'] for r in prov))
check('materiality no invented thresholds',len(mat)==15 and all(r['NumericMaterialityThreshold']==r['QuantifiedEffect']=='' and r['PatchExecuted']=='NO' for r in mat))
ids={r['ItemID'] for r in mat}
check('options resolve gates and remain pending',len(opt)==15 and all(set(r['GateIDs'].split(';'))<=ids and r['HumanDecision']=='PENDING_NOT_FROZEN' and r['Implemented']==r['NumericInputsAccepted']=='NO' for r in opt))
check('required candidate class vocabulary',all(r['CandidateClass'] in ['EXPLICIT','EMBEDDED','FIXED','DEFERRED','SYSTEM_RELEVANT_PENDING'] for r in opt))
source=json.loads((R/'evidence/SOURCE_MANIFEST.json').read_text())
check('67 frozen source copies exact',len(source)==67 and all(sha((R/s['local_path']).read_bytes())==s['sha256'] for s in source))
check('fixed P/U source identities',set(s['commit'] for s in source)=={'5bacad702ccfed17ad19ab510fa710651e966f2c','a3616a68ee44592af6527ca9024a90f1956646ae'})
prior=json.loads((R/'evidence/PRIOR_INPUT_MANIFEST.json').read_text())
check('selected prior evidence unchanged',all(sha((R/x['copy']).read_bytes())==sha((ROOT/x['original_repo_path']).read_bytes())==x['sha256'] for x in prior))
cache=json.loads((R/'evidence/CACHED_DEMAND_EVIDENCE.json').read_text(encoding='utf8'))
check('cached small inputs exact',all(sha((R/x['audit_copy']).read_bytes())==x['sha256'] for x in cache['files'] if x.get('audit_copy')))
check('raw bounded extraction documented',cache['summary']['raw_files_scanned']==52 and len(cache['raw_rows'])==123)
check('all retained raw candidate rows year2019',all(r['Year']=='2019' and r['file_sha256'] and r['csv_physical_line_end']>1 for r in cache['raw_rows']))
check('107 nonblank base conversions match retained evidence',sum(r['matches_nonblank_base'] is True for r in cache['conversion_comparison'])==107 and len(cache['conversion_comparison'])==121)
check('14 missing base cells remain marked',len(cache['missing_to_zero'])==14 and sum(p['Issue']=='MISSING_NOT_ZERO' for p in prov)==14)
check('11 road electricity zeros not promoted to observed zero',sum(p['Parameter']=='road electricity' and p['Issue']=='ZERO_FROM_EMPTY_SUBSET_NOT_OBSERVED_ZERO' for p in prov)==11)
network=json.loads((R/'evidence/NETWORK_TRANSPORT_EVIDENCE.json').read_text())
check('four existing networks only',len(network)==4 and [r['role'] for r in network].count('AUTHOR_REFERENCE')==2)
for i,n in enumerate(network[:2]):
 check(f'author sample{i} EV and rail retained',n['component_counts']['loads'].get('land transport EV')==98 and n['component_counts']['loads'].get('rail transport electricity')==98)
 check(f'author sample{i} V2G without EV Store',n['component_counts']['links'].get('V2G')==98 and not any('EV battery' in c or c=='battery storage' for c in n['component_counts']['stores']))
pre=next(n for n in network if n['role']=='TUTORIAL_PRE_STRIP')
check('shipping oil NaN evidence preserved',sum(r.get('weighted_MWh')=='NaN' for r in pre['transport_loads'] if r['carrier']=='shipping oil')==39)
check('shipping H2 NaN evidence preserved',sum(r.get('weighted_MWh')=='NaN' for r in pre['transport_loads'] if r['carrier']=='H2 for shipping')==1)
check('carbon Loads not mislabeled as MWh',all('weighted_tCO2' in r and 'weighted_MWh' not in r for r in pre['transport_loads'] if 'emissions' in r['carrier']))
carbon=json.loads((R/'evidence/CARBON_LEDGER_OBSERVATION.json').read_text())
check('rail carbon conditions documented',carbon['carrier_co2_emissions']['oil']==0 and carbon['rail_named_links']==[] and not any('rail' in r['name'].lower() for r in carbon['atmosphere_loads']))
check('tutorial no activeCO2Limit claim',carbon['global_constraints']['global_constraints_i']==['lv_limit'])
after=json.loads((R/'evidence/MODEL_IDENTITY_AFTER.json').read_text())
check('four protected layers unchanged and clean',after['all_unchanged'] and len(after['models'])==4 and all(m['clean'] for m in after['models']))
readiness=(R/'PHASE3B1_TRANSPORT_READINESS.md').read_text(encoding='utf8')
check('A through O answered',all('| '+s+' ' in readiness for s in 'ABCDEFGHIJKLMNO'))
check('human review ready is not numeric acceptance','TRANSPORT_BOUNDARY_READY_FOR_HUMAN_REVIEW = YES' in readiness and '候选仍PENDING' in readiness)
for p in R.glob('*.py'):ast.parse(p.read_text(encoding='utf8'))
check('audit-script syntax only',True)
receipt=dict(status='PASS',checks_passed=len(checks),checks=checks,scope='artifact consistency, source identities and read-only existing output inspection; not model validation or scientific input acceptance',solver_runs=0,model_code_changes=0,new_numeric_model_inputs=0,transport_boundary_frozen=False,human_review_ready=True)
(R/'evidence/DELIVERY_VALIDATION.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='checks'},indent=2))
