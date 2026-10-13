"""D-5b local tests (derived from d5_local_tests.py: TimeLimit 43200, run 50400, basis save) (no solver) = C09 T01-T10 on locally built truncated D-1/D-2 artifacts, plus D-specific gates.

The same tests T01-T07 ran on the real 2920 CSC in the cloud D-2 job (D2_CLOUD_READONLY_CHECKS.json).
Usage: python d5_local_tests.py <release_d5> <local d1 run> <local d2 out> <out json>
"""
import sys, json, shutil, tempfile, time, hashlib, os, traceback
from pathlib import Path
SRC, D1, D2, OUT = map(Path, sys.argv[1:5])
TMP = Path(tempfile.mkdtemp(prefix='d5t_')); REL = TMP / 'release'
shutil.copytree(SRC, REL, ignore=shutil.ignore_patterns('__pycache__'))
exp = json.loads((D2 / 'D2_CLOUD_READONLY_CHECKS.json').read_text())['expected_for_D5']
(REL / 'D5_EXPECTED.json').write_text(json.dumps(exp))
sys.path.insert(0, str(REL)); sys.path.insert(0, str(REL / 'helpers'))
import numpy as np
from adapter import open_problem, validate, load_candidate, exact_readback
import d5_decompose as D5
from d5_checks import parameter_diff
from v4_algebra_extracted import complete_kkt
T = {}


def check(name, fn):
    t = time.time()
    try: T[name] = {'status': 'PASS', 'detail': fn(), 'seconds': round(time.time() - t, 2)}
    except Exception as e: T[name] = {'status': 'FAIL', 'error': f'{type(e).__name__}: {e}'[:1500], 'trace': traceback.format_exc()[-2000:]}
    print(name, T[name]['status'], str(T[name].get('detail', T[name].get('error')))[:200], flush=True)


MP = D1 / 'bridge'
meta, a = open_problem(MP / 'math_problem', verify=True)
rec, cols, rows, xb = D5.load_block()
check('T01_block_verify_truncated_d1_csc', lambda: D5.verify_block(meta, a, cols, rows, xb))


def neg(mut):
    a2 = dict(a); a2, c2, r2, x2 = mut(a2, cols, rows, xb)
    try: D5.verify_block(meta, a2, c2, r2, x2)
    except (ValueError, IndexError) as e: return 'REJECTED: ' + str(e)[:100]
    raise AssertionError('tampering not detected')
def t_cost(a2, c, r, x): cc = np.array(a2['cost']); cc[c[5]] = 1.0; a2['cost'] = cc; return a2, c, r, x
def t_primal(a2, c, r, x): x = x.copy(); x[1000] += 1e-3; return a2, c, r, x
def t_cross(a2, c, r, x):
    idx = np.array(a2['index']); inrow = np.zeros(meta['num_row'], bool); inrow[r] = True
    idx[int(a2['start'][int(c[0])])] = int(np.flatnonzero(~inrow)[0]); a2['index'] = idx; return a2, c, r, x
def t_rowset(a2, c, r, x): return a2, c, r[1:], x
check('T02_negative_nonzero_block_cost', lambda: neg(t_cost))
check('T03_negative_perturbed_block_primal', lambda: neg(t_primal))
check('T04_negative_cross_entry', lambda: neg(t_cross))
check('T05_negative_row_set', lambda: neg(t_rowset))
def t05b():
    bad = dict(exp, block_receipt_sha256='0' * 64); (REL / 'D5_EXPECTED.json').write_text(json.dumps(bad))
    import importlib; m = importlib.reload(D5)
    try: m.load_block()
    except ValueError as e: return 'REJECTED: ' + str(e)
    finally: (REL / 'D5_EXPECTED.json').write_text(json.dumps(exp)); importlib.reload(D5)
    raise AssertionError('swapped block receipt accepted')
check('T05b_negative_block_receipt_binding', t05b)
mmeta, marr, mc, mr, ident = D5.main_problem(meta, a, cols, rows)
def t06():
    v = validate(mmeta, marr); assert mmeta['num_col'] == meta['num_col'] - exp['block_columns'] and mmeta['num_row'] == meta['num_row'] - exp['block_rows']; return v
check('T06_main_problem_validate_dims', t06)
def t07():
    st = np.asarray(a['start']); idx = np.asarray(a['index']); val = np.asarray(a['value'])
    rowmap = np.full(meta['num_row'], -1); rowmap[mr] = np.arange(len(mr))
    for j_new in range(len(mc)):
        j = mc[j_new]; p, q = st[j], st[j + 1]; P, Q = marr['start'][j_new], marr['start'][j_new + 1]
        assert np.array_equal(rowmap[idx[p:q]], marr['index'][P:Q]) and np.array_equal(val[p:q].view('u8'), marr['value'][P:Q].view('u8'))
    for k, sel in [('cost', mc), ('col_lower', mc), ('col_upper', mc), ('row_lower', mr), ('row_upper', mr)]:
        assert np.array_equal(np.asarray(a[k])[sel].view('u8'), marr[k].view('u8'))
    assert mmeta['offset'] == meta['offset']; return 'bitwise restriction on ALL main columns + all cost/bounds'
check('T07_main_restriction_bitwise', t07)


class Fake:
    def create(self, off): self.off = off; self.rs = []; self.rh = []; self.cols = []
    def rows(self, s, r): self.rs.append(s.copy()); self.rh.append(r.copy())
    def update(self): pass
    def columns(self, beg, ids, vals, obj, lb, ub): self.cols.append((beg.copy(), ids.copy(), vals.copy(), obj.copy(), lb.copy(), ub.copy()))
    def _cat(self):
        if not hasattr(self, 'S'):
            self.S = np.concatenate(self.rs); self.H = np.concatenate(self.rh)
            self.O = np.concatenate([c[3] for c in self.cols]); self.L = np.concatenate([c[4] for c in self.cols]); self.U = np.concatenate([c[5] for c in self.cols])
            st = [0]; ids = []; vals = []
            for beg, i, v, *_ in self.cols:
                base = st[-1]; st.extend((base + np.append(beg[1:], len(i))).tolist()); ids.append(i); vals.append(v)
            self.ST = np.array(st); self.I = np.concatenate(ids); self.V = np.concatenate(vals)
    def scalar(self, attr, kind):
        self._cat(); return {'NumVars': len(self.O), 'NumConstrs': len(self.H), 'ModelSense': 1, 'ObjCon': self.off}[attr]
    def array(self, attr, s, n, dtype='<f8'):
        self._cat()
        if attr == 'VType': return np.full(n, b'C', dtype='S1')
        return {'Obj': self.O, 'LB': self.L, 'UB': self.U, 'Sense': self.S, 'RHS': self.H}[attr][s:s + n]
    def matrix_columns(self, s, n):
        self._cat(); p, q = self.ST[s], self.ST[s + n]; return (self.ST[s:s + n] - p).astype(np.int32), self.I[p:q], self.V[p:q]
check('T08_load_and_exact_readback_fake_backend', lambda: exact_readback(*(lambda f: (load_candidate(f, mmeta, marr), f)[1:])(Fake()), mmeta, marr))


def t09():
    base = json.loads((REL / 'C06_EFFECTIVE_MODEL_PARAMETERS.json').read_text())
    ok = parameter_diff(base, dict(base, Crossover=-1, TimeLimit=43200.)); assert ok['status'] == 'PASS', ok['unauthorized']
    ok2 = parameter_diff(base, dict(base, Crossover=-1, TimeLimit=13999.5)); assert ok2['status'] == 'PASS'
    bad = parameter_diff(base, dict(base, Crossover=-1, TimeLimit=43200., NumericFocus=3)); assert bad['status'] == 'FAIL'
    bad2 = parameter_diff(base, dict(base, TimeLimit=43200.)); assert bad2['status'] == 'FAIL'
    bad3 = parameter_diff(base, dict(base, Crossover=-1, TimeLimit=50000.)); assert bad3['status'] == 'FAIL'
    bad4 = parameter_diff(base, dict(base, Crossover=-1, Threads=8)); assert bad4['status'] == 'FAIL'
    return {'authorized': ok['differences'], 'rejects_extra_NumericFocus': bad['unauthorized'], 'rejects_missing_crossover': bad2['unauthorized'],
            'rejects_TimeLimit_50000': bad3['unauthorized'], 'rejects_Threads_8': bad4['unauthorized']}
check('T09_parameter_gate_crossover_and_timelimit_43200', t09)


def t10():
    # Pipeline test only (no solution exists locally): synthetic main vectors -> exact merge -> unchanged V4 algebra.
    d = Path(tempfile.mkdtemp()); raw = d / 'raw'; raw.mkdir(); recv = {'vectors': {}}
    rng = np.random.default_rng(1)
    for k, n in [('X', len(mc)), ('Pi', len(mr)), ('RC', len(mc))]:
        np.save(raw / f'{k}.npy', rng.standard_normal(n)); recv['vectors'][k] = {'status': 'SAVED_UNQUALIFIED', 'sha256': hashlib.sha256((raw / f'{k}.npy').read_bytes()).hexdigest()}
    (raw / 'RAW_RECEIPT.json').write_text(json.dumps(recv))
    D5.merge(raw, d / 'merged', meta, cols, rows, xb, mc, mr, 2)
    z, pi, rc = [np.load(d / f'merged/vectors/{k}.npy') for k in ('X', 'Pi', 'RC')]
    assert np.array_equal(z[mc].view('u8'), np.load(raw / 'X.npy').view('u8')) and np.array_equal(z[cols].view('u8'), xb.view('u8')) and not pi[rows].any() and not rc[cols].any()
    Dm = np.load(MP / 'mapping/D.npy'); Rm = np.load(MP / 'mapping/R.npy')
    k = complete_kkt(meta, a, z, pi, rc, Dm, Rm, d / 'kkt', json.loads((REL / 'V4_APPROVED.json').read_text()))
    act = np.load(d / 'kkt/algebra/activity_solver.npy'); lo, hi = np.asarray(a['row_lower']), np.asarray(a['row_upper'])
    viol = np.maximum(np.where(np.isfinite(lo), lo - act, 0), np.where(np.isfinite(hi), act - hi, 0))
    blockmax = float(viol[rows].max()); shutil.rmtree(d)
    assert blockmax <= 1e-12 * max(1.0, float(np.abs(act[rows]).max()))
    return {'merge_bitwise': True, 'block_rows_max_violation_LP_units': blockmax, 'V4_ran': True, 'independent_kkt_pass_expected_false_for_random_main': k['independent_kkt_pass']}
check('T10_merge_plus_unchanged_V4_pipeline', t10)


def t11():
    # Immutable D-1 binding + read-only directory links; local stand-in ROOT with the same layout (runs/d1_build2920_*).
    import d5_checks
    root = TMP / 'root'; (root / 'runs').mkdir(parents=True); base = root / 'runs' / 'd1_build2920_LOCAL'; shutil.copytree(D1, base)
    idx = json.loads((base / 'ARTIFACT_SHA_INDEX.json').read_text())
    sb = {'baseline_run_id': base.name, 'baseline_path': str(base), 'baseline_ARTIFACT_SHA_INDEX_sha256': hashlib.sha256((base / 'ARTIFACT_SHA_INDEX.json').read_bytes()).hexdigest(),
          'core': {'D1_BUILD_GATES.json': hashlib.sha256((base / 'D1_BUILD_GATES.json').read_bytes()).hexdigest()}, 'files': idx['files'], 'bytes': idx['bytes']}
    (REL / 'SOURCE_BINDING.json').write_text(json.dumps(sb)); d5_checks.ROOT = root
    run = TMP / 'run'; run.mkdir(); s = d5_checks.verify_inputs(run, lambda x: None)
    assert (run / 'artifacts').is_symlink() and (run / 'bridge').is_symlink() and json.loads((run / 'IMMUTABLE_INPUTS.json').read_text())['status'] == 'ALL_REFERENCED_INPUT_SHA_PASS'
    victim = base / idx['files'][3]['relative']; data = victim.read_bytes(); victim.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
    run2 = TMP / 'run2'; run2.mkdir()
    try: d5_checks.verify_inputs(run2, lambda x: None); raise AssertionError('tampered D-1 artifact accepted')
    except AssertionError as e:
        if 'accepted' in str(e): raise
        return {'files_bound': len(s['files']), 'tamper_one_byte': 'REJECTED ' + idx['files'][3]['relative']}
check('T11_D1_binding_and_tamper_negative', t11)


def t12():
    import d5_acceptance, pypsa, logging
    logging.disable(logging.WARNING)
    b = json.loads((D1 / 'artifacts/GATE6_2920_V4_BINDING.json').read_text())
    assert (D1 / 'artifacts/gate6_2920_scheme_a_unsolved.nc').exists() and b['network_SHA256'] == hashlib.sha256((D1 / 'artifacts/gate6_2920_scheme_a_unsolved.nc').read_bytes()).hexdigest()
    n = pypsa.Network(D1 / 'artifacts/gate6_2920_scheme_a_unsolved.nc')
    assert len(n.snapshots) == 2920   # exported network is the full 2920 horizon even in the truncated local LP
    try: d5_acceptance.restore_network(n, D1 / 'artifacts/mapping', np.load(MP / 'mapping/vlabels.npy'), np.zeros(meta['num_col']), b['snapshots'])
    except AssertionError: return {'binding_file': 'GATE6_2920_V4_BINDING.json', 'network_file_sha_bound': True, 'restore_rejects_binding_snapshots_%d' % b['snapshots']: True}
    raise AssertionError('non-2920 binding accepted by restore_network')
check('T12_acceptance_2920_rebinding_guard', t12)


def t13():
    from d_production_control import limits_valid, phase_deadline
    now = time.time()
    a = {'build_phase_seconds': 1, 'build_absolute_deadline_epoch': now + 1, 'bridge_phase_seconds': 2400, 'post_phase_seconds': 3000,
         'load_absolute_deadline_epoch': now + 2400, 'native_absolute_deadline_epoch': now + 45600, 'raw_absolute_deadline_epoch': now + 46500, 'post_absolute_deadline_epoch': now + 49500,
         'absolute_deadline_epoch': now + 50400, 'maximum_native_seconds': 43200, 'native_exit_grace_seconds': 120, 'term_grace_seconds': 30, 'raw_save_seconds': 600,
         'supervisor_lease_seconds': 8, 'soft_memory_limit_decimal_gb': 65, 'resource_limits': {'rss_bytes': 75 * 1024 ** 3, 'cgroup_headroom_bytes': 12 * 1024 ** 3, 'disk_free_bytes': 8 * 1024 ** 3}}
    limits_valid(a)
    launch = (REL / 'd5_launch.py').read_text()
    for frag in ["'load_absolute_deadline_epoch':now+2400", "'native_absolute_deadline_epoch':now+45600", "'raw_absolute_deadline_epoch':now+46500", "'post_absolute_deadline_epoch':now+49500",
                 "'absolute_deadline_epoch':now+50400", "'maximum_native_seconds':43200", "D5B_REQUIRES_COMPLETED_D5", "save_final_basis", "'raw_save_seconds':600", "'bridge_phase_seconds':2400", "'post_phase_seconds':3000"]:
        assert frag in launch, frag
    return {p: phase_deadline({'phase': p, 'entered_epoch': now}, a) - now for p in ('BRIDGE', 'NATIVE', 'RAW_SAVE', 'POSTPROCESS')}
check('T13_authorization_deadlines_43200_50400', t13)


def t14():
    # save_basis with a fake native library: int32 arrays in chunks, receipt, and a failure path that never raises.
    import d5_native, ctypes as C
    class Fn:
        def __init__(self, fail): self.fail = fail
        def __call__(self, model, name, s, n, ptr):
            if self.fail: return 10005
            arr = np.ctypeslib.as_array(C.cast(ptr, C.POINTER(C.c_int32)), shape=(n,)); arr[:] = (np.arange(s, s + n) % 3) - 1; return 0
    class Lib:
        def __init__(self, fail): self.GRBgetintattrarray = Fn(fail)
    class B: model = None
    out = {}
    for fail in (False, True):
        run = TMP / ('basis_run_%d' % fail); (run / 'raw').mkdir(parents=True)
        r = d5_native.save_basis(Lib(fail), B(), {'num_col': 1000, 'num_row': 2500}, run, {'run_id': 'x', 'raw_absolute_deadline_epoch': time.time() + 60})
        out['fail' if fail else 'ok'] = {k: v['status'] for k, v in r['arrays'].items()}
        if not fail:
            v = np.load(run / 'raw/basis/VBasis.npy'); assert v.dtype == np.int32 and len(v) == 1000 and np.array_equal(v, (np.arange(1000) % 3) - 1)
    assert out == {'ok': {'VBasis': 'SAVED', 'CBasis': 'SAVED'}, 'fail': {'VBasis': 'NOT_AVAILABLE', 'CBasis': 'NOT_AVAILABLE'}}
    src = (REL / 'd5_native.py').read_text()
    # Basis is only read after optimize: no basis/start setter and no file read-in anywhere in the native worker.
    assert not any(x in src for x in ('GRBsetintattrarray', 'GRBsetdblattrarray', 'GRBread', 'PStart', 'DStart', "b'Start'"))
    assert src.index('save_basis(lib, backend') > src.index('int(lib.GRBoptimize(backend.model))')
    return out
check('T14_basis_saved_only_not_used', t14)

status = 'PASS' if all(v['status'] == 'PASS' for v in T.values()) else 'FAIL'
OUT.write_text(json.dumps({'status': status, 'tests': T, 'solver_calls': 0,
                           'note': 'D-5b. Local WSL (same package versions as 122). Truncated T=16 D-1 build + D-2 block from the same code; T01-T07 also ran on the real 2920 CSC in the cloud D-2 job. T10 is a pipeline test with synthetic main vectors, not an acceptance.'},
                          indent=1, default=str) + '\n')
shutil.rmtree(TMP); print('OVERALL', status)
