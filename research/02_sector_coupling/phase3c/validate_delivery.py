"""Verify delivery schema/roundtrip, evidence integrity and protected Git identities.

These are audit integrity checks, NOT full-system model tests or numeric acceptance.
"""
from pathlib import Path
import ast,csv,hashlib,json,re
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
checks=[]
def check(name,condition,scope='DELIVERY_INTEGRITY'):
    checks.append(dict(check=name,passed=bool(condition),scope=scope))
    if not condition:raise AssertionError(name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names='INDUSTRY_FIRST_FULLSC_BOUNDARY AGRICULTURE_FIRST_FULLSC_BOUNDARY FULLSC_CARRIER_INVENTORY HYDROGEN_FUEL_BOUNDARY EXTERNAL_COMMODITY_SUPPLY_BOUNDARY CROSS_BORDER_INTERVENTION_CONTRACT CARBON_SCOPE_FREEZE PHASE3_RESEARCH_MODEL_DESIGN_CLOSEOUT PHASE4_ASSEMBLY_HANDOFF'.split()
for name in names:check('requested report '+name,(R/(name+'.md')).is_file())
tables={}
for name,n in [('FULLSC_SECTOR_CARRIER_MATRIX',24),('PHASE4_SYSTEM_BLOCKER_REGISTER',9)]:
    with (R/(name+'.csv')).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    source=json.loads((R/'data'/f'{name}.json').read_text(encoding='utf8'))
    check(name+' CSV preserves all authored records',rows==source and len(rows)==n)
    check(name+' no blank cells or silent None columns',all(all(v is not None and v!='' for v in x.values()) for x in rows))
    tables[name]=rows
matrix=tables['FULLSC_SECTOR_CARRIER_MATRIX'];gates=tables['PHASE4_SYSTEM_BLOCKER_REGISTER']
required={'Power','Buildings Residential','Buildings Services','Road','Rail','Shipping Domestic','Shipping International','Aviation Domestic','Aviation International','Industry','Agriculture','Hydrogen','Synthetic fuels','Gas','Oil','Biomass','CO2'}
check('17 required sectors/carriers',required<={r['Sector_or_Carrier'] for r in matrix})
check('unique matrix subjects',len({r['Sector_or_Carrier'] for r in matrix})==len(matrix))
allowed={'EXPLICIT','EMBEDDED','FIXED','DEFERRED','EXTERNAL_SUPPLY','REPORTING_ONLY','SYSTEM_LEVEL_BLOCKER'}
check('only permitted FirstFullSCStatus values',all(r['FirstFullSCStatus'] in allowed for r in matrix))
check('representation not mistaken for implemented/accepted inputs',all(r['ImplementationState']=='PHASE4_NOT_ASSEMBLED' and r['NumericInputStatus']=='NO_NEW_NUMERIC_INPUT_ACCEPTED' for r in matrix))
ids={r['BlockerID'] for r in gates}
check('nine unique system gates',ids=={f'P4-{i:02}' for i in range(1,10)})
check('all gates are before solve with action/materiality/test',all(r['Stage']=='BEFORE_FIRST_FULLSC_SOLVE' and r['Status']=='SYSTEM_LEVEL_BLOCKER' and all(r[k] for k in ['MaterialImpactPath','AcceptanceTest','Phase4Action']) for r in gates))
check('every matrix blocker resolves or is deferred',all(r['RemainingBlocker']=='NONE_DEFERRED_OUT_OF_SCOPE' or set(r['RemainingBlocker'].split(';'))<=ids for r in matrix))
receipt=json.loads((R/'evidence/TABLE_EXPORT_RECEIPT.json').read_text())
check('two artifact-tool typed exports',len(receipt)==2 and all(r['authoring']=='@oai/artifact-tool' and r['typed_values_roundtrip'] for r in receipt))
for r in receipt:check('preview available '+r['output'],(R/'evidence/previews'/r['output'].replace('.csv','.png')).is_file())
dep=json.loads((R/'evidence/DEPENDENCY_MANIFEST.json').read_text())
for d in dep['dependencies']:
    p=ROOT/d['path'];check('prior evidence unchanged '+d['path'],p.stat().st_size==d['bytes'] and sha(p)==d['sha256'],'UNCHANGED_PRIOR_EVIDENCE')
extra=json.loads((R/'evidence/EXTRA_SOURCE_MANIFEST.json').read_text())
check('five bounded frozen-U source files',len(extra)==5)
for d in extra:
    p=R/d['path'];check('frozen-U blob '+d['file'],d['git_sha']=='a3616a68ee44592af6527ca9024a90f1956646ae' and p.stat().st_size==d['bytes'] and sha(p)==d['sha256'],'FIXED_SOURCE_INTEGRITY')
agri=json.loads((R/'evidence/AGRICULTURE_OBSERVATIONS.json').read_text(encoding='utf8'))
check('agriculture not adopted as new model data',agri['accepted_new_model_values'] is False)
for d in agri['source_files']:check('agriculture observation source hash '+d['path'],sha(ROOT/d['path'])==d['sha256'],'CACHED_OBSERVATION_INTEGRITY')
observations=agri['observations'];cache={}
check('176 distinct agriculture cache observations',len(observations)==176 and len({(x['country'],x['cached_year'],x['field']) for x in observations})==176)
check('all agriculture observations remain UNVERIFIED',all(x['status']=='UNVERIFIED' for x in observations))
for x in observations:
    if x['file'] not in cache:
        with (ROOT/x['file']).open(encoding='utf-8-sig',newline='') as f:cache[x['file']]={r['']:r for r in csv.DictReader(f)}
    check('raw cache text preserved '+x['country']+'/'+x['cached_year']+'/'+x['field'],x['value_text']==cache[x['file']][x['country']][x['field']] and x['missing']==(x['value_text']==''),'CACHED_OBSERVATION_INTEGRITY')
identity=json.loads((R/'evidence/MODEL_IDENTITY_AFTER.json').read_text())
before=json.loads((R/'evidence/MODEL_IDENTITY_BEFORE.json').read_text())
check('four protected Git layers unchanged',len(identity['models'])==4 and identity['all_unchanged'] and [(x['path'],x['commit']) for x in identity['models']]==[(x['path'],x['commit']) for x in before['models']],'PROTECTED_GIT_STATE')
check('existing shipping candidate unchanged and clean',identity['shipping_candidate_clean'] and identity['shipping_candidate_commit']=='85a32dc231458fd753445df38d422b78435b8aad','PROTECTED_GIT_STATE')
for p in R.glob('*.py'):ast.parse(p.read_text(encoding='utf8'));check('audit utility syntax '+p.name,True)
close=(R/'PHASE3_RESEARCH_MODEL_DESIGN_CLOSEOUT.md').read_text(encoding='utf8')
for statement in ['PHASE3_RESEARCH_MODEL_DESIGN_CLOSED = YES','READY_TO_ENTER_PHASE4_ASSEMBLY = YES','READY_FOR_FIRST_FULLSC_SOLVE = NO']:check('explicit gate '+statement,statement in close)
for q in 'ABCDEFGHIJKLMN':check('final question answered '+q,f'| {q} ' in close)
for p in R.glob('*.md'):
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
        if not target.startswith(('http:','https:','#')):check('local report link '+p.name+':'+target,(p.parent/target.split('#')[0]).exists())
record=dict(validation_scope='Audit delivery schemas, exact exports, evidence hashes, protected Git identities. No solver/model-readiness test or numerical input acceptance.',checks=checks,passed=len(checks),failed=0,requested_deliverables=11,matrix_rows=24,phase4_system_gates=9,solver_runs=0,formal_model_changes=0,new_numeric_model_inputs=0,design_closed=True,ready_to_enter_phase4_assembly=True,ready_for_first_fullsc_solve=False)
(R/'evidence/DELIVERY_VALIDATION.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in record.items() if k!='checks'},ensure_ascii=False))
