"""C09 read-only comparison with C06/C07A/C07B. No solver, no model build, no change to any result.

Run in WSL (pypsa-earth env). Account/group metrics follow c07 compare_c07.py definitions:
stocks/flows read from the C09 original-unit X, budgets and pass flags from the unchanged V4 receipts.
"""
from pathlib import Path
import json, math
import numpy as np

W = Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c09_exact_decomposition_20261013')
W6 = W.parent / 'c06_barconvtol_20261012'; W7 = W.parent / 'c07_v4_reliability_20261013'; ROOT = W.parents[1] / 'outputs'
B = ROOT / 'c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
load = lambda p: np.load(p, mmap_mode='r', allow_pickle=False)
rid = read(W / 'LAUNCH_RECEIPT.json')['run_id']; P = ROOT / 'c09_daily_diagnostic' / rid / 'cloud_run'

LAB = read(B / 'artifacts/mapping/LABELS.json'); vl = load(B / 'bridge/mapping/vlabels.npy')
VM = {b['name']: b for b in LAB['variables']}


def cols(name, asset):
    b = VM[name]; la = load(B / 'artifacts/mapping' / b['labels_file']); dim = next(d for d in b['dims'] if d != 'snapshot')
    labs = np.take(la, b['coordinates'][dim].index(asset), axis=b['dims'].index(dim)).ravel()
    ix = np.searchsorted(vl, labs); assert np.array_equal(vl[ix], labs); return ix


raw = read(P / 'raw/vectors/RAW_RECEIPT.json'); post = read(P / 'postprocess/POSTPROCESS_RECEIPT.json')
kkt = read(P / 'postprocess/KKT.json'); phys = read(P / 'postprocess/PHYSICAL_CHECKS.json'); X = load(P / 'postprocess/original_vectors/X_original.npy')
oldac = read(W6 / 'C06_ALL_ACCOUNT_AND_GROUP_COMPARISON.json')
pa = {r['asset']: r for r in phys['details']['fixed_prefix_checks']}; ga = {r['buses'][0]: r for r in phys['details']['fixed_group_obligations_v4']}
assert len(pa) == 807 and len(ga) == 385
accounts = []
for old in oldac['accounts']:
    a = old['asset']; r = pa[a]; e = X[cols('Store-e', a)]; flow = X[cols('Store-p', a)]
    annual = math.fsum(float(x) * 24 for x in flow); assert annual == r['annual_release_mwh']; q = old['Q_MWh']; budget = r['energy_budget_mwh']
    errors = dict(annual_abs_MWh=abs(annual - q), stock_lower_MWh=max(0, -float(e.min())), terminal_abs_MWh=abs(float(e[-1])),
                  prefix_max_MWh=r['max_prefix_error_mwh'], state_L1_MWh=r['gross_state_error_mwh'], meter_L1_MWh=r['meter_difference_l1_mwh'])
    accounts.append(dict(asset=a, passed=r['passed'], annual_signed_error_MWh=annual - q, error_over_budget={n: x / budget for n, x in errors.items()}))
groups = [dict(ga[old['bus']], account_count=old['account_count'], accounts=old['accounts']) for old in oldac['groups']]
acmap = {r['asset']: r for r in accounts}; card = []
for n in (1, 2, 3, 4):
    gg = [r for r in groups if r['account_count'] == n]; aa = [acmap[a] for r in gg for a in r['accounts']]
    card.append(dict(account_count=n, groups=len(gg), accounts=len(aa), failed_groups=sum(not r['passed'] for r in gg), failed_accounts=sum(not r['passed'] for r in aa)))
res_lines = [json.loads(s) for s in (P / 'RESOURCE.jsonl').read_text().splitlines() if s.strip()]
auth = read(P / 'AUTHORIZATION.json'); arch = read(sorted((W / 'monitor_snapshots').glob('*.json'))[-1])['_ARCHIVE_RECEIPT.json']
phys_fail = [c['Check'] for c in phys['checks'] if c['Status'] != 'PASS']
c09 = dict(
    run_id=rid, native_status=raw['native_status'], info=raw['native_info'], gates=post['gates'], postprocess_status=post['status'], KKT=kkt,
    costs=read(P / 'postprocess/DUAL_COST_LEDGER.json'), netcdf=read(P / 'postprocess/NETCDF_READBACK.json'),
    physical_checks=dict(count=len(phys['checks']), failed=phys_fail, all_physics_pass=phys['all_physics_pass']),
    resource_totals=dict(failed_accounts=sum(not r['passed'] for r in accounts), failed_groups=sum(not r['passed'] for r in groups),
                         positive_annual_overuse_MWh=math.fsum(max(0, r['annual_signed_error_MWh']) for r in accounts),
                         negative_annual_shortfall_MWh=math.fsum(max(0, -r['annual_signed_error_MWh']) for r in accounts),
                         group_gross_over_MWh=math.fsum(r['gross_oversupply_mwh'] for r in groups),
                         group_gross_under_MWh=math.fsum(r['gross_undersupply_mwh'] for r in groups),
                         max_account_error_budget_ratio=max(v for r in accounts for v in r['error_over_budget'].values()), cardinality=card),
    resources=dict(sampled_process_RSS_max=max(r['rss_bytes'] for r in res_lines), cgroup_current_max=max(c['current'] for r in res_lines for c in r['cgroup']),
                   cgroup_headroom_min=min(r['cgroup_headroom_bytes'] for r in res_lines), disk_free_min=min(r['disk_free_bytes'] for r in res_lines),
                   protection_reasons=[r['reason'] for r in res_lines if r.get('reason')], resource_samples=len(res_lines),
                   start_to_archive_seconds=arch['completed_epoch'] - auth['started_epoch'], cgroup_peak_scope='shared cgroup lifetime; not run-exclusive'),
)
c7 = read(W7 / 'C07_C06_A_B_COMPARISON.json')
out = dict(qualification='READ_ONLY_COMPARISON', C09=c09, C07_reference_file='work/c07_v4_reliability_20261013/C07_C06_A_B_COMPARISON.json',
           C07_keys=sorted(c7.keys()))
(W / 'C09_COMPARISON.json').write_text(json.dumps(out, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in c09.items() if k not in ('KKT',)}, indent=1, ensure_ascii=False)[:6000]); print(sorted(c7.keys()))
