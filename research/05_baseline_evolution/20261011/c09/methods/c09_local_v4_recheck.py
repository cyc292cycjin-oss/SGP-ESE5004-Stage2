"""C09 local read-only recheck of the fetched run (no solver, no model build).

Run in WSL with the pypsa-earth env (numpy 1.26.4 / scipy 1.15.2, same as cloud):
    python c09_local_v4_recheck.py <extracted C09 release dir> <local cloud_run dir> <frozen C03 bridge dir> <output json>

1. Re-derive the main-LP restriction from the frozen C03 CSC and compare its SHA identity with the cloud receipt.
2. Re-run the release's block verification (decoupling, zero cost, block feasibility) locally.
3. Check the merge bitwise with code independent of c09_decompose.merge.
4. Plain numpy residuals of the main LP in native coordinates (not the V4 code path).
5. Re-run the unchanged V4 algebra (complete_kkt) on the merged vectors and compare with cloud KKT.json.
"""
import sys, json, time, tempfile, shutil
from pathlib import Path
import numpy as np

REL, RUN, BR, OUT = map(Path, sys.argv[1:5])
sys.path.insert(0, str(REL)); sys.path.insert(0, str(REL / 'helpers'))
from adapter import open_problem
from c09_decompose import load_block, verify_block, main_problem
from v4_algebra_extracted import complete_kkt

t0 = time.time(); res = {'qualification': 'LOCAL_READ_ONLY_RECHECK_NO_SOLVER', 'run_id': RUN.parent.name}
meta, a = open_problem(BR / 'math_problem', verify=True)
D = np.load(BR / 'mapping/D.npy'); R = np.load(BR / 'mapping/R.npy')
rec, cols, rows, xb = load_block()

# 1. main restriction identity
mmeta, ma, mc, mr, ident = main_problem(meta, a, cols, rows)
cloud_id = json.loads((RUN / 'C09_MAIN_PROBLEM_IDENTITY.json').read_text())
res['main_identity'] = {'dims': [mmeta['num_col'], mmeta['num_row'], mmeta['nnz']],
                        'all_array_sha_match_cloud': ident == cloud_id['arrays_sha256'],
                        'main_columns_file_match': bool(np.array_equal(np.load(RUN / 'C09_MAIN_COLUMNS.npy'), mc)),
                        'main_rows_file_match': bool(np.array_equal(np.load(RUN / 'C09_MAIN_ROWS.npy'), mr))}

# 2. block verification
res['block'] = verify_block(meta, a, cols, rows, xb)
res['block']['partition'] = bool(len(np.intersect1d(cols, mc)) == 0 and len(cols) + len(mc) == meta['num_col']
                                 and len(np.intersect1d(rows, mr)) == 0 and len(rows) + len(mr) == meta['num_row'])

# 3. merge
raw = {k: np.load(RUN / 'raw/vectors' / (k + '.npy')) for k in ('X', 'Pi', 'RC')}
mer = {k: np.load(RUN / 'merged_for_V4/vectors' / (k + '.npy')) for k in ('X', 'Pi', 'RC')}
bits = lambda v: np.ascontiguousarray(v).view('u8')
res['merge'] = {
    'X_main_bitwise': bool(np.array_equal(bits(mer['X'][mc]), bits(raw['X']))),
    'Pi_main_bitwise': bool(np.array_equal(bits(mer['Pi'][mr]), bits(raw['Pi']))),
    'RC_main_bitwise': bool(np.array_equal(bits(mer['RC'][mc]), bits(raw['RC']))),
    'X_block_equals_prebuilt_primal': bool(np.array_equal(bits(mer['X'][cols]), bits(xb))),
    'Pi_block_all_zero': bool(np.all(mer['Pi'][rows] == 0)),
    'RC_block_all_zero': bool(np.all(mer['RC'][cols] == 0)),
}

# 4. plain residuals of the main LP in native (C03) coordinates
x, pi, rc = raw['X'], raw['Pi'], raw['RC']
st, ix, va = ma['start'], ma['index'], ma['value']
colof = np.repeat(np.arange(mmeta['num_col']), np.diff(st))
act = np.bincount(ix, weights=va * x[colof], minlength=mmeta['num_row'])
lo, hi = ma['row_lower'], ma['row_upper']
rv = np.maximum(np.where(np.isfinite(lo), lo - act, 0), np.where(np.isfinite(hi), act - hi, 0))
cv = np.maximum(np.where(np.isfinite(ma['col_lower']), ma['col_lower'] - x, 0), np.where(np.isfinite(ma['col_upper']), x - ma['col_upper'], 0))
aty = np.bincount(colof, weights=va * pi[ix], minlength=mmeta['num_col'])
stat = np.abs(ma['cost'] - aty - rc)
res['main_native_plain'] = {'row_violation_max': float(rv.max()), 'column_violation_max': float(cv.max()),
                            'stationarity_abs_max_native': float(stat.max()),
                            'objective_cTx_plus_offset': float(ma['cost'] @ x + meta['offset'])}

# 5. unchanged V4 algebra on merged vectors
d = tempfile.mkdtemp()
try:
    contract = json.loads((REL / 'V4_APPROVED.json').read_text())
    kkt = complete_kkt(meta, a, mer['X'], mer['Pi'], mer['RC'], D, R, d + '/kkt', contract)
finally:
    shutil.rmtree(d)
cloud = json.loads((RUN / 'postprocess/KKT.json').read_text())
keys = [k for k in cloud if isinstance(cloud[k], (int, float, bool)) and not isinstance(cloud[k], str)]
res['V4_kkt_local'] = {k: kkt[k] for k in keys if k in kkt}
res['V4_kkt_identical_to_cloud'] = all(kkt.get(k) == cloud[k] for k in keys)
res['V4_kkt_mismatches'] = {k: [kkt.get(k), cloud[k]] for k in keys if kkt.get(k) != cloud[k]}
res['seconds'] = time.time() - t0
OUT.write_text(json.dumps(res, indent=2, default=lambda o: o.item() if hasattr(o, 'item') else str(o)) + '\n')
print(json.dumps(res, indent=2, default=lambda o: o.item() if hasattr(o, 'item') else str(o)))
