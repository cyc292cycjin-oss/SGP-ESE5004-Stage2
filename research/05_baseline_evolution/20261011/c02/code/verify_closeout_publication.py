"""Check delivery identities and scope; does not rerun build or unit tests."""
from pathlib import Path
import json, hashlib, ast, subprocess
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c02_daily_build_20261012')
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
D=R/'research/05_baseline_evolution/20261011/c02'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(W/'upload_stage/PAYLOAD_MANIFEST.json');tests=read(D/'evidence/LOCAL_NO_SOLVE_TESTS.json')
checks=[]
for name,h in tests['code_sha256'].items():
    assert sha(D/'code'/name)==h==manifest['files'][name]['sha256']
checks.append('six_executed_C02_sources_equal_deployed_and_tested_SHA')
for sub in ['helpers','source']:
    for p in (D/'code'/sub).glob('*.py'):
        assert sha(p)==manifest['files'][sub+'/'+p.name]['sha256']
checks.append('pinned_helpers_and_archival_source_SHA_preserved')
for p in D.rglob('*'):
    if p.is_file():
        assert p.stat().st_size<2_000_000,(p,p.stat().st_size)
        assert p.suffix in {'.md','.py','.json','.jsonl','.log'},p
        if p.suffix=='.json':read(p)
        if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'))
checks.extend(['no_large_binary_or_credential_payload_files','JSON_and_python_syntax_valid'])
b=read(D/'evidence/original_run/BUILD_RESULT.json');assert b['status']=='C02_BLOCKED_WITH_SPECIFIC_EVIDENCE' and b['solver_calls']==0
assert read(D/'DAILY_V4_BINDING_STATUS.json')['usable_for_C03'] is False
c=read(D/'C02_CONSTRAINT_COVERAGE.json');assert c['total_active_variables']==2450005 and c['total_active_rows']==6042238 and c['nnz'] is None
assert len(c['families'])==36 and c['families']['ResearchStoreDirection']['active_rows']==807*365
assert c['families']['ResearchBatteryNominal']['active_rows']==196
checks.extend(['blocked_status_and_no_C03_authorization_consistent','actual_labels_counted_without_fabricated_NNZ_or_rhs','807_direction_and_196_battery_label_evidence'])
z=read(D/'evidence/C02_SIGNED_ZERO_FORENSICS.json');assert z['numeric_exact_equal'] and not z['bits_equal'] and not z['full_model_rebuilt']
assert all(not p['exists'] for p in read(D/'evidence/C02_RESOURCE_AND_EXIT_SUMMARY.json')['processes_after_exit'])
checks.extend(['signed_zero_expression_evidence_separated_from_missing_runtime_rhs','three_run_processes_absent_at_read_only_observation'])
assert read(D/'evidence/C02_LOCAL_SYNC_AND_PARTIAL_ARTIFACTS.json')['zip_crc']=='PASS'
checks.append('downloaded_original_light_archive_CRC_and_SHA_pass_reused')
write={'status':'PASS_CLOSEOUT_IDENTITY_AND_HONEST_REPORTING_CHECKS','checks':checks,'count':len(checks),
 'build_repeated':False,'solver_calls':0,'input_files_changed':False,
 'scope':'Delivery validation only. Actual C02 remains BLOCKED.'}
(D/'evidence/C02_CLOSEOUT_VALIDATION.json').write_text(json.dumps(write,indent=2)+'\n')
print(json.dumps(write))
