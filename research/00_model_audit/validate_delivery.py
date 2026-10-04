"""Validate delivery, not the scientific model. No workflow imports or solves."""
from pathlib import Path
import csv,json,hashlib,math
root=Path(__file__).resolve().parent
required=['MODEL_INPUT_MAP.md','SECTOR_COUPLING_MAP.md','MODIFICATION_MAP.md','CARBON_IMPLEMENTATION_NOTE.md','DATA_LEDGER.csv','REPO_STRUCTURE_PROPOSAL.md','REPRODUCIBILITY_RULES.md','USER_INPUT_NEEDED.md']
assert all((root/p).is_file() for p in required)
with (root/'DATA_LEDGER.csv').open(encoding='utf-8-sig',newline='') as f:
    matrix=list(csv.reader(f))
assert len(matrix[0])==28 and all(len(r)==28 for r in matrix)
records=[dict(zip(matrix[0],r)) for r in matrix[1:]]
assert len({r['Parameter_ID'] for r in records})==len(records)
assert all(r['Status'] in ('PENDING','UNVERIFIED') and r['Final_Value']=='' and r['Verified_By']=='' for r in records)
# Check CSV round trip against the deterministic extraction records.
source=json.loads((root/'ledger_records.json').read_text(encoding='utf-8'))
for actual,wanted in zip(records,source['rows']):
    for field in source['fields']:
        assert actual[field]==str(wanted[field]),(actual['Parameter_ID'],field,actual[field],wanted[field])
assert len(records)==len(source['rows'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checked={}
for f,key in [('AUDIT_RUNTIME_EVIDENCE.json','inputs'),('INPUT_INVENTORY.json','files')]:
    d=json.loads((root/f).read_text(encoding='utf-8'))
    for r in d[key]:
        if 'file' not in r:continue
        p=root/'input_snapshot'/r['file']
        if p.exists() and r.get('sha256'):
            assert sha(p)==r['sha256'],str(p)
            checked[r['file']]=r['sha256']
old=json.loads((root/'AUDIT_RUNTIME_EVIDENCE.json').read_text(encoding='utf-8'))
assert old['status_before']==old['status_after']==''
assert len(old['networks'])==3
for n in old['networks']:
    assert not any(r.get('GlobalConstraint')=='CO2Limit' for r in n['constraints'])
    industry=[r for r in n['components']['loads'] if r['carrier']=='industry electricity']
    assert len(industry)==1 and industry[0]['weighted_demand_MWh']==0
result={'delivery_files':required,'record_count':len(records),'column_count':28,'unique_ids':True,'csv_round_trip_matches':True,'statuses':{s:sum(r['Status']==s for r in records) for s in ['UNVERIFIED','PENDING']},'no_final_value_or_human_confirmation':True,'input_snapshot_hashes_matched':len(checked),'model_worktree_unchanged_at_extraction':True,'all_three_saved_networks_no_CO2Limit':True,'industrial_load_zero_in_all_three':True,'scientific_inputs_approved':False,'formal_experiments_started':False}
(root/'DELIVERY_VALIDATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(result,ensure_ascii=True))
