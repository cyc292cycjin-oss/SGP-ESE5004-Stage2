"""Summarize sealed JSON receipts only. No model, vector, or solver computation."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import json, hashlib, math

W = Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c02r_c03_combined_20261012')
E = W / 'cloud_light'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

source_manifest = read(E / 'LIGHT_SOURCE_MANIFEST.json')
for f in source_manifest['files']:
    p = E / f['relative']
    assert p.stat().st_size == f['bytes'] and sha(p) == f['sha256']
seal = read(E / 'CLOUD_SEAL_COMPLETE.json')
assert sha(E / 'BACKUP_INDEX.json') == seal['index_sha256']
index = {x['relative']: x for x in read(E / 'BACKUP_INDEX.json')['files']}
for f in source_manifest['files']:
    if f['relative'] in index:
        assert f['sha256'] == index[f['relative']]['sha256']

p = read(E / 'postprocess/PHYSICAL_CHECKS.json')
after = read(E / 'postprocess/PHYSICAL_CHECKS_AFTER_READBACK.json')
assert [(x['Check'], x['Status']) for x in p['checks']] == [(x['Check'], x['Status']) for x in after['checks']]
assert p['all_physics_pass'] == after['all_physics_pass']
assert p['details']['fixed_prefix_checks'] == after['details']['fixed_prefix_checks']
assert p['details']['fixed_group_obligations_v4'] == after['details']['fixed_group_obligations_v4']
reduction_diffs = [{'check': x['Check'], 'before': x['MaxAbsoluteResidual'],
                    'after': y['MaxAbsoluteResidual'],
                    'delta': y['MaxAbsoluteResidual'] - x['MaxAbsoluteResidual'], 'unit': x['Unit']}
                   for x, y in zip(p['checks'], after['checks'])
                   if 'MaxAbsoluteResidual' in x and x['MaxAbsoluteResidual'] != y['MaxAbsoluteResidual']]
d = p['details']
accounts = d['fixed_prefix_checks']
groups = d['fixed_group_obligations_v4']
q = {x['FixedAccountID']: x['QuantityMWh'] for x in d['accounting_report']['PendingFixedCostTerms']}
assert len(q) == len(accounts) == 807 and len(groups) == 385
account_rows = []
for x in accounts:
    excess = x['annual_release_mwh'] - q[x['asset']]
    account_rows.append({'asset': x['asset'], 'Q_mwh': q[x['asset']],
                         'annual_release_mwh': x['annual_release_mwh'],
                         'annual_excess_mwh': excess, 'budget_mwh': x['energy_budget_mwh'],
                         'passed': x['passed'], 'checks': x['draft_checks']})
native = read(E / 'raw/vectors/RAW_RECEIPT.json')
post = read(E / 'postprocess/POSTPROCESS_RECEIPT.json')
current = read(E / 'EFFECTIVE_MODEL_PARAMETERS.json')
parent = read(W / 'release/FIRST_RUN_EFFECTIVE_MODEL_PARAMETERS.json')
parameter_diff = {k: {'first_gate6': parent.get(k), 'daily': current.get(k)}
                  for k in sorted(set(parent) | set(current)) if current.get(k) != parent.get(k)}
assert set(parameter_diff) <= {'TimeLimit', 'TSPort'}
snap = read(sorted(W.glob('SNAPSHOT_*.json'))[-1])
assert all(not x['alive'] for x in snap['processes'].values())
scheme = read(E / 'artifacts/SCHEME_A_DAILY_EXACT_GROUPS.json')
assert len(scheme['groups']) == 385
assert all(Fraction(x['D']) <= Fraction(x['Q']) for x in scheme['groups'])

result = {
    'run_id': native['run_id'], 'status': post['status'],
    'method': 'JSON receipt aggregation; no new physical recomputation, optimization or model build',
    'source_manifest_sha256': sha(E / 'LIGHT_SOURCE_MANIFEST.json'),
    'source_seal_sha256': sha(E / 'CLOUD_SEAL_COMPLETE.json'),
    'native': native['native_info'], 'native_status': native['native_status'],
    'native_return_code': native['GRBoptimize_return_code'],
    'optimization_calls': read(E / 'NATIVE_CALL_EXIT.json')['optimization_calls'],
    'gates': post['gates'], 'KKT': read(E / 'postprocess/KKT.json'),
    'engineering': {
        'check_count': len(p['checks']), 'status_counts': dict(Counter(x['Status'] for x in p['checks'])),
        'non_account_failures': [x for x in p['checks'] if x['Status'] == 'FAIL' and not x['Check'].startswith('FIXED_RESOURCE_USAGE:')],
        'statuses_identical_after_NetCDF_readback': True,
        'fixed_V4_account_and_group_receipts_identical_after_readback': True,
        'derived_float_reductions_identical': False,
        'derived_float_reduction_difference_count': len(reduction_diffs),
        'max_derived_residual_differences_by_unit': {u: max((x for x in reduction_diffs if x['unit'] == u), key=lambda x: abs(x['delta'])) for u in sorted(set(x['unit'] for x in reduction_diffs))},
    },
    'fixed_accounts': {
        'total': 807, 'failed': sum(not x['passed'] for x in accounts),
        'subcheck_failures': dict(Counter(k for x in accounts for k, v in x['draft_checks'].items() if not v)),
        'gross_annual_excess_mwh': math.fsum(max(x['annual_excess_mwh'], 0.) for x in account_rows),
        'gross_annual_excess_over_budget_mwh': math.fsum(max(x['annual_excess_mwh'] - x['budget_mwh'], 0.) for x in account_rows),
        'max_annual_excess': max(account_rows, key=lambda x: x['annual_excess_mwh']),
        'note': 'Derived from stored annual release and approved Q; binary64 reporting arithmetic, not exact-rational feasibility proof',
    },
    'obligation_groups': {
        'total': 385, 'failed': sum(not x['passed'] for x in groups),
        'subcheck_failures': dict(Counter(k for x in groups for k, v in x['checks'].items() if not v)),
        'gross_oversupply_mwh': math.fsum(x['gross_oversupply_mwh'] for x in groups),
        'gross_undersupply_mwh': math.fsum(x['gross_undersupply_mwh'] for x in groups),
        'max_oversupply': max(groups, key=lambda x: x['gross_oversupply_mwh']),
    },
    'scheme_A_source': {'all_385_exact_D_le_Q': True, 'candidate_feasible': False},
    'costs': post['costs'], 'parameters_count': len(current), 'parameter_differences': parameter_diff,
    'resources': snap['sampled_resources'], 'processes_exited': True,
    'original_scientific_objective_optimality': 'NOT_PROVEN', 'Gate6_2920_PASS': False,
    'causality': 'NOT_ESTABLISHED; this receipt summary does not isolate root causes or prove LP infeasibility',
}
(W / 'DAILY_RESULT_SUMMARY.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['status', 'fixed_accounts', 'obligation_groups', 'parameters_count', 'parameter_differences']}, ensure_ascii=False, indent=2))
