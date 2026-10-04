"""Read bounded logs and annotations of existing runs, never rerun them."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,re
R=Path(__file__).resolve().parent;E=R/'evidence';REPO='cyc292cycjin-oss/SGP-ESE5004-Stage2'
jobs={
 'LOCKED_ENVS':110278333922,'PAGES':108604178669,
 'TEST_PUSH_UBUNTU':108604179016,'TEST_PR_UBUNTU':108604717318,
 'TEST_PUSH_MACOS':108604178968,'TEST_PUSH_WINDOWS':108604179005,'TEST_PR_MACOS':108604717299,
}
def collect(pair):
    name,job=pair
    result=subprocess.run(['gh','api',f'repos/{REPO}/check-runs/{job}/annotations?per_page=100'],capture_output=True)
    (E/(name+'_ANNOTATIONS.json')).write_bytes(result.stdout)
    p=subprocess.run(['gh','run','view','-R',REPO,'--job',str(job),'--log'],capture_output=True)
    assert p.returncode==0,p.stderr.decode(errors='replace')
    (E/(name+'_LOG.txt')).write_bytes(p.stdout)
    lines=p.stdout.decode('utf-8-sig').splitlines()
    matches=[i for i,s in enumerate(lines) if re.search(r'##\[error\]|Error:|Error in rule|Traceback|Exception:|PackagesNotFoundError|UnsatisfiableError|AssertionError',s)]
    selected=sorted({i for match in matches for i in range(max(0,match-3),min(len(lines),match+10))})
    excerpts=[dict(line=i+1,text=lines[i]) for i in selected]
    (E/(name+'_ERROR_EXTRACT.json')).write_text(json.dumps(excerpts,ensure_ascii=False,indent=2),encoding='utf8')
    return dict(name=name,job=job,log_lines=len(lines),error_markers=len(matches))
with ThreadPoolExecutor(max_workers=3) as pool:result=list(pool.map(collect,jobs.items()))
# Cross-branch CodeQL evidence: capture each previous run's failed-job log.
for name,run in [('CODEQL_INITIAL_MAIN',36313652192),('CODEQL_PR',36313847572)]:
    p=subprocess.run(['gh','run','view',str(run),'-R',REPO,'--log-failed'],capture_output=True);assert p.returncode==0
    (E/(name+'_LOG.txt')).write_bytes(p.stdout)
    lines=p.stdout.decode('utf-8-sig').splitlines()
    excerpts=[dict(line=i,text=s) for i,s in enumerate(lines,1) if any(k in s for k in ['##[error]','##[warning]','Exported results to SARIF','CodeQL scanned','Download action repository'])]
    (E/(name+'_ERROR_EXTRACT.json')).write_text(json.dumps(excerpts,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result))
