"""Validate local report/table links, claims, hashes and strict JSON portability."""
from pathlib import Path
import ast,csv,hashlib,json,math,re,os
R=Path(__file__).resolve().parent
def clean(x):
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
    if isinstance(x,list):return [clean(v) for v in x]
    if isinstance(x,float) and not math.isfinite(x):return None
    return x
for name in ['TOPOLOGY_TRACE.json','PAPER_CARBON_ACCOUNTING.json']:
    p=R/name;p.write_text(json.dumps(clean(json.loads(p.read_text())),indent=2,allow_nan=False),encoding='utf-8')
checks=[]
def check(label,ok):
    checks.append({'check':label,'pass':bool(ok)})
    if not ok:raise AssertionError(label)
required=['BASELINE_ARCHITECTURE.md','PAPER_BASELINE_REPRO_STATUS.md','UPSTREAM_SC_BASELINE.md','ENGINEERING_FIX_REGISTER.md','INDUSTRIAL_DEMAND_FIX_REPORT.md','CARBON_EQUIVALENCE_TEST.md','DATA_REPOSITORY_MAP.md','data_registry/DATA_SOURCES.csv','data_registry/DATA_HASHES.csv','RUN_MANIFEST_TEMPLATE.json','NEXT_EXPERIMENT_READINESS.md']
check('all requested deliverables exist',all((R/p).exists() for p in required))
payload=json.loads((R/'REGISTRY_RECORDS.json').read_text())
for name,records in payload.items():
    with (R/name).open(encoding='utf-8-sig',newline='') as f:actual=list(csv.DictReader(f))
    check(name+' count',len(actual)==len(records))
    for expected,got in zip(records,actual):
        for k,v in expected.items():
            if isinstance(v,(int,float)):
                check(name+' numeric cell '+k,math.isclose(float(got[k]),v,rel_tol=1e-14,abs_tol=1e-15))
            else:check(name+' cell '+k,got[k]==str(v if v is not None else ''))
    if name.endswith('DATA_SOURCES.csv'):check('no auto confirmation',all(r['status']!='CONFIRMED' and r['human_confirmation']=='PENDING' for r in actual))
for p in R.glob('*.py'):ast.parse(p.read_text());
check('Python source parses',True)
paths=[]
for folder,dirs,names in os.walk(R):
    dirs[:]=[d for d in dirs if d not in ['node_modules','__pycache__','.git']]
    paths.extend(Path(folder)/n for n in names)
for p in [p for p in paths if p.suffix=='.md']:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if '://' in target or target.startswith('#'):continue
        check('local link '+str(p.relative_to(R))+' -> '+target,(p.parent/target.split('#')[0]).exists())
tests=json.loads((R/'FIX_BRANCH_TESTS.json').read_text());check('fix branch tests passed',all(r['returncode']==0 for r in tests.values()))
check('run-manifest tests passed',all(json.loads((R/'RUN_MANIFEST_TESTS.json').read_text()).values()))
industrial=json.loads((R/'INDUSTRIAL_RECOVERY_EVIDENCE.json').read_text())
check('original GDP source preserved',industrial['raw_source_unchanged'])
check('all observed industry cells conserved',all(r['absolute_error_MWh']<=1e-6+1e-12*abs(r['national_MWh']) for r in industrial['country_carrier_industry_checks']))
check('TL remains absent not zero',next(r for r in industrial['countries'] if r['country']=='TL')['national_MWh'] is None)
for f in json.loads((R/'FIX_COMMITS.json').read_text()):check('portable patch hash '+f['branch'],hashlib.sha256((R/f['patch']).read_bytes()).hexdigest()==f['patch_sha256'])
files=[]
for p in sorted(paths):
    if not p.is_file() or any(x in p.parts for x in ['node_modules','__pycache__']) or p.name in ['FILE_HASHES.json','DELIVERY_VALIDATION.json']:continue
    files.append({'path':str(p.relative_to(R)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(R/'FILE_HASHES.json').write_text(json.dumps(files,indent=2))
summary={'check_count':len(checks),'passed':sum(r['pass'] for r in checks),'file_count':len(files),'bytes':sum(r['bytes'] for r in files),'checks_compact':[r for r in checks if ' cell ' not in r['check']]}
(R/'DELIVERY_VALIDATION.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='checks_compact'},indent=2))
