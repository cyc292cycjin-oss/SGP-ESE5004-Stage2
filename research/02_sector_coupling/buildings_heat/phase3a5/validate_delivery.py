"""Validate this evidence delivery, not model science or solver results."""
from pathlib import Path
from decimal import Decimal
import ast,csv,hashlib,json,re,collections,sys
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['ASEAN_BUILDINGS_HISTORICAL_ELECTRIC_HEATING_MATRIX','ASEAN_BUILDINGS_ENDUSE_EVIDENCE_MATRIX','BUILDINGS_USEFUL_HEAT_INPUT_CANDIDATES']
tables={};results={}
for n in names:
    ref=json.loads((R/f'data/derived/buildings/{n}.json').read_text(encoding='utf8'))
    with (R/(n+'.csv')).open(encoding='utf-8-sig',newline='') as f:actual=list(csv.DictReader(f))
    assert len(actual)==len(ref)
    for a,b in zip(actual,ref):
        assert set(a)==set(b)
        for k,v in b.items():
            if isinstance(v,(int,float)):assert a[k]!='' and Decimal(a[k])==Decimal(str(v)),(n,k,a[k],v)
            else:assert a[k]==v,(n,k,a[k],v)
    results[n]={'rows':len(actual),'columns':len(actual[0]),'CSV_JSON_value_roundtrip':True,'blank_and_text_exact':True};tables[n]=actual
h=tables[names[0]];c=tables[names[2]];end=tables[names[1]]
cs={'BN','KH','ID','LA','MY','MM','PH','SG','TH','TL','VN'}
assert {(r['Country'],r['Sector'],r['EndUse']) for r in h}=={(a,b,d) for a in cs for b in ['Residential','Services'] for d in ['space','water']}
assert len(h)==44 and len(end)==154 and len(c)==140
assert len({(r['Country'],r['Sector'],r['FuelGroup']) for r in end})==154
assert len({r['CandidateID'] for r in c})==140
assert len(c[0])==47
assert all(r['Status']=='UNVERIFIED' and r['HumanConfirmationRecord']=='PENDING' for r in c)
assert all(r['UsefulService']==r['Efficiency_or_COP']==r['DeviceInputShare']=='' for r in c)
assert all(r['Status'] in ['PENDING','UNVERIFIED'] and r['HumanConfirmation']=='PENDING' for r in h+end)
assert sum(r['RawElectricity']!='' for r in h)==2
assert all(r['EndUseShare']=='1' for r in c if r['FinalEnergyScope']=='end_use')
assert all(r['Blocker'] and r['SourceLocation'] and r['SourceRowID'] and r['SourceSHA256'] for r in c)
assert all(r['CookingDestination'] in ['DirectElectricity','DirectFuel','Unclassified'] for r in c)
assert all(r['RetainedDestination']!='ThermalEvidence_pending_conversion' for r in c if r['EndUse']=='cooking')
assert not any(r['RawElectricity']=='0' for r in h)
refs={r['CandidateID'] for r in c}
for r in end:
 for k,v in r.items():
  if k.endswith('_evidence') and v!='UNKNOWN':assert set(v.split('; '))<=refs
reg=json.loads((R/'data/raw/buildings/SOURCE_REGISTRY.json').read_text(encoding='utf8'))
assert len({r['source_id'] for r in reg})==len(reg)
for r in reg:
    for key in ['url','version','year','license','purpose']:assert key in r and r[key],(r['source_id'],key)
    if r.get('file'):assert sha(R/r['file'])==r['sha256'],r['file']
for r in c:assert sha(R/r['SourceFile'])==r['SourceSHA256']
for rec in json.loads((R/'evidence/CODE_IDENTITY.json').read_text()):
 assert rec['clean']
 for f in rec['files']:assert sha(R/'evidence/source_snapshot'/rec['layer']/f['path'])==f['sha256']
b=json.loads((R/'data/processed/buildings/BOUNDARY_SOURCE_CHECKS.json').read_text())
for fn in ['include_electricity_growth','redistribute_industrial_load']:
 assert len({b['functions'][layer][fn]['ast_sha256'] for layer in ['P','U','V']})==1,fn
assert b['functions']['U']['add_electricity_distribution_grid']['ast_sha256']==b['functions']['V']['add_electricity_distribution_grid']['ast_sha256']
assert b['functions']['U']['actual_elec_carrier']==['AC','industry electricity','agriculture electricityrail transport electricity']
required=['BASE_ELECTRICITY_BOUNDARY_TRACE','BUILDINGS_FINAL_TO_USEFUL_EVIDENCE','BUILDINGS_YEAR_BRIDGE_METHOD','BUILDINGS_SPACE_WATER_MAPPING',
 'BUILDINGS_TEMPORAL_METHOD','BUILDINGS_SPATIAL_ALLOCATION_OPTIONS','BUILDINGS_E3_EVIDENCE_GAPS','USER_INPUT_NEEDED_BUILDINGS','BUILDINGS_PHASE3A5_READINESS']
for n in required:assert (R/(n+'.md')).is_file()
for p in R.glob('*.md'):
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
  if re.match(r'[a-z]+://',link):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link)
checks=json.loads((R/'data/processed/buildings/CANDIDATE_SOURCE_CHECKS.json').read_text())
assert checks['raw_UNSD_rows_matched']==92 and checks['useful_service_values_filled']==0
result=dict(phase='3A5',validation_scope='research evidence only; not scientific acceptance or model regression',tables=results,
  source_records=len(reg),local_source_hashes_verified=sum(bool(r.get('file')) for r in reg),
  protected_snapshot_files_verified=sum(len(r['files']) for r in json.loads((R/'evidence/CODE_IDENTITY.json').read_text())),
  source_rows_matched=92,required_deliverables=12,accepted_scientific_inputs=0,solver_runs=0,E3_patch=False,
  source_discrepancies_retained=True,unknown_heating_not_zero=True,overall='PASS',E3_implementation_ready=False)
(R/'evidence/DELIVERY_VALIDATION.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
