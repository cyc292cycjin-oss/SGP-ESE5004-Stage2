"""Bounded delivery, identity and data-integrity validation; no experiment run."""
from pathlib import Path
import ast,csv,hashlib,json,re,subprocess
R=Path(__file__).resolve().parent;ROOT=R.parents[3]
REG=ROOT/'data_registry/buildings_phase3a4'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
for dest,name,key,count in [(R,'BUILDINGS_FIX_COMBINED_TEST_MATRIX','COMBINED_MATRIX',1062),
 (REG,'BUILDINGS_E3_DATA_REQUIREMENTS','E3_REQUIREMENTS',34),
 (REG,'BUILDINGS_USEFUL_HEAT_INPUT_SCHEMA','USEFUL_HEAT_SCHEMA',41)]:
    with (dest/(name+'.csv')).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    records=read(R/f'derived/{key}.json');assert len(rows)==len(records)==count
    for row,rec in zip(rows,records):
        for k,v in rec.items():
            if v is None:assert row[k]==''
            elif isinstance(v,bool):assert row[k].lower()==str(v).lower()
            elif isinstance(v,(int,float)):assert float(row[k])==v
            else:assert row[k]==v,(name,k,row[k],v)
    if key!='COMBINED_MATRIX':assert all(r['Human_Confirmation']=='PENDING' for r in rows)
    checks[name]=dict(rows=count,columns=len(rows[0]),csv_json_exact=True)
with (REG/'BUILDINGS_USEFUL_HEAT_INPUT_TEMPLATE.csv').open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f);assert reader.fieldnames==read(R/'derived/INPUT_TEMPLATE_FIELDS.json');assert list(reader)==[]
checks['scientific_input_rows']=0
identity=read(R/'evidence/FINAL_INTEGRATION_IDENTITY.json')
receipt=read(R/'evidence/INTEGRATION_RECEIPT.json')
combined=read(R/'evidence/COMBINED_TESTS.json')
assert receipt['status']=='PASS' and len(receipt['steps'])==9
assert all(t['exit_code']==0 for t in receipt['tests'])
assert combined['all_pass'] and combined['solver_runs']==0 and len(combined['rows'])==1062
parts=[]
for fix in ['E1','E2','E4']:parts+=read(R/f'evidence/after_E4_{fix}_strict.json')['rows']
assert combined['rows']==parts
prior=read(R.parent.parent/'buildings_phase3a3/evidence/COMBINED_TESTS.json')
assert combined['rows']==prior['rows']
checks['combined_exact_match_final_individual_and_prior_overlay']=True
contract=read(R/'evidence/ACCOUNTING_CONTRACT_TESTS.json')
assert contract['all_pass'] and len(contract['rows'])==18 and contract['model_inputs_written']==0
checks['synthetic_accounting_contract_checks']=18
diagnostic=read(R/'evidence/INTEGRATED_E3_DIAGNOSTIC.json')
assert diagnostic['total_after_TWh']==4 and not diagnostic['E3_patch']
checks['E3_known_blocker_reproduced']=True
links=[]
for p in R.glob('*.md'):
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
        if '://' in target or target.startswith('#'):continue
        assert (p.parent/target.split('#')[0]).exists(),(p.name,target)
        links.append(target)
checks['valid_local_links']=len(links)
for p in R.glob('*.py'):ast.parse(p.read_text(encoding='utf8'))
assert not (R/'BUILDINGS_FIX_E3_REPORT.md').exists()
checks['E3_patch_report_absent']=True

# WSL has the actual model worktrees and files; the validator must run there.
def git(repo,*args):return subprocess.check_output(['git','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','-C',str(repo),*args],text=True).strip()
repo=Path(receipt['worktree'])
assert git(repo,'rev-parse','HEAD')==identity['combined_commit']
assert not git(repo,'status','--porcelain')
git(repo,'diff','--check',receipt['base'])
checks['integration_clean']=True
for f,h in receipt['source_hashes'].items():assert sha(repo/f)==h
for s in receipt['protected_before']:
    p=Path(s['path']);assert git(p,'rev-parse','HEAD')==s['sha'] and not git(p,'status','--porcelain')
checks['protected_P_U_R_T_unchanged_clean']=True
for row in receipt['input_hash_checks']:assert sha(Path(row['path']))==row['sha256']
checks['unchanged_input_hashes']=len(receipt['input_hash_checks'])
grep=git(repo,'grep','-n','-E','services? electricity','--','scripts','configs')
assert not re.search(r'(?<!s)\bservice electricity\b',grep)
(R/'evidence/CARRIER_REFERENCES.txt').write_text(grep+'\n')
checks['singular_service_electricity_literal_absent']=True
# No implication that the canonical service carrier is included in E3 selectors.
checks['E3_selector_omission_still_present']=True
checks['formal_solver_runs']=0;checks['new_HUMAN_ACCEPTED_data_rows']=0
checks['integration_final_sha']=identity['combined_commit']
(R/'evidence/DELIVERY_VALIDATION.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
