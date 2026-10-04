"""Validate audit evidence and report consistency, not code-scanning availability."""
from pathlib import Path
from collections import Counter
import ast,hashlib,json,re,subprocess
R=Path(__file__).resolve().parent;ROOT=R.parents[2];E=R/'evidence'
checks=[]
def check(name,condition):
    checks.append(dict(check=name,passed=bool(condition)))
    if not condition:raise AssertionError(name)
load=lambda n:json.loads((E/(n+'.json')).read_text(encoding='utf8'))
reports='GITHUB_REPOSITORY_HEALTH CODEQL_FAILURE_ROOT_CAUSE GITHUB_ACTIONS_HEALTH CODEQL_WORKFLOW_AUDIT GITHUB_PHASE4_READINESS'.split()
for name in reports:check('requested report '+name,(R/(name+'.md')).is_file())
check('conditional fix report correctly absent',not (R/'CODEQL_FIX_REPORT.md').exists())
run=load('CODEQL_RUN')['response'];jobs=load('CODEQL_JOBS')['response']['jobs'];ann=load('CODEQL_ANNOTATIONS')['response']
check('exact failing identity',run['id']==37048744962 and run['head_sha']=='a3616a68ee44592af6527ca9024a90f1956646ae' and run['event']=='schedule' and run['conclusion']=='failure')
check('one Python job and step5 failure',len(jobs)==1 and jobs[0]['id']==110976558784 and jobs[0]['name']=='Analyze (python)' and [s['number'] for s in jobs[0]['steps'] if s['conclusion']=='failure']==[5])
check('all 10 annotations preserved',len(ann)==10 and Counter(x['annotation_level'] for x in ann)=={'warning':8,'failure':1,'notice':1})
log=(E/'CODEQL_FULL_LOG.txt').read_text(encoding='utf-8-sig');lines=log.splitlines()
errors=[(i,s) for i,s in enumerate(lines,1) if '##[error]' in s]
check('first and only fatal error is upload eligibility',len(errors)==1 and errors[0][0]==1505 and 'Code scanning is not enabled for this repository' in errors[0][1])
check('SARIF generation before fatal upload',log.index('Exported results to SARIF')<log.index('##[error]'))
check('runtime has correct permissions','SecurityEvents: write' in log and 'Contents: read' in log)
check('runtime uses published action series','github/codeql-action@v4.38.0' in log and 'actions/checkout@v7' in log)
check('current feature API failure recorded',all(load(n)['exit_code']!=0 and load(n)['response']['status']=='403' for n in ['CODE_SCANNING_ANALYSES','CODE_SCANNING_DEFAULT_SETUP']))
repo=load('REPOSITORY')['response'];check('private personal repo',repo['private'] and repo['owner']['type']=='User')
check('snapshot captures all visible runs',load('RECENT_RUNS')['response']['total_count']==len(load('RECENT_RUNS')['response']['workflow_runs'])==21)
check('ten workflow registrations',load('WORKFLOWS')['response']['total_count']==10)
check('latest test has seven successes',len(load('TEST_MAIN_JOBS')['response']['jobs'])==7 and all(x['conclusion']=='success' for x in load('TEST_MAIN_JOBS')['response']['jobs']))
g=load('REPOSITORY_GIT_AUDIT')
check('fetch fsck and default ref passed',g['fetch']['exit_code']==g['fsck_exit_code']==0 and g['default_remote_head']==run['head_sha'])
check('nine workflow YAML files parsed',len(g['workflow_yaml'])==9 and all(x['yaml_parsed'] for x in g['workflow_yaml']))
check('no unmerged index/submodule/LFS/environment directories',not any(g[k] for k in ['unmerged_index','submodules','lfs_pointers','environment_paths']))
for x in g['source_snapshots']:
    b=(E/'source'/x.get('snapshot_path',x['path'])).read_bytes();check('fixed Git source '+x['path'],len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'])
for x in load('PRIOR_DEPENDENCIES'):
    b=(ROOT/x['path']).read_bytes();check('prior scientific evidence unchanged '+x['path'],len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'] and b==(E/'prior'/x['path']).read_bytes())
f=load('FINAL_PROTECTED_STATE');check('13 existing worktree states unchanged',f['all_worktree_heads_and_status_unchanged'] and len(f['worktrees'])==13)
check('no actions rerun or model/remote change',all(f[k]==0 for k in ['scientific_files_modified','workflows_modified','model_runs','actions_reruns','remote_mutations']))
check('native research tree unchanged',not subprocess.check_output(['git','-C',str(ROOT),'diff','f5853f0c666a48782d202919c9e96a61619b8ca1','--','research']).strip())
readiness=(R/'GITHUB_PHASE4_READINESS.md').read_text(encoding='utf8')
for q in 'ABCDEFGHIJKL':check('question '+q,f'| {q} ' in readiness)
for state in ['REPOSITORY_HEALTHY = YES','CODEQL_HEALTHY = NO','PHASE1_3_SCIENTIFIC_INTEGRITY_AFFECTED = NO','GITHUB_READY_FOR_PHASE4 = NO','SCIENTIFIC_IMPACT = NONE']:check('explicit status '+state,state in readiness)
for p in R.glob('*.md'):
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
        if not link.startswith(('https:','http:','#')):check('report link '+link,(p.parent/link).exists())
for p in R.glob('*.py'):ast.parse(p.read_text(encoding='utf8'));check('audit utility syntax '+p.name,True)
record=dict(scope='Audit evidence integrity, report consistency, Git identities; not successful CodeQL upload or model validation',passed=len(checks),failed=0,checks=checks,required_reports=5,conditional_fix_report='NOT_APPLICABLE_NO_FIX',external_blocker_documented=True,codeql_healthy=False,model_runs=0,actions_reruns=0)
(E/'DELIVERY_VALIDATION.json').write_text(json.dumps(record,indent=2),encoding='utf8')
manifest=[]
for p in sorted(R.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts and p.name!='EVIDENCE_MANIFEST.json':
        b=p.read_bytes();manifest.append(dict(path=p.relative_to(R).as_posix(),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
(E/'EVIDENCE_MANIFEST.json').write_text(json.dumps(dict(files=manifest),indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in record.items() if k!='checks'}))
