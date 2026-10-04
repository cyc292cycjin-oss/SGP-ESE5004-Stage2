"""Deterministic summaries of captured evidence; does not execute model code."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,subprocess
R=Path(__file__).resolve().parent;ROOT=R.parents[2];E=R/'evidence'
load=lambda n:json.loads((E/(n+'.json')).read_text(encoding='utf8'))
git=load('REPOSITORY_GIT_AUDIT');tree=load('MAIN_TREE')['response']['tree']
log=(E/'CODEQL_FULL_LOG.txt').read_text(encoding='utf-8-sig')
prefix='/home/runner/work/SGP-ESE5004-Stage2/SGP-ESE5004-Stage2/'
extracted=set(re.findall(r'Extracted file '+re.escape(prefix)+r'(\S+\.py) in ',log))
py={x['path'] for x in tree if x['path'].endswith('.py')}
not_logged=sorted(py-extracted)
summary=dict(tracked_python_files=len(py),python_files_with_extraction_log=len(extracted),tracked_python_without_extracted_file_message=not_logged,analyzer_summary='77 out of 77 Python; 9 out of 9 GitHub Actions',notebook_count=len(git['notebooks']),notebook_coverage_claimed=False,annotations_by_level=dict(Counter(x['annotation_level'] for x in load('CODEQL_ANNOTATIONS')['response'])),repository_owner_type=load('REPOSITORY')['response']['owner']['type'],repository_private=load('REPOSITORY')['response']['private'])
copied=[]
for name in ['research/01_baseline_construction/prepare_model_layers.py','research/01_baseline_construction/BASELINE_ARCHITECTURE.md','research/02_sector_coupling/phase3c/evidence/MODEL_IDENTITY_AFTER.json','research/01_baseline_construction/FIX_COMMITS.json','research/02_sector_coupling/phase3c/PHASE3_RESEARCH_MODEL_DESIGN_CLOSEOUT.md']:
    p=ROOT/name;b=p.read_bytes();out=E/'prior'/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(b)
    copied.append(dict(path=name,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))
(E/'PRIOR_DEPENDENCIES.json').write_text(json.dumps(copied,indent=2))
def run(*args):
    p=subprocess.run(['git','-C',str(ROOT),*args],capture_output=True)
    return dict(args=list(args),exit_code=p.returncode,stdout=p.stdout.decode('utf8',errors='replace').strip(),stderr=p.stderr.decode('utf8',errors='replace').strip())
local={name:run(*args) for name,args in {'head':['rev-parse','HEAD'],'branch':['branch','--show-current'],'remotes':['remote','-v'],'status':['status','--porcelain'],'refs':['show-ref'],'research_diff':['diff','HEAD','--','research'],'unmerged':['ls-files','-u']}.items()}
assert local['head']['stdout']=='f5853f0c666a48782d202919c9e96a61619b8ca1'
assert local['research_diff']['stdout']=='' and local['unmerged']['stdout']==''
(E/'NATIVE_GIT_BEFORE.json').write_text(json.dumps(local,ensure_ascii=False,indent=2),encoding='utf8')
summary['prior_dependencies']=len(copied)
(E/'EVIDENCE_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summary,ensure_ascii=False))
