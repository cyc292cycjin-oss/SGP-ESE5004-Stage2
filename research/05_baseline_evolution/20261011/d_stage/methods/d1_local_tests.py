"""D-1 local interface tests (WSL, same package versions as 122). No solver, no cloud.

The real frozen 2920 network is used for every network-level gate. The Linopy build/export/bridge/gates path is
exercised on a truncated horizon (T=16) because this machine has 10 GB RAM; the cloud build runs the same code at T=2920.
Usage: python d1_local_tests.py <release_d1 dir> <frozen 2920 network> <repo dir> <output json>
"""
import sys, json, time, shutil, tempfile, threading, subprocess, hashlib, copy, traceback, logging
from pathlib import Path
REL, NET, REPO, OUT = map(Path, sys.argv[1:5])
sys.path.insert(0, str(REL)); sys.path.insert(0, str(REL / 'helpers'))
logging.disable(logging.WARNING)
results = {}; t00 = time.time()
sha_b = lambda b: hashlib.sha256(b).hexdigest()


def test(name):
    def deco(f):
        t = time.time()
        try: results[name] = {'status': 'PASS', 'detail': f(), 'seconds': round(time.time() - t, 2)}
        except Exception as e: results[name] = {'status': 'FAIL', 'detail': type(e).__name__ + ': ' + str(e)[:2000], 'trace': traceback.format_exc()[-3000:], 'seconds': round(time.time() - t, 2)}
        print(name, results[name]['status'], results[name]['seconds'], flush=True)
    return deco


@test('T01_scheme_A_files_equal_PR4_commit')
def _():
    base = 'research_inputs/derived/exact_source_closure_a_max_account_v1_20261011/'
    out = {}
    for f in ['EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json', 'EXACT_SOURCE_CLOSURE_A_CHANGESET.json', 'LOADS_AND_WEIGHTS_REFERENCE.json', 'carrier_fragment.json', 'external_pending_fixed_accounts.json']:
        blob = subprocess.check_output(['git', '-C', str(REPO), 'show', '8883de6fb3e15767c632ac92f535e8a423e90b69:' + base + f])
        local = (REL / 'scheme_a' / f).read_bytes(); assert blob == local, f; out[f] = sha_b(local)
    assert out['EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json'] == 'a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720'
    for f, h in [('V4_APPROVED.json', '955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f'), ('GATE6_3H_ROUNDING_AUDIT.json', 'c6f95ca9be8db91b17f3e0a6188935337cf23a3efdf1f57819db5c0e0e06fe56'),
                 ('EFFECTIVE_PERTURBATION_LEDGER.csv', '0450345f1c6a89d89309c920c66d8f7286b84aac76597fa7bd9db19a5a988856')]:
        assert sha_b((REL / f).read_bytes()) == h, f
    return out


def tampered_root(edit):
    """Copy of the release data with one JSON input edited; code is unchanged."""
    d = Path(tempfile.mkdtemp(prefix='d1neg_')); shutil.copytree(REL, d / 'r', ignore=shutil.ignore_patterns('_c02r_original', '__pycache__'))
    edit(d / 'r'); return d


def expect_reject(edit, expect):
    from d1_model import assemble_2920
    d = tampered_root(edit)
    try:
        (d / 'out').mkdir(); assemble_2920(NET, d / 'r', d / 'out', lambda s: None)
    except AssertionError as e:
        msg = repr(e.args)[:300]; assert expect in msg, msg; return 'REJECTED: ' + msg
    finally: shutil.rmtree(d)
    raise AssertionError('tampered input accepted')


def edit_json(rel, fn):
    def f(root):
        p = root / rel; v = json.loads(p.read_text()); fn(v); p.write_text(json.dumps(v))
    return f


@test('T02_negative_changeset_after_hex')
def _():
    def fn(v): v['changes'][0]['after_hex'] = float.hex(float.fromhex(v['changes'][0]['after_hex']) * 2)
    return expect_reject(edit_json('scheme_a/EXACT_SOURCE_CLOSURE_A_CHANGESET.json', fn), '')


@test('T03_negative_load_reference')
def _():
    def fn(v): v['loads'][5]['binary64_sha256'] = '0' * 64
    return expect_reject(edit_json('scheme_a/LOADS_AND_WEIGHTS_REFERENCE.json', fn), 'LOAD_REFERENCE')


@test('T04_negative_group_D_gt_Q')
def _():
    # Move one account out of its group: that group's Q' drops below D (or the 807 ownership set breaks).
    def fn(v):
        g = next(x for x in v['groups'] if len(x['stores']) >= 2); g['stores'] = g['stores'][:1]
    return expect_reject(edit_json('GATE6_3H_ROUNDING_AUDIT.json', fn), '')


@test('T05_negative_wrong_source_network')
def _():
    def fn(v): v['network_reference']['sha256'] = '1' * 64
    return expect_reject(edit_json('scheme_a/LOADS_AND_WEIGHTS_REFERENCE.json', fn), '')


@test('T06_truncated_end_to_end_build_bridge_gates_index')
def _():
    import d1_build, d1_worker
    from c02_common import write, sha, read
    run = Path(tempfile.mkdtemp(prefix='d1run_')) / 'run'; run.mkdir()
    now = time.time(); T = 16
    a = {'run_id': 'd1_local_test', 'source_network': str(NET), 'source_network_sha256': sha(NET), 'test_snapshots': T,
         'build_phase_seconds': 3600, 'build_absolute_deadline_epoch': now + 3600}
    write(run / 'AUTHORIZATION.json', a)
    stop = threading.Event()
    def hb():
        while not stop.is_set(): write(run / 'GUARD_HEARTBEAT.json', {'epoch': time.time()}); time.sleep(1)
    th = threading.Thread(target=hb, daemon=True); th.start(); time.sleep(1.2)
    d1_build.resources = lambda p: {}; d1_build.resource_gate = lambda r, start=False: None   # 10 GB laptop: cgroup gate not applicable
    import d1_model, fixed_accounts
    real, real_validate = d1_model.assemble_2920, fixed_accounts.validate_exported_accounting
    skipped = []

    def truncated(source, root, out, progress):
        # Harness only: the real full-2920 assembly runs every network gate including validate_exported_accounting on the
        # true annual horizon. Afterwards the horizon is shortened for the Linopy path; the annual fixed-quantity
        # validator cannot hold on 16 snapshots and is the only check skipped there (recorded below).
        n = real(source, root, out, progress)
        n.set_snapshots(n.snapshots[:T]); n.snapshot_weightings.loc[:, ['objective', 'generators', 'stores']] = 3.
        fixed_accounts.validate_exported_accounting = lambda m: skipped.append('validate_exported_accounting@T=%d' % len(m.snapshots))
        return n
    d1_model.assemble_2920 = truncated
    try:
        d1_build.main(run)
        res = read(run / 'BUILD_RESULT.json'); assert res['status'] == 'D1_BUILD_STATIC_ACCEPTED_NO_SOLVE', res
        from d1_bridge import bridge
        bridge(run / 'artifacts', run / 'bridge', lambda s: None)
        g = d1_worker.build_gates(run, lambda s: None); d1_worker.artifact_index(run, lambda s: None)
        assert g['status'] == 'D1_BUILD_GATES_PASS', g['gates']
        idx = read(run / 'ARTIFACT_SHA_INDEX.json'); cov = read(run / 'artifacts/D1_CONSTRAINT_COVERAGE.json')
        b = read(run / 'artifacts/GATE6_2920_V4_BINDING.json')
        return {'build_result': {k: res[k] for k in ('snapshots', 'rows', 'columns', 'nnz', 'build_seconds', 'peak_worker_rss_bytes')},
                'gates': g['gates'], 'label_coverage': g['label_coverage'], 'dims': g['dimensions'], 'scheme_A_slack_MWh': g['scheme_A_slack_MWh'],
                'artifact_files': idx['file_count'], 'artifact_bytes': idx['bytes'], 'families': len(cov['families']),
                'binding': {k: b[k] for k in ('binding_id', 'snapshots', 'expected_snapshots', 'hours_per_snapshot', 'V4_formulas_changed', 'physical_absolute_floor', 'physical_relative_budget', 'kkt_normalized_budget')},
                'full_2920_network_gates': read(run / 'artifacts/D1_NETWORK_LP_DIFF_REGISTER.json')['status'],
                'harness_only_skipped_on_truncated_horizon': skipped}
    finally:
        d1_model.assemble_2920 = real; fixed_accounts.validate_exported_accounting = real_validate; stop.set(); th.join(); shutil.rmtree(run.parent)


@test('T07_authorization_limits_and_phase_budgets')
def _():
    from d_production_control import limits_valid, phase_deadline
    now = time.time()
    a = {'build_phase_seconds': 10800, 'build_absolute_deadline_epoch': now + 10800, 'bridge_phase_seconds': 3600, 'load_absolute_deadline_epoch': now + 14400,
         'maximum_native_seconds': 1, 'native_absolute_deadline_epoch': now + 14401, 'raw_save_seconds': 300, 'raw_absolute_deadline_epoch': now + 14851,
         'post_phase_seconds': 1800, 'post_absolute_deadline_epoch': now + 16651, 'absolute_deadline_epoch': now + 16951,
         'native_exit_grace_seconds': 120, 'term_grace_seconds': 30, 'supervisor_lease_seconds': 8, 'soft_memory_limit_decimal_gb': 65,
         'resource_limits': {'rss_bytes': 75 * 1024 ** 3, 'cgroup_headroom_bytes': 12 * 1024 ** 3, 'disk_free_bytes': 8 * 1024 ** 3}}
    limits_valid(a)
    d = {p: phase_deadline({'phase': p, 'entered_epoch': now}, a) - now for p in ('BUILD', 'BRIDGE', 'POSTPROCESS', 'DONE')}
    assert d == {'BUILD': 10800, 'BRIDGE': 3600, 'POSTPROCESS': 1800, 'DONE': 16651}
    bad = dict(a, resource_limits=dict(a['resource_limits'], rss_bytes=60 * 1024 ** 3))
    try: limits_valid(bad); raise AssertionError('soft memory over RSS accepted')
    except ValueError: pass
    return {'phase_budgets_seconds': d, 'rss_soft_limit_negative': 'REJECTED'}


@test('T08_solver_import_firewall')
def _():
    code = ('import sys;sys.argv=["x"];sys.path.insert(0,%r);import runpy\n' % str(REL)
            + 'g=runpy.run_path(%r,run_name="d1fw")\n' % str(REL / 'd1_build.py')
            + 'try:\n import gurobipy\nexcept ModuleNotFoundError as e:print("BLOCKED",e)\n')
    out = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=120)
    assert 'BLOCKED D1_NO_SOLVER_IMPORT:gurobipy' in out.stdout, out.stdout + out.stderr[-500:]
    return out.stdout.strip()


status = 'PASS' if all(r['status'] == 'PASS' for r in results.values()) else 'FAIL'
OUT.write_text(json.dumps({'status': status, 'tests': results, 'solver_calls': 0, 'cloud_actions': 0, 'seconds': round(time.time() - t00, 1),
                           'environment': 'WSL pypsa-earth env: python 3.11.13, pypsa 0.30.3, linopy 0.5.5, numpy 1.26.4, scipy 1.15.2, pandas 2.3.1, xarray 2025.1.2, netCDF4 1.7.2, psutil 7.0.0',
                           'note': 'Real frozen 2920 network for all network-level gates; Linopy build/export/bridge/gates on T=16 (10 GB RAM). Cloud runs identical code at T=2920.'}, indent=1, default=str) + '\n')
print(status)
