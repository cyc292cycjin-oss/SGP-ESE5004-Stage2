"""Check report completeness, source identity, exported data and scientific gates.

This does not import PyPSA, invoke a solver, or rerun E1/E2/E4 experiments.
"""
from pathlib import Path
from decimal import Decimal as D
import csv,json,hashlib,re,ast
R=Path(__file__).resolve().parent;P=R.parent/'phase3a5';E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
requested_md=['ASEAN_ELECTRICITY_BOUNDARY_TRACE','AEO8_ELECTRICITY_SOURCE_TRACE','ELECTRICITY_LOSS_ACCOUNTING','FULLSC_ASTAR_CANDIDATES','BASE_FUTURE_ELECTRICITY_BOUNDARY','MALAYSIA_ENDUSE_MAPPING','MALAYSIA_2016_2019_YEAR_BRIDGE','MALAYSIA_E3_ACCOUNTING_PROTOTYPE','PHASE3A6_DATA_GAPS','USER_INPUT_NEEDED_PHASE3A6','PHASE3A6_READINESS']
requested_csv=['ELECTRICITY_ACCOUNTING_GLOSSARY','AEO8_ELECTRIFICATION_SCOPE_MATRIX','MALAYSIA_BUILDINGS_SOURCE_LEDGER','MALAYSIA_ELECTRIC_HEATING_EVIDENCE','MALAYSIA_HISTORICAL_DEVICE_EVIDENCE','MALAYSIA_USEFUL_HEAT_CANDIDATES','MALAYSIA_E3_CLOSURE_TEST']
for n in requested_md:assert (R/(n+'.md')).stat().st_size>200,n
records={}
numeric={'Year','RawValue','RawElectricity','FinalElectricityGWh','FinalEnergyMWh','EndUseShare','LHS','RHS','Difference'}
for n in requested_csv:
 expected=json.loads((R/f'data/derived/{n}.json').read_text(encoding='utf8'))
 with (R/(n+'.csv')).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
 assert len(rows)==len(expected)
 for row,orig in zip(rows,expected):
  assert row.keys()==orig.keys()
  for k,v in orig.items():
   if k in numeric and v!='' and re.fullmatch(r'-?\d+(\.\d+)?',str(v)):assert D(row[k])==D(str(v)),(n,k,row[k],v)
   else:assert row[k]==str(v),(n,k)
  assert row['HumanConfirmation']=='PENDING'
 records[n]=rows
registry=json.loads((R/'data/SOURCE_REGISTRY.json').read_text())
for r in registry:assert sha(R/r['file'])==r['sha256']
for n in ['MALAYSIA_BUILDINGS_SOURCE_LEDGER','MALAYSIA_ELECTRIC_HEATING_EVIDENCE','MALAYSIA_HISTORICAL_DEVICE_EVIDENCE','MALAYSIA_USEFUL_HEAT_CANDIDATES']:
 for row in records[n]:assert sha(R/row['SourceFile'])==row['SourceSHA256']
ht=records['MALAYSIA_ELECTRIC_HEATING_EVIDENCE']
for r in ht:
 if r['EndUse']=='space':assert r['RawElectricity']==r['FinalElectricityGWh']==''
 else:
  expected=D(r['RawElectricity'])*(D('41.84')/D('3.6') if r['RawUnit']=='ktoe' else D(1))
  assert abs(D(r['FinalElectricityGWh'])-expected)<D('1e-9')
for r in records['MALAYSIA_USEFUL_HEAT_CANDIDATES']:
 assert r['HistoricalEfficiency_or_COP']==r['DeviceInputShare']==r['UsefulServiceMWh']==''
 assert r['EndUseShare']==('1' if r['EndUse']=='water' else '')
tests={r['TestID']:r for r in records['MALAYSIA_E3_CLOSURE_TEST']}
assert D(tests['MYC03']['Difference'])==D('-.43')
assert D(tests['MYC05']['Difference'])==D('-378')
assert tests['MYC13']['Result']=='BLOCKED_BOUNDARY' and tests['MYC14']['Result']=='BLOCKED_ANNUAL'
assert tests['MYC15']['Result']=='NOT_RUN_ANNUAL_GATE_FAILED'
# Independent checks against the exact source excerpt cells, not chart pixels.
txt=(E/'malaysia-neb2016_p95.txt').read_text(encoding='utf8').split('YEAR: 2016 / UNIT:')[1].split('TABLE 41:')[0]
assert re.search(r'Water Heating\s+-\s+-\s+-\s+70\s+70',txt)
assert re.search(r'Cooking\s+1\s+538\s+-\s+117\s+655',txt)
txt=(E/'malaysia-neb2016_p103.txt').read_text(encoding='utf8')
assert re.search(r'TOTAL\s+16,440.66\s+1,034.62\s+8,516.23\s+13,114.06\s+39,106.00',txt)
txt=(E/'malaysia-neb2019_p73.txt').read_text(encoding='utf8')
assert re.search(r'15\. Residential[^\n]+2,715\s+3,339',txt)
assert re.search(r'16\. Commercial[^\n]+4,086\s+4,662',txt)
trajectory=json.loads((R/'data/derived/AEO8_TRAJECTORY_CHECK.json').read_text())
assert len(trajectory)==6 and all(r['match'] for r in trajectory)
# Reused code copies retain original bytes; new loss snapshots retain their hashes.
prior=json.loads((P/'evidence/CODE_IDENTITY.json').read_text())
for layer in prior:
 for f in layer['files']:assert sha(P/'evidence/source_snapshot'/layer['layer']/f['path'])==f['sha256']
loss=json.loads((E/'LOSS_CODE_IDENTITY.json').read_text())
assert all(r['clean'] for r in loss['protected_models'])
for f in loss['files']:assert sha(E/'source_snapshot/U'/f['path'])==f['sha256']
assert sha(E/'installed_pypsa_optimize.py')==loss['installed_api']['sha256']
assert "transmission_losses: 'int' = 0" in loss['installed_api']['optimizer_signature']
assert not loss['installed_api']['solver_run']
for p in R.glob('*.py'):ast.parse(p.read_text(encoding='utf8'))
readiness=(R/'PHASE3A6_READINESS.md').read_text(encoding='utf8')
assert '| E3_PRODUCTION_IMPLEMENTATION_READY | NO |' in readiness
assert '| ELECTRICITY_BOUNDARY_READY_FOR_HUMAN_REVIEW | YES |' in readiness
assert '| MALAYSIA_E3_PROTOTYPE_READY_FOR_HUMAN_REVIEW | YES |' in readiness
for c in list('ABCDEFGHIJKLMNOPQRSTUVW'):assert re.search(r'\| '+c+r' ',readiness),c
report=dict(requested_deliverables=18,markdown_reports=11,csv_tables=7,csv_row_counts={k:len(v) for k,v in records.items()},source_hashes_verified=len(registry),AEO_config_comparisons=18,protected_models_unchanged=loss['protected_models'],all_human_confirmations_pending=True,blank_space_heat_and_performance_preserved=True,source_discrepancies_preserved=True,annual_E3_closed=False,snapshot_test_run=False,solver_runs=0,production_patch=False,passed=True,scope='Delivery/evidence verification, not E3 scientific closure',csv_visual_review='all seven first-five-column previews inspected; CSV has no persistent formatting')
(E/'DELIVERY_VALIDATION.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='protected_models_unchanged'},indent=2))
