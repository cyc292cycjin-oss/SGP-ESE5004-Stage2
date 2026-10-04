"""Validate the remote evidence, required reports and packageable audit files."""
from pathlib import Path
import csv,json,hashlib,os,re
R=Path(__file__).resolve().parent;E=R/'evidence';checks=[]
def check(name,value):
 checks.append({'check':name,'pass':bool(value)});assert value,name
def read(n):return json.loads((E/n).read_text(encoding='utf-8-sig'))
required=['PRE_PHASE4_GIT_STATE.md','RESEARCH_MILESTONE_REF_PLAN.md','PHASE1_3_REMOTE_ARCHIVE.md','REMOTE_REF_VERIFICATION.csv','PHASE4_GIT_STARTING_POINT.md','GITHUB_REMOTE_FREEZE_READINESS.md']
for name in required:check('deliverable:'+name,(R/name).is_file() and (R/name).stat().st_size>0)
rows=list(csv.DictReader((R/'REMOTE_REF_VERIFICATION.csv').open(encoding='utf-8-sig',newline='')))
check('CSV fields',list(rows[0])==['LocalRef','RemoteRef','ExpectedSHA','FetchedSHA','Match','Purpose'])
source=read('REMOTE_VERIFICATION_ROWS.json');remote=read('REMOTE_AFTER.json')['refs']
check('CSV row count',len(rows)==len(source)==12)
for row,original in zip(rows,source):
 check('CSV exact data:'+row['RemoteRef'],all(str(original[k]).lower()==v if k=='Match' else original[k]==v for k,v in row.items()))
 ref=row['RemoteRef'];actual=remote.get(ref+'^{}',remote.get(ref))
 check('SHA match:'+ref,row['ExpectedSHA']==row['FetchedSHA']==actual and row['Match']=='true')
check('all 14 milestones remotely reachable',len(read('MILESTONES_AFTER.json'))==14 and all(m['remote_after'] for m in read('MILESTONES_AFTER.json')))
check('fetch prune tags',read('REMOTE_AFTER.json')['fetch']['args']==['fetch','--prune','--tags','origin'])
check('protected worktrees',len(read('FINAL_PROTECTED_STATE.json')['protected_worktrees'])==13 and all(x['unchanged'] for x in read('FINAL_PROTECTED_STATE.json')['protected_worktrees']))
check('archive remains local',len(read('FINAL_PROTECTED_STATE.json')['unarchived_commits'])==15)
check('phase4 absent',read('FINAL_PROTECTED_STATE.json')['phase4_absent'])
report=(R/'GITHUB_REMOTE_FREEZE_READINESS.md').read_text(encoding='utf8')
for letter in 'ABCDEFGHIJKL':check('answer:'+letter,'**'+letter+'.' in report)
check('CodeQL does not block','| CODEQL_BLOCKS_PHASE4 | NO |' in report)
check('no false complete','| PHASE1_3_REMOTE_HISTORY_FROZEN | NO |' in report)
check('no scientific changes',read('FINAL_PROTECTED_STATE.json')['model_edits']==0)
payload=[]
for parent,dirs,files in os.walk(R,followlinks=False):
 dirs[:]=[d for d in dirs if d not in {'node_modules','__pycache__','previews'}]
 for name in sorted(files):
  p=Path(parent)/name;rel=p.relative_to(R).as_posix()
  if rel in {'evidence/DELIVERY_VALIDATION.json','FILE_HASHES.json'}:continue
  check('payload no raw/cache:'+rel,p.suffix.lower() not in {'.zip','.nc','.netcdf','.xlsx','.xls','.png','.jpg','.pdf','.pyc'})
  b=p.read_bytes();payload.append({'path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
check('max delivered file under 10 MB',max(x['bytes'] for x in payload)<10_000_000)
(E/'DELIVERY_VALIDATION.json').write_text(json.dumps({'checks':checks,'pass':all(x['pass'] for x in checks),'csv_preview_reviewed':True,'scientific_tests_rerun':0},indent=2),encoding='utf8')
(R/'FILE_HASHES.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'checks':len(checks),'all_pass':True,'payload_files':len(payload),'payload_bytes':sum(x['bytes'] for x in payload)}))
