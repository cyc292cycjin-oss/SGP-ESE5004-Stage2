"""D-2 read-only job on the D-1 2920 CSC (no solver, no build, no write to D-1 files).

1. Verify the D-1 run (gates PASS, every artifact/bridge file SHA against ARTIFACT_SHA_INDEX.json).
2. tools/block_tools.py: identify the fixed-resource block, build its exact primal, exact-rational row verification.
3. D-5 decomposition code on the real CSC: verify_block (1e-12 LP-unit tolerance), four tamper negatives,
   main-LP restriction identity, validate, bitwise restriction sample (C09 T01-T07 on real 2920 data).
Usage: python d2_job.py <d1 run dir> <out dir>
"""
import sys, json, time, hashlib, shutil, importlib.util, traceback
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import numpy as np


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 23), b''): h.update(b)
    return h.hexdigest()


def put(p, v):
    tmp = Path(str(p) + '.tmp'); tmp.write_text(json.dumps(v, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o)) + '\n'); tmp.rename(p)


def main(run, out):
    t0 = time.time(); out.mkdir(exist_ok=False); status = {'phase': 'START', 'epoch': t0, 'solver_calls': 0}; put(out / 'D2_STATUS.json', status)
    def stage(s): status.update(phase=s, epoch=time.time(), elapsed=time.time() - t0); put(out / 'D2_STATUS.json', status)
    gates = json.loads((run / 'D1_BUILD_GATES.json').read_text()); assert gates['status'] == 'D1_BUILD_GATES_PASS'
    idx = json.loads((run / 'ARTIFACT_SHA_INDEX.json').read_text())
    for f in idx['files']:
        p = run / f['relative']; assert p.stat().st_size == f['bytes'] and sha(p) == f['sha256'], f['relative']
    stage('D1_ARTIFACTS_SHA_PASS')
    import block_tools as bt
    mp, mapping, labels = run / 'bridge/math_problem', run / 'bridge/mapping', run / 'artifacts/mapping'
    meta, a, A = bt.load_problem(mp); ci = bt.column_info(mapping, labels); stage('BLOCK_TOOLS_LOADED')
    cols, rows, rec = bt.identify_block(A, a, ci); stage('BLOCK_IDENTIFIED')
    xb, vr = bt.build_block_primal(A, a, ci, cols, rows); stage('BLOCK_PRIMAL_BUILT_AND_EXACT_VERIFIED')
    blk = out / 'block'; blk.mkdir()
    np.save(blk / 'BLOCK_COLUMNS.npy', cols.astype(np.int64)); np.save(blk / 'BLOCK_ROWS.npy', rows.astype(np.int64)); np.save(blk / 'BLOCK_PRIMAL.npy', xb)
    rec.update(vr, seconds=time.time() - t0, files={f: sha(blk / f) for f in ['BLOCK_COLUMNS.npy', 'BLOCK_ROWS.npy', 'BLOCK_PRIMAL.npy']},
               source_manifest_sha256=sha(mp / 'MATH_PROBLEM.json'), block_duals='exactly 0', tool_sha256=sha(HERE / 'block_tools.py'), d1_run=str(run))
    put(blk / 'BLOCK_RECEIPT.json', rec)
    del A, ci
    req = {'cross_entries_0': rec['cross_entries'] == 0, 'zero_cost': rec['zero_cost'] is True, 'stores_807': rec['stores'] == 807,
           'meters_found_807': rec['meters_found'] == 807, 'groups_385': rec['groups'] == 385, 'snapshots_2920': rec['snapshots'] == 2920,
           'exact_block_residual_le_1e-12_LP_units': rec['max_exact_violation_LP_units'] <= 1e-12}
    expected = {'block_dir': str(blk), 'block_receipt_sha256': sha(blk / 'BLOCK_RECEIPT.json'), 'block_columns': rec['block_columns'], 'block_rows': rec['block_rows'],
                'num_col': meta['num_col'], 'num_row': meta['num_row'], 'nnz': meta['nnz'], 'source_manifest_sha256': rec['source_manifest_sha256'], 'd1_run': str(run)}
    # D-5 decomposition module, byte-identical to the release copy, bound to this EXPECTED in a separate directory.
    dec = out / 'decompose_check'; dec.mkdir(); shutil.copyfile(HERE / 'd5_decompose.py', dec / 'd5_decompose.py'); put(dec / 'D5_EXPECTED.json', expected)
    assert sha(dec / 'd5_decompose.py') == sha(HERE / 'd5_decompose.py')
    spec = importlib.util.spec_from_file_location('d5_decompose', dec / 'd5_decompose.py'); D5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(D5)
    from adapter import open_problem, validate
    meta, a = open_problem(mp, verify=True); r2, cols, rows, xb = D5.load_block()
    T = {}
    def check(name, fn):
        t = time.time()
        try: T[name] = {'status': 'PASS', 'detail': fn(), 'seconds': round(time.time() - t, 1)}
        except Exception as e: T[name] = {'status': 'FAIL', 'error': type(e).__name__ + ': ' + str(e)[:500], 'trace': traceback.format_exc()[-1500:]}
        stage(name)
    check('T01_block_verify_real_2920_csc', lambda: D5.verify_block(meta, a, cols, rows, xb))
    def neg(mut):
        a2 = dict(a); a2, c2, r2_, x2 = mut(a2, cols, rows, xb)
        try: D5.verify_block(meta, a2, c2, r2_, x2)
        except (ValueError, IndexError) as e: return 'REJECTED: ' + str(e)[:100]
        raise AssertionError('tampering not detected')
    def t_cost(a2, c, r, x): cc = np.array(a2['cost']); cc[c[5]] = 1.0; a2['cost'] = cc; return a2, c, r, x
    def t_primal(a2, c, r, x): x = x.copy(); x[1000] += 1e-3; return a2, c, r, x
    def t_cross(a2, c, r, x):
        idx = np.array(a2['index']); j = int(c[0]); inrow = np.zeros(meta['num_row'], bool); inrow[r] = True
        k = int(np.flatnonzero(~inrow)[0]); idx[int(a2['start'][j])] = k; a2['index'] = idx; return a2, c, r, x
    def t_rowset(a2, c, r, x): return a2, c, r[1:], x
    check('T02_negative_nonzero_block_cost', lambda: neg(t_cost))
    check('T03_negative_perturbed_block_primal', lambda: neg(t_primal))
    check('T04_negative_cross_entry', lambda: neg(t_cross))
    check('T05_negative_row_set', lambda: neg(t_rowset))
    holder = {}
    def t06():
        mmeta, marr, mc, mr, ident = D5.main_problem(meta, a, cols, rows); holder.update(mmeta=mmeta, marr=marr, mc=mc, mr=mr, ident=ident)
        v = validate(mmeta, marr); return {'dims': [mmeta['num_col'], mmeta['num_row'], mmeta['nnz']], 'validate': v, 'arrays_sha256': ident}
    check('T06_main_problem_validate_dims', t06)
    def t07():
        mmeta, marr, mc, mr = holder['mmeta'], holder['marr'], holder['mc'], holder['mr']
        st = np.asarray(a['start']); idx = np.asarray(a['index']); val = np.asarray(a['value'])
        rowmap = np.full(meta['num_row'], -1); rowmap[mr] = np.arange(len(mr))
        for j_new in np.random.default_rng(0).choice(len(mc), 20000, replace=False):
            j = mc[j_new]; p, q = st[j], st[j + 1]; P, Q = marr['start'][j_new], marr['start'][j_new + 1]
            assert np.array_equal(rowmap[idx[p:q]], marr['index'][P:Q]) and np.array_equal(val[p:q].view('u8'), marr['value'][P:Q].view('u8'))
        for k, sel in [('cost', mc), ('col_lower', mc), ('col_upper', mc), ('row_lower', mr), ('row_upper', mr)]:
            assert np.array_equal(np.asarray(a[k])[sel].view('u8'), marr[k].view('u8'))
        assert mmeta['offset'] == meta['offset']; return 'bitwise restriction on 20000 sampled columns + all cost/bounds'
    check('T07_main_restriction_bitwise', t07)
    ok = all(req.values()) and all(v['status'] == 'PASS' for v in T.values())
    res = {'status': 'PASS' if ok else 'R4_BLOCKED', 'requirements': req, 'block_receipt': rec, 'expected_for_D5': expected,
           'main_problem': {'dims': T.get('T06_main_problem_validate_dims', {}).get('detail', {}).get('dims')}, 'tests': T,
           'solver_calls': 0, 'builds': 0, 'd1_files_rechecked': idx['file_count'], 'seconds': time.time() - t0}
    put(out / 'D2_CLOUD_READONLY_CHECKS.json', res); stage('DONE')


if __name__ == '__main__':
    out = Path(sys.argv[2])
    try: main(Path(sys.argv[1]), out)
    except BaseException as e:
        put(out / 'D2_FAILURE.json', {'error': type(e).__name__, 'detail': str(e)[:5000], 'trace': traceback.format_exc()[-5000:], 'solver_calls': 0, 'retry': False}); raise
