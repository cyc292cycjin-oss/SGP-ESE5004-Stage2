"""Generic exact-block tools for any snapshot resolution (365 daily or 2920 x 3h).

Read-only on the frozen CSC. No solver. Steps:
  1. identify_block(): fixed-resource Stores + their final-energy meters, from labels; verify
     closure (no row mixes block/non-block columns) and zero cost (solver + scientific).
  2. build_block_primal(): exact-rational greedy feasible point using the ACTUAL CSC coefficients
     (energy-balance weights, meter/bus coefficients, load RHS), then rounded to binary64
     (rounding down where it matters), and verified row-by-row in exact rationals.
Usage:
  python block_tools.py <math_problem_dir> <mapping_dir_with_vlabels> <labels_dir> <out_dir>
"""
import sys, json, hashlib, time, collections
from pathlib import Path
from fractions import Fraction as F
import numpy as np, scipy.sparse as sp


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest()


def arr_sha(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def load_problem(d):
    d = Path(d); meta = json.loads((d / 'MATH_PROBLEM.json').read_text(encoding='utf-8-sig'))
    a = {}
    for k, it in meta['arrays'].items():
        p = d / it['file']
        if sha(p) != it['sha256']: raise ValueError('SHA mismatch ' + k)
        a[k] = np.load(p)
    A = sp.csc_matrix((a['value'], a['index'], a['start']), shape=(meta['num_row'], meta['num_col']))
    return meta, a, A


def column_info(mapping_dir, labels_dir):
    vl = np.load(Path(mapping_dir) / 'vlabels.npy')
    LB = json.loads((Path(labels_dir) / 'LABELS.json').read_text())
    lab2 = {}
    for v in LB['variables']:
        lab = np.load(Path(labels_dir) / v['labels_file']); dims = v['dims']; co = v['coordinates']
        for idx, l in np.ndenumerate(lab):
            if l < 0: continue
            if len(dims) == 2:
                sd = dims.index('snapshot'); other = dims[1 - sd]
                lab2[int(l)] = (v['name'], co[other][idx[1 - sd]], idx[sd])
            elif len(dims) == 1: lab2[int(l)] = (v['name'], co[dims[0]][idx[0]], None)
            else: lab2[int(l)] = (v['name'], None, None)
    return [lab2[int(l)] for l in vl]


def identify_block(A, a, ci):
    n = A.shape[1]
    stores = {nm for (v, nm, t) in ci if v in ('Store-e', 'Store-p') and nm and nm.endswith('fixed resource')}
    meters = {s.replace('fixed resource', 'final-energy meter') for s in stores}
    S = np.array([(nm in stores and v in ('Store-e', 'Store-p')) or (nm in meters and v in ('Link-p', 'Link-p_nom')) for (v, nm, t) in ci])
    cols = np.flatnonzero(S)
    R = A.tocsr()
    rows = np.unique(A[:, cols].indices)
    inrows = np.zeros(A.shape[0], bool); inrows[rows] = True
    colof = np.repeat(np.arange(n), np.diff(A.indptr))
    cross = int(np.sum(S[colof] != inrows[A.indices]))
    zero_cost = bool(np.all(a['cost'][cols] == 0) and np.all(a['cost_scientific'][cols] == 0))
    met_found = len({ci[j][1] for j in cols if ci[j][0] == 'Link-p'})
    rec = {'stores': len(stores), 'meters_found': met_found, 'block_columns': int(len(cols)), 'block_rows': int(len(rows)),
           'cross_entries': cross, 'zero_cost': zero_cost,
           'block_column_index_sha256': arr_sha(cols.astype(np.int64)), 'block_row_index_sha256': arr_sha(rows.astype(np.int64))}
    if cross or not zero_cost or met_found != len(stores):
        raise ValueError('BLOCK_NOT_DECOUPLED_OR_NOT_ZERO_COST ' + json.dumps(rec))
    return cols, rows, rec


def build_block_primal(A, a, ci, cols, rows):
    """Greedy exact construction; coefficients are read from the CSC, nothing is hard-coded."""
    R = A.tocsr(); rl, ru = a['row_lower'], a['row_upper']
    col = {ci[j]: j for j in cols}
    stores = sorted({ci[j][1] for j in cols if ci[j][0] == 'Store-e'})
    T = 1 + max(ci[j][2] for j in cols if ci[j][0] == 'Store-p')
    meter = lambda s: s.replace('fixed resource', 'final-energy meter')
    def row_entries(i): return {int(k): F(float(v)) for k, v in zip(R.indices[R.indptr[i]:R.indptr[i + 1]], R.data[R.indptr[i]:R.indptr[i + 1]])}
    def rows_of(j): return A.indices[A.indptr[j]:A.indptr[j + 1]]
    # energy rows per store: e_t row containing e_t, p_t (and e_{t-1} for t>0)
    energy = {}; bus = {}; init = {}
    for s in stores:
        for t in range(T):
            e, p = col[('Store-e', s, t)], col[('Store-p', s, t)]
            cand = [i for i in rows_of(p) if e in row_entries(i) and rl[i] == ru[i]]
            if len(cand) != 1: raise ValueError('ENERGY_ROW_AMBIGUOUS %s %d' % (s, t))
            ent = row_entries(cand[0]); prev = col[('Store-e', s, t - 1)] if t > 0 else None
            if t == 0 and len(ent) != 2: raise ValueError('CYCLIC_OR_UNEXPECTED_INITIAL_ROW ' + s)
            if t > 0 and set(ent) != {e, p, prev}: raise ValueError('ENERGY_ROW_SHAPE %s %d' % (s, t))
            energy[(s, t)] = (ent, F(float(rl[cand[0]])))
            m = col[('Link-p', meter(s), t)]
            cb = [i for i in rows_of(p) if set(row_entries(i)) == {p, m} and rl[i] == ru[i] == 0]
            if len(cb) != 1: raise ValueError('BUS_ROW ' + s)
            ent2 = row_entries(cb[0]); bus[(s, t)] = -ent2[p] / ent2[m]   # m = ratio * p
    # load rows: equality rows with nonzero RHS containing only meter Link-p columns
    groups = collections.defaultdict(dict)
    for i in rows:
        if rl[i] != ru[i] or rl[i] == 0: continue
        ent = row_entries(i)
        if not all(ci[k][0] == 'Link-p' and ci[k][1].endswith('final-energy meter') for k in ent): continue
        t = ci[next(iter(ent))][2]
        key = tuple(sorted(ci[k][1] for k in ent))
        groups[key][t] = (ent, F(float(rl[i])))
    x = {}
    for g, byt in groups.items():
        accs = [m.replace('final-energy meter', 'fixed resource') for m in g]
        # initial inventory from t=0 row: a_e*e0 + a_p*p0 = rhs  -> e0 = (rhs - a_p p0)/a_e ; inventory with p=0:
        inv = {}
        for s in accs:
            ent, rhs = energy[(s, 0)]; ae = ent[col[('Store-e', s, 0)]]
            inv[s] = rhs / ae
        for t in range(T):
            ent_load, d = byt[t]
            need = d   # in "sum of coeff*m" units
            for k, s in enumerate(accs):
                ps, ms, es = col[('Store-p', s, t)], col[('Link-p', meter(s), t)], col[('Store-e', s, t)]
                entE, rhsE = energy[(s, t)]; ae, ap = entE[es], entE[ps]
                # e_t = (rhs - ap*p - a_prev*e_prev)/ae ; with e_prev=inv (t>0) or rhs-only (t=0)
                base = rhsE if t == 0 else rhsE - entE[col[('Store-e', s, t - 1)]] * inv[s]
                # e_t >= 0  ->  p <= base/ap if (-ap/ae)>0 ... solve e_t(p) = (base - ap p)/ae >= 0
                slope = -ap / ae; e0 = base / ae          # e_t = e0 + slope*p
                pmax = (e0 / -slope) if slope < 0 else None
                cm = ent_load[ms] * bus[(s, t)]             # load-row contribution per unit p
                last = (k == len(accs) - 1)
                take = need / cm if last else (min(need / cm, pmax) if pmax is not None else need / cm)
                if not last:
                    tf = float(take)
                    if F(tf) > take: tf = float(np.nextafter(tf, -np.inf))
                    take = F(max(tf, 0.0))
                pf = float(take); x[ps] = pf
                mf = float(F(pf) * bus[(s, t)]); x[ms] = mf
                need -= ent_load[ms] * F(mf)
                inv[s] = e0 + slope * F(pf); x[es] = float(inv[s])
        for s in accs:
            mn = col[('Link-p_nom', meter(s), None)]
            x[mn] = max(x[col[('Link-p', meter(s), t)]] for t in range(T))
    if len(x) != len(cols): raise ValueError('BLOCK_PRIMAL_INCOMPLETE %d/%d' % (len(x), len(cols)))
    xb = np.array([x[j] for j in cols])
    # exact verification on every block row
    xf = dict(zip(cols.tolist(), xb.tolist())); worst = F(0); nviol = 0; scale = F(0)
    for i in rows:
        ent = row_entries(i); act = sum(c * F(xf[k]) for k, c in ent.items())
        v = F(0)
        if np.isfinite(rl[i]) and act < F(float(rl[i])): v = F(float(rl[i])) - act
        if np.isfinite(ru[i]) and act > F(float(ru[i])): v = max(v, act - F(float(ru[i])))
        if v > 0: nviol += 1; worst = max(worst, v)
    return xb, {'groups': len(groups), 'snapshots': T, 'rows_with_nonzero_exact_violation': nviol,
                'max_exact_violation_LP_units': float(worst)}


if __name__ == '__main__':
    mp, mapping, labels, out = sys.argv[1:5]; out = Path(out); out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    meta, a, A = load_problem(mp); ci = column_info(mapping, labels)
    cols, rows, rec = identify_block(A, a, ci); print(json.dumps(rec), flush=True)
    xb, vr = build_block_primal(A, a, ci, cols, rows)
    np.save(out / 'BLOCK_COLUMNS.npy', cols.astype(np.int64)); np.save(out / 'BLOCK_ROWS.npy', rows.astype(np.int64)); np.save(out / 'BLOCK_PRIMAL.npy', xb)
    rec.update(vr, seconds=time.time() - t0, files={f: sha(out / f) for f in ['BLOCK_COLUMNS.npy', 'BLOCK_ROWS.npy', 'BLOCK_PRIMAL.npy']},
               source_manifest_sha256=sha(Path(mp) / 'MATH_PROBLEM.json'), block_duals='exactly 0')
    (out / 'BLOCK_RECEIPT.json').write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec, indent=1))
