"""C09 exact block decomposition. No optimizer, environment or launch.

The frozen C03 daily CSC is split into
  * the decoupled zero-cost fixed-resource block (884,472 columns / 2,203,217 rows), and
  * the main LP (all other rows/columns).
Every structural claim is re-verified at runtime from the SHA-bound source arrays.
The block primal is a pre-built binary64 point (exact-rational residuals in
block/C09_BLOCK_PRIMAL_RECEIPT.json); block duals are exactly 0.  Source arrays are
read-only; the main LP is a pure row/column restriction (no coefficient changes).
"""
from pathlib import Path
import json, hashlib, time
import numpy as np

HERE = Path(__file__).resolve().parent
BLOCK = HERE / 'block'
EXPECTED = {'block_columns': 884472, 'block_rows': 2203217, 'num_col': 2450005, 'num_row': 6042238,
            'nnz': 11403496}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 * 1024 ** 2), b''):
            h.update(b)
    return h.hexdigest()


def arr_sha(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def load_block():
    rec = json.loads((BLOCK / 'C09_BLOCK_PRIMAL_RECEIPT.json').read_text())
    for name, h in rec['files'].items():
        if sha(BLOCK / name) != h:
            raise ValueError('BLOCK_FILE_SHA_MISMATCH ' + name)
    cols = np.load(BLOCK / 'C09_BLOCK_COLUMNS.npy')
    rows = np.load(BLOCK / 'C09_BLOCK_ROWS.npy')
    xb = np.load(BLOCK / 'C09_BLOCK_PRIMAL.npy')
    if len(cols) != EXPECTED['block_columns'] or len(rows) != EXPECTED['block_rows'] or len(xb) != len(cols):
        raise ValueError('BLOCK_DIMENSIONS')
    if not (np.all(np.diff(cols) > 0) and np.all(np.diff(rows) > 0)):
        raise ValueError('BLOCK_INDEX_NOT_STRICTLY_SORTED')
    if not np.isfinite(xb).all():
        raise ValueError('BLOCK_PRIMAL_NONFINITE')
    return rec, cols, rows, xb


def verify_block(meta, a, cols, rows, xb):
    """Recompute decoupling, zero cost and block feasibility from the frozen CSC."""
    n, m = meta['num_col'], meta['num_row']
    if (n, m, len(a['value'])) != (EXPECTED['num_col'], EXPECTED['num_row'], EXPECTED['nnz']):
        raise ValueError('SOURCE_DIMENSIONS')
    start = np.asarray(a['start']); index = np.asarray(a['index']); value = np.asarray(a['value'])
    incol = np.zeros(n, bool); incol[cols] = True
    inrow = np.zeros(m, bool); inrow[rows] = True
    colof = np.repeat(np.arange(n), np.diff(start))
    # (1) every nonzero is either (block row, block col) or (main row, main col)
    cross = incol[colof] != inrow[index]
    if cross.any():
        raise ValueError('BLOCK_NOT_DECOUPLED: %d cross entries' % int(cross.sum()))
    # (2) block rows are exactly the rows touched by block columns
    touched = np.zeros(m, bool); touched[index[incol[colof]]] = True
    if not np.array_equal(touched, inrow):
        raise ValueError('BLOCK_ROW_SET_MISMATCH')
    # (3) zero cost on the block (solver cost and scientific cost)
    if np.any(np.asarray(a['cost'])[cols] != 0) or np.any(np.asarray(a['cost_scientific'])[cols] != 0):
        raise ValueError('BLOCK_COST_NONZERO')
    # (4) block primal residual on block rows and block column bounds (binary64 evaluation)
    x = np.zeros(n); x[cols] = xb
    sel = incol[colof]
    act = np.zeros(m); np.add.at(act, index[sel], value[sel] * x[colof[sel]])
    mag = np.zeros(m); np.add.at(mag, index[sel], np.abs(value[sel] * x[colof[sel]]))
    lo = np.asarray(a['row_lower'])[rows]; hi = np.asarray(a['row_upper'])[rows]
    v = np.maximum(np.where(np.isfinite(lo), lo - act[rows], 0), np.where(np.isfinite(hi), act[rows] - hi, 0))
    tol = 1e-12 * np.maximum(1.0, mag[rows])
    if np.any(v > tol):
        raise ValueError('BLOCK_PRIMAL_RESIDUAL %g' % float(v.max()))
    cl = np.asarray(a['col_lower'])[cols]; cu = np.asarray(a['col_upper'])[cols]
    if np.any(xb < cl) or np.any(xb > cu):
        raise ValueError('BLOCK_COLUMN_BOUNDS')
    return {'status': 'BLOCK_DECOUPLED_ZERO_COST_FEASIBLE', 'cross_entries': 0,
            'block_columns': int(len(cols)), 'block_rows': int(len(rows)),
            'block_binary64_max_row_violation_LP_units': float(v.max(initial=0.0)),
            'block_column_index_sha256': arr_sha(cols), 'block_row_index_sha256': arr_sha(rows)}


def main_problem(meta, a, cols, rows):
    """Pure restriction of the frozen CSC to main rows/columns. Values bit-identical."""
    n, m = meta['num_col'], meta['num_row']
    keepc = np.ones(n, bool); keepc[cols] = False
    keepr = np.ones(m, bool); keepr[rows] = False
    mc = np.flatnonzero(keepc); mr = np.flatnonzero(keepr)
    rowmap = np.full(m, -1, np.int64); rowmap[mr] = np.arange(len(mr))
    start = np.asarray(a['start'], np.int64); index = np.asarray(a['index']); value = np.asarray(a['value'])
    counts = np.diff(start)[mc]
    sel = np.repeat(keepc, np.diff(start))
    new_index = rowmap[index[sel]]
    if np.any(new_index < 0):
        raise ValueError('MAIN_COLUMN_REFERENCES_BLOCK_ROW')
    out = {
        'start': np.concatenate([[0], np.cumsum(counts)]).astype(np.int64),
        'index': new_index.astype(np.int32),
        'value': np.ascontiguousarray(value[sel], dtype=np.float64),
        'cost': np.ascontiguousarray(np.asarray(a['cost'])[mc]),
        'col_lower': np.ascontiguousarray(np.asarray(a['col_lower'])[mc]),
        'col_upper': np.ascontiguousarray(np.asarray(a['col_upper'])[mc]),
        'row_lower': np.ascontiguousarray(np.asarray(a['row_lower'])[mr]),
        'row_upper': np.ascontiguousarray(np.asarray(a['row_upper'])[mr]),
    }
    mmeta = {'num_col': int(len(mc)), 'num_row': int(len(mr)), 'nnz': int(len(out['value'])),
             'sense': meta['sense'], 'offset': meta['offset'], 'derivation': 'C09 restriction of frozen C03 CSC'}
    ident = {k: arr_sha(v) for k, v in out.items()}
    ident.update(main_columns_sha256=arr_sha(mc), main_rows_sha256=arr_sha(mr))
    return mmeta, out, mc, mr, ident


def merge(raw_folder, dest, meta, cols, rows, xb, mc, mr, native_status):
    """Full-length C03-coordinate vectors: main solver output + exact block primal + zero block duals."""
    raw_folder = Path(raw_folder); dest = Path(dest)
    if dest.exists():
        raise ValueError('merge destination must be new')
    (dest / 'vectors').mkdir(parents=True)
    rec = json.loads((raw_folder / 'RAW_RECEIPT.json').read_text())
    if any(rec['vectors'].get(k, {}).get('status') != 'SAVED_UNQUALIFIED' for k in ('X', 'Pi', 'RC')):
        raise ValueError('MAIN_RAW_INCOMPLETE')
    out = {'qualification': 'DERIVED_UNQUALIFIED_MERGE_NOT_NATIVE_OUTPUT', 'native_status': native_status,
           'vectors': {}, 'basis': 'NOT_REQUESTED',
           'source_native_receipt_sha256': sha(raw_folder / 'RAW_RECEIPT.json'),
           'block_primal_sha256': arr_sha(xb), 'block_duals': 'EXACT_ZERO',
           'main_vectors_copied_bitwise': True}
    for name, length, idx, block_value in [('X', meta['num_col'], mc, xb), ('Pi', meta['num_row'], mr, 0.0),
                                           ('RC', meta['num_col'], mc, 0.0)]:
        src = raw_folder / (name + '.npy')
        if sha(src) != rec['vectors'][name]['sha256']:
            raise ValueError('MAIN_RAW_SHA ' + name)
        v = np.load(src)
        if len(v) != len(idx):
            raise ValueError('MAIN_RAW_LENGTH ' + name)
        full = np.zeros(length)
        full[idx] = v
        if name == 'X':
            full[cols] = xb
        elif name == 'Pi':
            full[rows] = 0.0
        else:
            full[cols] = 0.0
        if not np.array_equal(full[idx].view('u8'), v.view('u8')):
            raise ValueError('MAIN_COPY_NOT_BITWISE')
        p = dest / 'vectors' / (name + '.npy')
        np.save(p, full)
        out['vectors'][name] = {'status': 'SAVED_UNQUALIFIED', 'sha256': sha(p), 'count': int(length),
                                'derivation': 'main native + block exact'}
    (dest / 'vectors' / 'RAW_RECEIPT.json').write_text(json.dumps(out, indent=2) + '\n')
    return out
