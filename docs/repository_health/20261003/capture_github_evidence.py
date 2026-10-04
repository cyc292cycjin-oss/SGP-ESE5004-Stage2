"""Bounded read-only GitHub API/log evidence capture. Does not rerun workflows."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import json,subprocess,hashlib
R=Path(__file__).resolve().parent;E=R/'evidence';E.mkdir(exist_ok=True)
REPO='cyc292cycjin-oss/SGP-ESE5004-Stage2';BASE='repos/'+REPO
RUN=37048744962;JOB=110976558784
queries={
 'REPOSITORY':BASE,'REMOTE_BRANCHES':BASE+'/branches?per_page=100',
 'REMOTE_TAGS':BASE+'/tags?per_page=100','WORKFLOWS':BASE+'/actions/workflows?per_page=100',
 'RECENT_RUNS':BASE+'/actions/runs?per_page=100',
 'ACTIONS_PERMISSIONS':BASE+'/actions/permissions',
 'DEFAULT_TOKEN_PERMISSIONS':BASE+'/actions/permissions/workflow',
 'CODE_SCANNING_DEFAULT_SETUP':BASE+'/code-scanning/default-setup',
 'CODE_SCANNING_ANALYSES':BASE+'/code-scanning/analyses?per_page=5',
 'CODEQL_RUN':BASE+f'/actions/runs/{RUN}',
 'CODEQL_JOBS':BASE+f'/actions/runs/{RUN}/jobs?per_page=100',
 'CODEQL_CHECK':BASE+f'/check-runs/{JOB}',
 'CODEQL_ANNOTATIONS':BASE+f'/check-runs/{JOB}/annotations?per_page=100',
 'CODEQL_ARTIFACTS':BASE+f'/actions/runs/{RUN}/artifacts',
 'CODEQL_RUN_HISTORY':BASE+'/actions/workflows/368257323/runs?per_page=50',
 'TEST_MAIN_JOBS':BASE+'/actions/runs/36524269304/jobs?per_page=100',
 'TEST_PUSH_JOBS':BASE+'/actions/runs/36313652191/jobs?per_page=100',
 'TEST_PR_JOBS':BASE+'/actions/runs/36313847580/jobs?per_page=100',
 'LOCKED_ENVS_JOBS':BASE+'/actions/runs/36834440056/jobs?per_page=100',
 'PAGES_JOBS':BASE+'/actions/runs/36313652188/jobs?per_page=100',
 'MAIN_WORKFLOW_JOBS':BASE+'/actions/runs/36817994582/jobs?per_page=100',
 'LINT_JOBS':BASE+'/actions/runs/36313847449/jobs?per_page=100',
 'MAIN_TREE':BASE+'/git/trees/a3616a68ee44592af6527ca9024a90f1956646ae?recursive=1',
}
def capture(item):
 name,endpoint=item
 p=subprocess.run(['gh','api',endpoint],capture_output=True)
 try:body=json.loads(p.stdout.decode('utf-8-sig'))
 except (ValueError,UnicodeDecodeError):body=p.stdout.decode('utf8',errors='replace')
 record=dict(endpoint=endpoint,fetched_utc=datetime.now(timezone.utc).isoformat(),exit_code=p.returncode,response=body,stderr=p.stderr.decode('utf8',errors='replace'))
 (E/(name+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
 return dict(name=name,exit_code=p.returncode)
with ThreadPoolExecutor(max_workers=4) as pool:status=list(pool.map(capture,queries.items()))
log=subprocess.run(['gh','run','view',str(RUN),'-R',REPO,'--log'],capture_output=True)
assert log.returncode==0,log.stderr.decode(errors='replace')
(E/'CODEQL_FULL_LOG.txt').write_bytes(log.stdout)
lines=log.stdout.decode('utf-8-sig').splitlines()
markers=['##[error]','##[warning]','Download action repository','SecurityEvents:','Contents:','Exported results to SARIF','CodeQL scanned','Error:','Error running']
extract=[dict(line=i,text=s) for i,s in enumerate(lines,1) if any(m in s for m in markers)]
(E/'CODEQL_LOG_EXTRACT.json').write_text(json.dumps(extract,ensure_ascii=False,indent=2),encoding='utf8')
(E/'API_CAPTURE_RECEIPT.json').write_text(json.dumps(dict(requests=status,log_bytes=len(log.stdout),log_sha256=hashlib.sha256(log.stdout).hexdigest()),indent=2))
print(json.dumps(dict(requests=len(status),nonzero_api=[x for x in status if x['exit_code']],log_lines=len(lines),errors=[x for x in extract if '##[error]' in x['text']]),ensure_ascii=False))
