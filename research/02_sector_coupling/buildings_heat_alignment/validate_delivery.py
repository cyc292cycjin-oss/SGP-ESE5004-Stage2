"""Validate tables, references, hashes and unchanged model worktrees; no experiments."""
from pathlib import Path
import ast,csv,hashlib,json,re,subprocess
R=Path(__file__).resolve().parent;P=R.parent/'buildings_heat';ev=R/'evidence'
def read(p):return json.loads(p.read_text())
checks={}
for out,inp,key,count in [('BUILDINGS_DEMAND_ACCOUNTING','ACCOUNTING_RECORDS','row_id',99),('BUILDINGS_DATA_REGISTRY','REGISTRY_RECORDS','source_id',42)]:
    with (R/(out+'.csv')).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    records=read(R/f'data/derived/buildings/{inp}.json')
    assert len(rows)==count==len(records);assert len({r[key] for r in rows})==count
    assert all(r['status']=='UNVERIFIED' and r['human_confirmation']=='PENDING' for r in rows)
    for row,rec in zip(rows,records):
        for k,v in rec.items():
            if isinstance(v,(float,int)):
                assert abs(float(row[k])-v)<=1e-10*max(1,abs(v))
            else:assert row[k]==('' if v is None else str(v)),(out,k)
    checks[out]={'rows':len(rows),'columns':len(rows[0]),'matches_author_records':True,'all_human_pending':True}
for record in read(R/'data/raw/buildings/RETRIEVAL_MANIFEST.json'):
    assert record['access']=='RETRIEVED'
    assert hashlib.sha256((R/record['filename']).read_bytes()).hexdigest()==record['sha256']
checks['candidate_hashes']=7
links=[]
for p in R.glob('*.md'):
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if '://' in target or target.startswith('#'):continue
        assert (p.parent/target.split('#')[0]).exists(),(p.name,target)
        links.append(target)
checks['relative_document_links']=len(links)
for p in R.glob('*.py'):ast.parse(p.read_text())
checks['python_parse']='PASS'
for fix in ['E1','E2','E4']:
    before=read(ev/f'{fix}_before.json');after=read(ev/f'{fix}_after.json')
    assert before['all_pass'] is False and after['all_pass'] is True
    assert not before['optimizer_called'] and not after['optimizer_called']
checks['candidate_before_fail_after_pass']=['E1','E2','E4']
checks['accounting']=read(R/'data/derived/buildings/ACCOUNTING_CHECKS.json')
# This section runs in WSL, where the actual retained Git models and raw inputs live.
home=Path('/home/jin/research/SGP_ESE5004_Stage2')
sha_u='a3616a68ee44592af6527ca9024a90f1956646ae'
models={'tutorial':(home/'pypsa-asean','ce327bfae2abe5526d4c1976173f0f8d08366ba5'),'paper':(home/'phase2/paper_reference','5bacad702ccfed17ad19ab510fa710651e966f2c'),'upstream':(home/'phase2/upstream_sc_baseline',sha_u),'research_model':(home/'phase2/research_model',sha_u)}
checks['unchanged_models']={}
def git(path,*args):return subprocess.check_output(['git','-C',str(path),*args],text=True).strip()
for name,(path,expected) in models.items():
    sha=git(path,'rev-parse','HEAD');status=git(path,'status','--porcelain');assert sha==expected and not status,(name,sha,status)
    checks['unchanged_models'][name]={'sha':sha,'clean':True}
for record in read(ev/'CANDIDATE_COMMITS.json'):
    path=Path(record['worktree']);assert git(path,'rev-parse','HEAD')==record['commit'] and not git(path,'status','--porcelain')
    assert git(path,'rev-parse','HEAD^')==sha_u
checks['candidate_branches_clean_and_independent']=True
hash_count=0
for r in read(P/'evidence/LOCAL_INPUT_HASHES.json'):
    path=Path(r['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==r['sha256'];hash_count+=1
checks['retained_input_hashes_unchanged']=hash_count
checks['solver_runs']=0;checks['accepted_data_rows']=0
(ev/'DELIVERY_VALIDATION.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
