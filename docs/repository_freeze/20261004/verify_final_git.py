"""Check protected identities and withheld archive reachability after push."""
from pathlib import Path
import json,subprocess
from datetime import datetime,timezone
R=Path(__file__).resolve().parent;E=R/'evidence';REPO='/home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit'
def run(*a,repo=REPO):
 p=subprocess.run(['git','-C',repo,*a],capture_output=True)
 return {'exit_code':p.returncode,'stdout':p.stdout.decode('utf8','replace').strip(),'stderr':p.stderr.decode('utf8','replace').strip()}
def git(*a,**kw):
 p=run(*a,**kw);assert not p['exit_code'],p;return p['stdout']
before=json.loads((E/'WSL_BEFORE.json').read_text());checks=[]
for x in before['worktrees']:
 now=dict(path=x['path'],head=git('rev-parse','HEAD',repo=x['path']),branch=git('branch','--show-current',repo=x['path']),status=git('status','--porcelain',repo=x['path']))
 checks.append(dict(**now,unchanged=now==x));assert now==x,(x,now)
refs=json.loads((E/'REFS_BEFORE.json').read_text())
for ref,sha in refs['local'].items():assert git('rev-parse',ref)==sha
assert git('rev-parse','origin/main')=='a3616a68ee44592af6527ca9024a90f1956646ae'
assert run('show-ref','--verify','refs/heads/research/full-sc-baseline')['exit_code']!=0
assert run('show-ref','--verify','refs/remotes/origin/research/full-sc-baseline')['exit_code']!=0
remote_refs=git('for-each-ref','--format=%(refname)','refs/remotes/origin','refs/tags/reference/').splitlines()
archive='753ff15b45ddb91c406a823f8252fc7b603f29c4'
unarchived=git('rev-list',archive,'--not',*remote_refs).splitlines();assert len(unarchived)==15
risk_paths=['research/00_model_audit/input_snapshot/data/industry/us_cities.csv']+['research/00_source_provenance/official/technology-data/inputs/'+n for n in ['data_sheets_for_renewable_fuels.xlsx','technology_data_catalogue_for_energy_storage.xlsx','technology_data_for_el_and_dh.xlsx']]
held=[]
for ref,sha in refs['local'].items():
 paths=git('ls-tree','-r','--name-only',sha,'--',*risk_paths).splitlines()
 if paths:held.append(dict(ref=ref,sha=sha,paths=paths))
coverage=[]
for family in json.loads((E/'ARCHIVE_FAMILIES.json').read_text()):
 containing=[ref for ref in remote_refs if run('merge-base','--is-ancestor',family['latest_commit'],ref)['exit_code']==0]
 coverage.append(dict(family=family['family'],commit=family['latest_commit'],remote_contains=containing))
obj=dict(utc=datetime.now(timezone.utc).isoformat(),protected_worktrees=checks,local_branches_unchanged=True,main_unchanged=True,phase4_absent=True,unarchived_commits=unarchived,withheld_research_branches=held,report_commit_coverage=coverage,model_edits=0,solver_runs=0,merges=0)
(E/'FINAL_PROTECTED_STATE.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'protected_worktrees':len(checks),'unchanged':True,'archive_commits_still_local':len(unarchived),'held_branches':len(held),'report_families_still_local':len(coverage)}))
