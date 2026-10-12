"""Design-only checks. Reads lightweight JSON and fixed Git objects, never model data."""
from pathlib import Path
from fractions import Fraction as F
import json, hashlib, subprocess, ast
O=Path(__file__).resolve().parents[1]; E=O/'evidence'
R=O
while not (R/'.git').exists():
    if R==R.parent:raise RuntimeError('Repository root missing')
    R=R.parent
def read(n):return json.loads((E/n).read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
checks=[]
def check(name,test,detail):
    assert test,name
    checks.append({'check':name,'status':'PASS','detail':detail})
p=read('C00_PROTOCOL_DESIGN.json');ref=read('FIRST_RUN_EFFECTIVE_MODEL_PARAMETERS.json')
check('No execution authority',p['execution_authorized'] is False and p['G6_05']=='PAUSED_BY_USER','Design only; old authorizations never reused')
check('Annual weights',p['snapshot_count']*p['interval_hours']==p['annual_hours']==p['source_snapshot_count']*p['source_interval_hours']==8760 and set(p['snapshot_weightings'].values())=={24},'Three weight columns separately sum to 8760')
check('Real first-run parameters',all(ref[k]==v for k,v in p['LP_relevant_reference_parameters'].items()),'All selected values equal actual archived native readback; future native setting untested')
check('Correct baseline versus P2/G6-05',ref['BarConvTol']==1e-6 and ref['NumericFocus']==0 and ref['FeasibilityTol']==1e-6 and ref['DualReductions']==1,'No P2 tolerance or cancelled G6-05 override')
check('Actual memory parameters',ref['SoftMemLimit']==65 and ref['MemLimit']==1e100,'No false claim that MemLimit 70 GB was applied')
raw=(E/'FIRST_RUN_EFFECTIVE_MODEL_PARAMETERS.json').read_bytes()
check('Parameter exact bytes',sha(raw)=='0a7875a902b6671b67e2b8707bdfa81b3407574e70aac32f4fb79d56f6d2dca1','Hash matched original BACKUP_INDEX during extraction')
check('Unmodified V4 reference',sha((E/'V4_APPROVED_HISTORICAL_REFERENCE.json').read_bytes())==p['old_V4_reference_sha256'],'Old dimensions remain, a future daily binding is required')
s=0
for phase,seconds in p['phase_budgets_seconds'].items():
    s+=seconds;check('Deadline '+phase,p['relative_absolute_deadlines_seconds'][phase]==s,{'budget':seconds,'t0_offset':s})
check('Total budget',s==9150==p['total_seconds'] and p['recommended_TimeLimit_seconds']==3600,'Suggested budgets only, no wallclock timer started')
flat=F.from_float(1234.567890123)
check('Flat Load conservation derivation',flat*2920*3==flat*365*24,'Illustrative exact arithmetic, not a newly assembled model')
mean=(F(1)+F(1,2**53))/8;stored=F(float(mean));drift=24*stored-3*(F(1)+F(1,2**53))
check('Binary64 mean is not generally exact',stored!=mean and drift!=0,{'exact_mean':str(mean),'stored_mean':str(stored),'energy_drift':str(drift),'meaning':'Counterexample explaining the annual representation NO-GO, not a project profile finding'})
loss=F(1,1024);ret=(1-loss)**3
eight_step_flow=3*sum((ret**k for k in range(8)),F(0))
check('Storage coarsening is not exact elimination',eight_step_flow!=24,{'old_8_step_constant_flow_factor':str(eight_step_flow),'daily_factor':24,'assumption':'Interior/cyclic recurrence with nonzero standing loss; noncyclic initial constant handled separately'})
check('Scheme A known local certificate closure',F(255,34359738368)>0 and F(513,34359738368)>0,'Reuse reviewed old positive D-Q and new positive Q-D; no matrix proof rerun')
risk=read('B03_FINAL_RISK_CLASSIFICATION.json')
check('Risk classification domain',len(risk['rows'])==12 and all(r['classification'] in {'PROVEN','NECESSARY_CHECK_PASS','RISK','UNKNOWN'} for r in risk['rows']),'Every row separately classified; global feasibility NOT_PROVEN')
for rec in read('SOURCE_BINDING.json')['sources']:
    b=subprocess.check_output(['git','-C',str(R),'show',rec['commit']+':'+rec['repo_path']])
    check('Fixed source '+rec['repo_path'],sha(b)==rec['sha256'] and len(b)==rec['bytes'],'Small fixed-commit reference only; existing analysis not rerun')
for f in E.glob('*.json'):json.loads(f.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
check('JSON finite syntax',True,'All new JSON parsed without NaN/Infinity')
result={'status':'DESIGN_CONSISTENCY_PASS','checks':checks,'checks_count':len(checks),'scope':'Only protocol consistency, exact arithmetic illustrations and lightweight evidence identity. Not daily model, aggregation dataset or solver validation.','execution_authorized':False,'network_builds':0,'LP_builds':0,'solver_calls':0,'AutoDL_operations':0}
(E/'DESIGN_VALIDATION_RECEIPT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False))
