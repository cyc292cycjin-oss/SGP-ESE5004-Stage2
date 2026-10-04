"""Validate only the new Phase3A7 documentary handoff, not a model experiment."""
from pathlib import Path
import json,csv,hashlib,re,ast
R=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
names=['BUILDINGS_FIRST_FULLSC_BOUNDARY','BUILDINGS_MATERIALITY_REGISTER']
tables={}
for name in names:
    expected=json.loads((R/f'data/{name}.json').read_text(encoding='utf8'))
    with (R/f'{name}.csv').open(encoding='utf-8-sig',newline='') as f: actual=list(csv.DictReader(f))
    check(name+' CSV exact JSON roundtrip',actual==expected)
    tables[name]=actual
rows=tables[names[0]];register=tables[names[1]]
required='Country Sector SpaceHeating WaterHeating Cooling Cooking DirectElectricity DirectFuel Representation EvidenceStatus FullSC_Blocker Reason'.split()
check('required columns',set(required)<=set(rows[0]))
countries='BN KH ID LA MM MY PH SG TH TL VN'.split()
check('11 countries x separate R/S, no duplicate keys',len(rows)==22 and {(r['Country'],r['Sector']) for r in rows}=={(c,s) for c in countries for s in ['Residential','Services']})
check('44 thermal uses retained embedded; no unknown-to-zero substitution',all(r['SpaceHeating']==r['WaterHeating']=='EMBEDDED' for r in rows))
check('cooling and cooking retained once',all(r['Cooling']=='EMBEDDED' and r['Cooking']=='EMBEDDED_ACCOUNTING_ONLY' for r in rows))
check('separate final accounts explicitly retained',all('KEEP_ONCE' in r['DirectElectricity'] and 'KEEP_ONCE' in r['DirectFuel'] and 'never add parent plus children' in r['ParentContainment'] for r in rows))
check('no numerical input accepted or written',all(r['NumericDataAcceptance']=='PENDING_UNCHANGED' and r['NumericInputWritten']=='NO' for r in rows))
check('thermal promotion still pending locally',all(r['ThermalPromotionStatus']=='PENDING_LOCAL_EVIDENCE_IF_MATERIAL' for r in rows))
check('15 unique materiality entries',len(register)==15 and {r['ItemID'] for r in register}=={f'M{i:02}' for i in range(1,16)})
ids={r['ItemID'] for r in register}
check('all shared gates resolve',all(set(r['SharedGateIDs'].split(';'))<=ids for r in rows))
check('materiality qualitative, no invented numeric thresholds',all(r['NumericThreshold']==r['QuantifiedMateriality']=='' and r['CredibleMaterialityPathway'] and r['MinimumClosureOrContainment'] and r['ReopenTrigger'] for r in register))
check('M01-M06 shared assembly gates; M15 comparison gate',all(r['FullSC_Blocker']=='YES_BEFORE_NUMERIC_ASSEMBLY' for r in register[:6]) and register[-1]['FullSC_Blocker']=='YES_BEFORE_COMPARATIVE_EXPERIMENT')
manifest=json.loads((R/'evidence/INPUT_MANIFEST.json').read_text(encoding='utf8'))
check('all 16 retained dependencies unchanged',len(manifest)==16 and all(sha((R/r['path']).read_bytes())==r['sha256'] for r in manifest))
heat=json.loads((R.parent/'phase3a5/data/derived/buildings/ASEAN_BUILDINGS_HISTORICAL_ELECTRIC_HEATING_MATRIX.json').read_text(encoding='utf8'))
for row in rows:
    refs=re.findall(r'P5_HEAT_ROW_(\d+):',row['Evidence'])
    check(row['Country']+'/'+row['Sector']+' evidence row identity',len(refs)==2 and all((heat[int(n)-1]['Country'],heat[int(n)-1]['Sector'])==(row['Country'],row['Sector']) for n in refs))
reports=['RESEARCH_ELECTRICITY_BOUNDARY_FREEZE','BUILDINGS_MINIMUM_DEFENSIBLE_BASELINE','BUILDINGS_PHASE3_CLOSEOUT','NEXT_SECTOR_HANDOFF']
for name in reports:check(name+' exists',len((R/f'{name}.md').read_text(encoding='utf8'))>500)
freeze=(R/(reports[0]+'.md')).read_text(encoding='utf8')
check('frozen human concept distinguished from numerical acceptance','HUMAN_FROZEN_CONCEPT' in freeze and 'NOT SCIENTIFICALLY ACCEPTED' in freeze and 'PENDING' in freeze)
closeout=(R/'BUILDINGS_PHASE3_CLOSEOUT.md').read_text(encoding='utf8')
check('A-G answered',all('| '+letter+' ' in closeout for letter in 'ABCDEFG'))
check('next-sector scoping and numerical readiness distinguished','BUILDINGS_CLOSED_FOR_NEXT_SECTOR_SCOPING | YES' in closeout and 'NUMERICAL_FULLSC_ASSEMBLY_VERIFIED | NO' in closeout)
identity=json.loads((R/'evidence/MODEL_IDENTITY.json').read_text())
check('four model identities protected and clean',len(identity['protected_models'])==4 and all(r['clean'] for r in identity['protected_models']))
for p in R.glob('*.py'):ast.parse(p.read_text(encoding='utf8'))
check('supporting Python syntax',True)
receipt=dict(status='PASS',checks_passed=len(checks),checks=checks,scope='documentary consistency and protected Git identity only; not numerical model acceptance',model_runs=0,formal_E3_implemented=False,new_numeric_model_inputs=0)
(R/'evidence/DELIVERY_VALIDATION.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='checks'},indent=2))
