"""Validate audit artifacts and read-only model boundaries; no optimization or fixes."""
from pathlib import Path
import csv,hashlib,json,re,subprocess
R=Path(__file__).resolve().parent
required=['BUILDINGS_HEAT_SOURCE_TRACE.md','COOLING_ACCOUNTING_TRACE.md','HEAT_ASSUMPTION_REGISTER.csv','BUILDINGS_FUEL_SHIFT_TRACE.md','BUILDINGS_ELECTRICITY_DOUBLE_COUNT_AUDIT.md','BUILDINGS_HEAT_DATA_GAPS.md','BUILDINGS_HEAT_ACCEPTANCE_STATUS.md']
assert all((R/f).is_file() for f in required)
manifest=json.loads((R/'SOURCE_MANIFEST.json').read_text())
for x in manifest['source_files']:
    p=R/'source_snapshot'/x['layer']/x['path']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],p
with (R/'HEAT_ASSUMPTION_REGISTER.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
assert len(rows)==74 and all(r['Status']=='UNVERIFIED' and r['Human_Acceptance']=='PENDING' for r in rows)
assert len(set(r['Parameter'] for r in rows))==len(rows)
broken=[]
for p in R.glob('*.md'):
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if '://' not in link and not (p.parent/link.split('#')[0]).exists():broken.append([p.name,link])
assert not broken,broken
boundaries={
 '/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean':'ce327bfae2abe5526d4c1976173f0f8d08366ba5',
 '/home/jin/research/SGP_ESE5004_Stage2/phase2/paper_reference':'5bacad702ccfed17ad19ab510fa710651e966f2c',
 '/home/jin/research/SGP_ESE5004_Stage2/phase2/upstream_sc_baseline':'a3616a68ee44592af6527ca9024a90f1956646ae',
 '/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model':'a3616a68ee44592af6527ca9024a90f1956646ae'}
result={}
for root,sha in boundaries.items():
    head=subprocess.check_output(['git','-C',root,'rev-parse','HEAD']).decode().strip()
    status=subprocess.check_output(['git','-C',root,'status','--porcelain']).decode()
    assert head==sha and not status,(root,head,status)
    result[root]={'head':head,'working_tree_clean':True}
out={'required_deliverables':len(required),'frozen_source_hashes_verified':len(manifest['source_files']),'assumption_rows':len(rows),'all_unverified':True,'human_acceptance_pending':True,'relative_links_valid':True,'model_boundaries':result,'optimization_executed':False,'audit_validation':'PASS (does not certify scientific acceptance)'}
(R/'evidence/DELIVERY_VALIDATION.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
