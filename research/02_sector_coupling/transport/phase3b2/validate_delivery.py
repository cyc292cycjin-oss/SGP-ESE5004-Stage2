"""Validate delivery content/integrity, not numerical model readiness."""
from pathlib import Path
import ast,csv,hashlib,json,re
R=Path(__file__).resolve().parent;ROOT=R.parents[3];B=R.parent/'phase3b1'
checks=[]
def check(name,condition,scope='DELIVERY_INTEGRITY'):
    checks.append(dict(check=name,passed=bool(condition),scope=scope))
    if not condition: raise AssertionError(name)
names='TRANSPORT_MINIMUM_DEFENSIBLE_BASELINE ROAD_ENERGY_ACCOUNTING_SPEC ROAD_EV_ELECTRICITY_ACCOUNTING RAIL_EMBEDDED_ACCOUNTING SHIPPING_FUEL_ACCOUNTING AVIATION_FUEL_ACCOUNTING TRANSPORT_SYNTHETIC_FUEL_ACCOUNTING TRANSPORT_CARBON_ACCOUNTING_CONTRACT TRANSPORT_SPATIAL_TEMPORAL_MINIMUM TRANSPORT_ENGINEERING_FIX_REPORT TRANSPORT_PHASE3_CLOSEOUT NEXT_FULLSC_HANDOFF'.split()
for name in names:check('requested '+name,(R/(name+'.md')).is_file())
for name,n in [('TRANSPORT_FIRST_FULLSC_BOUNDARY',13),('TRANSPORT_FIX_TEST_MATRIX',17),('TRANSPORT_MATERIALITY_CLOSEOUT',16)]:
    with (R/(name+'.csv')).open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    source=json.loads((R/'data'/f'{name}.json').read_text(encoding='utf8'))
    check(name+' exact CSV roundtrip',rows==source and len(rows)==n)
receipt=json.loads((R/'evidence/TABLE_EXPORT_RECEIPT.json').read_text())
check('three artifact-tool exports',len(receipt)==3 and all(x['authoring']=='@oai/artifact-tool' and x['typed_values_roundtrip'] for x in receipt))
before=json.loads((R/'evidence/SHIPPING_TEST_BEFORE.json').read_text())
after=json.loads((R/'evidence/SHIPPING_TEST_AFTER.json').read_text())
check('same 15 regression cases',sorted(x['test'] for x in before['tests'])==sorted(x['test'] for x in after['tests']) and len(after['tests'])==15,'OFFLINE_TEST_RECEIPT')
check('14 baseline nonpass',sum(x['status']!='PASS' for x in before['tests'])==14 and not before['passed'],'OFFLINE_TEST_RECEIPT')
check('15 candidate passes',after['passed'] and all(x['status']=='PASS' for x in after['tests']),'OFFLINE_TEST_RECEIPT')
guard_before=json.loads((R/'evidence/SHIPPING_TARGET_GUARD_BEFORE.json').read_text())
guard_after=json.loads((R/'evidence/SHIPPING_TARGET_GUARD_AFTER.json').read_text())
check('two target failures reproduced',len(guard_before['tests'])==17 and sum(x['status']!='PASS' for x in guard_before['tests'])==2,'OFFLINE_TEST_RECEIPT')
check('17 final passes',len(guard_after['tests'])==17 and guard_after['passed'] and all(x['status']=='PASS' for x in guard_after['tests']),'OFFLINE_TEST_RECEIPT')
candidate=json.loads((R/'evidence/SHIPPING_CANDIDATE_IDENTITY.json').read_text())
check('candidate based on fixed U',candidate['base']=='a3616a68ee44592af6527ca9024a90f1956646ae')
check('isolated candidate chain',candidate['commit']=='85a32dc231458fd753445df38d422b78435b8aad' and len(candidate['candidate_commits'])==3 and not candidate['merged_into_research_model'])
check('candidate patch SHA',hashlib.sha256((R/'candidate/SHIPPING_ALLOCATION.patch').read_bytes()).hexdigest()==candidate['patch_sha256'])
check('candidate restricted changed files',set(candidate['changed_files'])=={'.gitattributes','scripts/prepare_sector_network.py','scripts/_shipping_allocation.py','tests/transport/test_shipping_allocation.py'})
check('byte-fidelity has no semantic change',candidate['ast_unchanged_from_tested_guard'])
obs=json.loads((R/'evidence/COUNTRY_ACCOUNT_OBSERVATIONS.json').read_text(encoding='utf8'))
old=json.loads((B/'evidence/CACHED_DEMAND_EVIDENCE.json').read_text(encoding='utf8'))
check('44 country-account observations',len(obs['observations'])==44 and len({(x['country'],x['account']) for x in obs['observations']})==44)
check('cached values unchanged',all(x['base_text']==old['tables']['base'][x['country']][x['cached_column']] for x in obs['observations']))
check('all numeric observations UNVERIFIED',all(x['acceptance_status']=='UNVERIFIED_NUMERIC_INPUT' for x in obs['observations']))
check('missing shipping cells preserved',sum(x['base_text']=='' for x in obs['observations'])==6)
dep=json.loads((R/'evidence/DEPENDENCY_MANIFEST.json').read_text())
for row in dep['dependencies']:
    p=ROOT/row['path'];check('prior unchanged '+row['path'],p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'])
identity=json.loads((R/'evidence/MODEL_IDENTITY_AFTER.json').read_text())
check('four protected models unchanged',len(identity['models'])==4 and identity['all_unchanged'],'PROTECTED_GIT_STATE')
check('candidate clean',identity['candidate_clean'],'PROTECTED_GIT_STATE')
for p in list(R.glob('*.py'))+list((R/'candidate').glob('*.py')):
    ast.parse(p.read_text(encoding='utf8'));check('syntax '+p.name,True)
close=(R/'TRANSPORT_PHASE3_CLOSEOUT.md').read_text(encoding='utf8')
check('honest no model-ready declaration','TRANSPORT_CLOSED_FOR_FULLSC_ASSEMBLY = NO' in close and 'NUMERICAL_INPUTS_AND_IMPLEMENTATION_FROZEN = NO' in close)
for question in 'ABCDEFGHIJKLM':check('final answer '+question,f'| {question} ' in close)
for p in list(R.glob('*.md')):
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
        if not target.startswith(('http:', 'https:', '#')):check('local link '+p.name+':'+target,(p.parent/target.split('#')[0]).exists())
summary=dict(validation_scope='Delivery files, unchanged evidence, isolated offline test receipts and Git identity; NOT a full-system solve or numerical acceptance',checks=checks,passed=sum(x['passed'] for x in checks),failed=0,solver_runs=0,formal_model_modified=False,candidate_functional_fixes=2,candidate_commits=3,transport_research_scope_closed=True,representation_frozen_by_user=True,transport_closed_for_fullsc_assembly=False)
(R/'evidence/DELIVERY_VALIDATION.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in summary.items() if k!='checks'},ensure_ascii=False))
