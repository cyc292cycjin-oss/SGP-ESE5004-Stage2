"""Validate handoff integrity, strict results and frozen inputs. Never solve."""
from pathlib import Path
import ast,csv,hashlib,json,re,subprocess
R=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(p,*args):return subprocess.check_output(['git','-C',str(p),*args],text=True).strip()
checks={}
for name,key,count in [('BUILDINGS_FIX_TEST_MATRIX','FIX_TEST_MATRIX',1062),('ASEAN_BUILDINGS_DATA_CANDIDATES','DATA_CANDIDATES',8),('BUILDINGS_DATA_REGISTRY_UPDATED','DATA_REGISTRY_UPDATED',50)]:
    with (R/(name+'.csv')).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    records=read(R/f'data/derived/buildings/{key}.json')
    assert len(rows)==len(records)==count
    for row,rec in zip(rows,records):
        for k,v in rec.items():
            if v is None:assert row[k]==''
            elif isinstance(v,bool):assert row[k].lower()==str(v).lower()
            elif isinstance(v,(int,float)):assert float(row[k])==v,(name,k,row[k],v)
            else:assert row[k]==v,(name,k)
    if key!='FIX_TEST_MATRIX':assert all(r['status']=='UNVERIFIED' and r['human_confirmation']=='PENDING' for r in rows)
    checks[name]=dict(rows=count,columns=len(rows[0]),csv_json_exact_match=True)
combined=read(R/'evidence/COMBINED_TESTS.json')
parts=[]
for fix in ['E1','E2','E4']:
    before=read(R/f'evidence/{fix}_before.json');after=read(R/f'evidence/{fix}_after.json')
    assert not before['all_pass'] and after['all_pass']
    assert before['solver_runs']==after['solver_runs']==0
    parts+=after['rows']
assert combined['all_pass'] and combined['rows']==parts
checks['combined_rows_exactly_match_individual']=len(parts)
manifest=read(R/'data/raw/buildings/RETRIEVAL_MANIFEST.json')
for r in manifest:
    if r['access']=='RETRIEVED':assert sha(R/r['filename'])==r['sha256']
    else:assert not r['sha256'] and not (R/r['filename']).exists()
checks['new_source_files_hashed']=sum(r['access']=='RETRIEVED' for r in manifest)
loc=read(R/'evidence/SOURCE_LOCATION_CHECKS.json')
assert all(all(x['terms_found'].values()) for x in loc['locations'])
checks['source_locations_checked']=len(loc['locations'])
links=[]
for p in list(R.glob('*.md'))+list((R/'evidence').glob('*.md'))+[R/'data/README.md']:
    for t in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
        if '://' in t or t.startswith('#'):continue
        assert (p.parent/t.split('#')[0]).exists(),(p.name,t)
        links.append(t)
checks['local_links_valid']=len(links)
for p in R.glob('*.py'):ast.parse(p.read_text(encoding='utf8'))
checks['python_parse']='PASS'
handoff=read(R/'evidence/HANDOFF_VERIFICATION.json')
assert all(handoff[x] for x in ['receipt_match','canonical_match','desktop_readme_byte_match','all_payload_hashes_match'])
checks['prior_desktop_package_match']=True

home=Path('/home/jin/research/SGP_ESE5004_Stage2')
U='a3616a68ee44592af6527ca9024a90f1956646ae'
models={'tutorial':(home/'pypsa-asean','ce327bfae2abe5526d4c1976173f0f8d08366ba5'),
 'paper':(home/'phase2/paper_reference','5bacad702ccfed17ad19ab510fa710651e966f2c'),
 'upstream':(home/'phase2/upstream_sc_baseline',U),'research_model':(home/'phase2/research_model',U)}
checks['unchanged_models']={}
for name,(repo,expected) in models.items():
    assert git(repo,'rev-parse','HEAD')==expected and not git(repo,'status','--porcelain')
    checks['unchanged_models'][name]=dict(sha=expected,clean=True)
for rec in read(R/'evidence/FIX_COMMITS.json'):
    repo=Path(rec['worktree']);assert git(repo,'rev-parse','HEAD')==rec['branch_head'] and not git(repo,'status','--porcelain')
    assert git(repo,'rev-parse',rec['source_commit']+'^')==U
    assert not git(repo,'diff',rec['source_commit'],rec['branch_head'],'--','scripts','configs','data')
checks['fix_branches_clean_and_independent']=True
raw=read(R.parent/'buildings_heat/evidence/LOCAL_INPUT_HASHES.json')
for rec in raw:assert sha(Path(rec['path']))==rec['sha256']
checks['previous_model_input_hashes_unchanged']=len(raw)
checks.update(solver_runs=0,accepted_new_data_rows=0,research_model_merged=False)
(R/'evidence/DELIVERY_VALIDATION.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
print(json.dumps(checks,indent=2))
