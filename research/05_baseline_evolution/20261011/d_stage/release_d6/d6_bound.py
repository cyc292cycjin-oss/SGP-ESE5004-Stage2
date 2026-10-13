"""D-6（DR1）：2920 主 LP 的严格下界（只读，不调用求解器）。由 work/c10_rigorous_bound_20261013/methods/c10_bound.py 参数化而来。

与 C10 的差别（其余公式、外向舍入与安全余量不变）：
  * 路径与维度全部为参数；块的列/行来自 D-2（SHA 绑定），向量来自 D-5 合并向量（SHA 绑定）。
  * 储能伸缩求和：先逐行核对能量平衡行无损（a_prev == -a_e、a_e/a_p 与 rhs 在时间上恒定、t>=1 时 rhs=0），
    权重 k = a_e/a_p 从实际系数读出（不硬编码 24 或 3）。任何有成本储能不满足无损条件 -> 不使用伸缩求和，结论为
    TELESCOPING_NOT_APPLICABLE 并报告（按 D 指令）。非循环储能另外核对成本符号对应的 e_T 方向界。
  * 每列族名称来自 D-1 的 LABELS.json。
Usage: python d6_bound.py <d1 run> <d5 run> <d2 block dir> <out dir> <delta_rel> [<delta_rel> ...]
"""
import sys, json, math, time, bisect, hashlib, collections
from pathlib import Path
import numpy as np, scipy.sparse as sp

D1, D5, BLK, OUT = map(Path, sys.argv[1:5]); DELTAS = [float(x) for x in sys.argv[5:]]
EPS = np.finfo(float).eps; t0 = time.time(); OUT.mkdir(parents=True, exist_ok=False)
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 23), b''): h.update(b)
    return h.hexdigest()
def put(name, v): (OUT / name).write_text(json.dumps(v, indent=1, default=float) + '\n')
status = {'phase': 'START', 'solver_calls': 0}
def stage(s): status.update(phase=s, elapsed=time.time() - t0); put('D6_STATUS.json', status)

# ---- inputs (SHA-bound) ----
MP = D1 / 'bridge/math_problem'; meta = json.loads((MP / 'MATH_PROBLEM.json').read_text())
arr = {}
for k, it in meta['arrays'].items():
    p = MP / it['file']; assert sha(p) == it['sha256'], k; arr[k] = np.load(p)
n, m = meta['num_col'], meta['num_row']; off = float(meta['offset'])
A = sp.csc_matrix((arr['value'], arr['index'], arr['start']), shape=(m, n))
rl, ru, c, lb, ub = arr['row_lower'], arr['row_upper'], arr['cost'], arr['col_lower'], arr['col_upper']
mrec = json.loads((D5 / 'merged_for_V4/vectors/RAW_RECEIPT.json').read_text())
x = np.load(D5 / 'merged_for_V4/vectors/X.npy'); y = np.load(D5 / 'merged_for_V4/vectors/Pi.npy')
assert sha(D5 / 'merged_for_V4/vectors/X.npy') == mrec['vectors']['X']['sha256'] and sha(D5 / 'merged_for_V4/vectors/Pi.npy') == mrec['vectors']['Pi']['sha256']
brec = json.loads((BLK / 'BLOCK_RECEIPT.json').read_text())
for f, h in brec['files'].items(): assert sha(BLK / f) == h, f
S = np.zeros(n, bool); S[np.load(BLK / 'BLOCK_COLUMNS.npy')] = True; Sr = np.zeros(m, bool); Sr[np.load(BLK / 'BLOCK_ROWS.npy')] = True
MM = json.loads((D1 / 'bridge/mapping/MAPPING_MANIFEST.json').read_text()); starts = [r['start'] for r in MM['row_ranges']]
def rowfam(i): return MM['row_ranges'][bisect.bisect_right(starts, i) - 1]['family']
vl = np.load(D1 / 'bridge/mapping/vlabels.npy'); assert np.all(np.diff(vl) > 0)
LB = json.loads((D1 / 'artifacts/mapping/LABELS.json').read_text())
names = [v['name'] for v in LB['variables']]; colfam = np.full(n, -1, np.int32); storecols = collections.defaultdict(dict)
for k, v in enumerate(LB['variables']):
    lab = np.load(D1 / 'artifacts/mapping' / v['labels_file']); flat = lab.ravel(); ok = flat >= 0
    pos = np.searchsorted(vl, flat[ok]); assert np.array_equal(vl[pos], flat[ok]); colfam[pos] = k
    if v['name'] in ('Store-p', 'Store-e', 'Store-e_nom'):
        dims = v['dims']; co = v['coordinates']; idxs = np.argwhere(lab >= 0)
        for (ii, p) in zip(idxs, pos):
            if len(dims) == 2:
                sd = dims.index('snapshot'); nm = co[dims[1 - sd]][ii[1 - sd]]; t = int(ii[sd]); storecols[nm][(v['name'], t)] = int(p)
            else: storecols[co[dims[0]][ii[0]]][('e_nom', None)] = int(p)
assert (colfam >= 0).all()
stage('INPUTS_SHA_PASS')

Mc = ~S; Mr = ~Sr; midx = np.flatnonzero(Mc); pos_of = np.full(n, -1, np.int64); pos_of[midx] = np.arange(len(midx))
Am = A[Mr][:, Mc].tocsc(); xm, ym, cm = x[Mc], y[Mr], c[Mc]; rlm, rum = rl[Mr].copy(), ru[Mr].copy(); L0 = lb[Mc].copy(); U0 = ub[Mc].copy()
P = math.fsum(cm * xm) + off
Rf = A.tocsr()
def row_entries(i): return {int(k): float(v) for k, v in zip(Rf.indices[Rf.indptr[i]:Rf.indptr[i + 1]], Rf.data[Rf.indptr[i]:Rf.indptr[i + 1]])}
stage('MAIN_LP_EXTRACTED')

# ---- exact storage aggregation with explicit lossless verification ----
g = cm.copy(); rhs_adj = 0.0; log = []; lossy = []; unsupported = []
for nm, d in storecols.items():
    if ('Store-p', 0) not in d: continue
    if S[d[('Store-p', 0)]]: continue                      # block store (zero cost, exact certificate)
    T = max(t for (v, t) in d if v == 'Store-p')
    pcols = [d[('Store-p', t)] for t in range(T + 1)]; ecols = [d[('Store-e', t)] for t in range(T + 1)]
    cs = float(c[pcols[0]])
    if not all(float(c[j]) == cs for j in pcols): unsupported.append((nm, 'NONCONSTANT_STORE_P_COST')); continue
    for j in pcols: g[pos_of[j]] = 0.0
    if cs == 0: continue
    ae = ap = None; rhs0 = None; cyclic = None; ok = True
    for t in range(T + 1):
        e, p = ecols[t], pcols[t]
        cand = [i for i in A.indices[A.indptr[p]:A.indptr[p + 1]] if rowfam(i) == 'Store-energy_balance' and e in row_entries(i)]
        if len(cand) != 1 or rl[cand[0]] != ru[cand[0]]: ok = False; break
        ent = row_entries(cand[0]); prev = ecols[t - 1] if t > 0 else ecols[T]
        if t == 0:
            cyclic = prev in ent and len(ent) == 3
            if not cyclic and len(ent) != 2: ok = False; break
            rhs0 = float(rl[cand[0]]); ae, ap = ent[e], ent[p]
            if cyclic and (ent[prev] != -ae or rhs0 != 0): lossy.append(nm); ok = False; break
        else:
            if set(ent) != {e, p, prev} or ent[e] != ae or ent[p] != ap or ent[prev] != -ae or rl[cand[0]] != 0: lossy.append(nm); ok = False; break
    if not ok:
        if nm not in lossy: unsupported.append((nm, 'ENERGY_ROW_SHAPE')); continue
        continue
    k = ae / ap
    if cyclic: log.append((nm, 'cyclic', cs, k)); continue      # sum_t p_t = 0 exactly
    einit = rhs0 / ae; eT = ecols[T]
    # c_s * sum_t p_t = c_s*k*(e_init - e_T); need the bound on e_T matching sign(c_s*k)
    coef = cs * k                                               # objective part = coef*e_init - coef*e_T
    if ('e_nom', None) in d and coef > 0:
        # e_T <= e_nom (Store-ext-e-upper with e_max_pu = 1 verified below) -> -coef*e_T >= -coef*e_nom
        rows_T = [i for i in A.indices[A.indptr[eT]:A.indptr[eT + 1]] if rowfam(i) == 'Store-ext-e-upper']
        en = d[('e_nom', None)]; okrow = len(rows_T) == 1 and row_entries(rows_T[0]) == {eT: 1.0, en: -1.0} and ru[rows_T[0]] == 0
        if not okrow: unsupported.append((nm, 'EXT_UPPER_ROW_SHAPE')); continue
        g[pos_of[en]] -= coef; rhs_adj += coef * einit; log.append((nm, 'ext', cs, k))
    elif coef > 0:
        emax = float(ub[eT]) if np.isfinite(ub[eT]) else None
        if emax is None:
            ups = [ru[i] for i in A.indices[A.indptr[eT]:A.indptr[eT + 1]] if rowfam(i) == 'Store-fix-e-upper' and row_entries(i) == {eT: 1.0}]
            if len(ups) != 1: unsupported.append((nm, 'NO_FIXED_E_UPPER')); continue
            emax = float(ups[0])
        rhs_adj += coef * (einit - emax); log.append((nm, 'fixed', cs, k))
    else:
        emin = float(lb[eT]) if np.isfinite(lb[eT]) else None
        if emin is None:
            los = [rl[i] for i in A.indices[A.indptr[eT]:A.indptr[eT + 1]] if rowfam(i) in ('Store-fix-e-lower', 'Store-ext-e-lower') and row_entries(i) == {eT: 1.0}]
            if len(los) != 1: unsupported.append((nm, 'NO_E_LOWER_FOR_NEGATIVE_COST')); continue
            emin = float(los[0])
        rhs_adj += coef * (einit - emin); log.append((nm, 'fixed_lower', cs, k))
agg = {'stores_aggregated': dict(collections.Counter(s[1] for s in log)), 'weights_k_seen': sorted({s[3] for s in log}), 'lossy_stores': lossy, 'unsupported': unsupported}
put('D6_STORAGE_AGGREGATION.json', agg); stage('STORAGE_AGGREGATION')
results = {}
if lossy or unsupported:
    results['status'] = 'TELESCOPING_NOT_APPLICABLE'
    put('D6_BOUND_SUMMARY.json', {'status': 'TELESCOPING_NOT_APPLICABLE', 'aggregation': agg, 'solver_calls': 0}); stage('DONE'); sys.exit(0)

gl, gu = np.isfinite(rlm), np.isfinite(rum)
yy = ym.copy(); wrong = ((yy > 0) & ~gl) | ((yy < 0) & ~gu); yy[wrong] = 0.0
r = cm - Am.T @ yy
err = 4 * EPS * (np.abs(cm) + abs(Am).T @ np.abs(yy)) * (np.diff(Am.indptr) + 2)
rlo, rhi = r - err, r + err
rowterm = np.where(yy > 0, yy * np.where(gl, rlm, 0), np.where(yy < 0, yy * np.where(gu, rum, 0), 0.0))
def minprod(r1, r2, l, u):
    c1 = np.where(np.isfinite(l), r1 * l, np.where(r1 > 0, -np.inf, np.where(r1 < 0, np.inf, 0))); c2 = np.where(np.isfinite(u), r1 * u, np.where(r1 > 0, np.inf, np.where(r1 < 0, -np.inf, 0)))
    c3 = np.where(np.isfinite(l), r2 * l, np.where(r2 > 0, -np.inf, np.where(r2 < 0, np.inf, 0))); c4 = np.where(np.isfinite(u), r2 * u, np.where(r2 > 0, np.inf, np.where(r2 < 0, -np.inf, 0)))
    return np.minimum(np.minimum(c1, c2), np.minimum(c3, c4))
def outward_lo(v, scale): return v - (1e-9 * np.abs(v) + 1e-9 * scale + 1e-300)
def outward_hi(v, scale): return v + (1e-9 * np.abs(v) + 1e-9 * scale + 1e-300)
summary = {'P_hat_EUR': P, 'aggregation': agg, 'wrong_sign_duals_zeroed': int(wrong.sum()), 'main_columns': int(len(midx)), 'main_rows': int(Mr.sum()), 'deltas': {}}
for DELTA in DELTAS:
    Ucut = P + DELTA * abs(P); agg_rhs = (Ucut - off) - rhs_adj; agg_rhs = agg_rhs + 1e-9 * abs(agg_rhs)
    R = sp.vstack([Am.tocsr(), sp.csr_matrix(cm.reshape(1, -1)), sp.csr_matrix(g.reshape(1, -1))]).tocsr()
    rlx = np.append(rlm, [-np.inf, -np.inf]); rux = np.append(rum, [Ucut - off, agg_rhs]); nr = R.shape[0]
    rows = np.repeat(np.arange(nr), np.diff(R.indptr)); cols = R.indices; a = R.data; L, U = L0.copy(), U0.copy(); hist = []
    for it in range(40):
        lo_c = np.where(a > 0, a * L[cols], a * U[cols]); hi_c = np.where(a > 0, a * U[cols], a * L[cols])
        lo_inf = ~np.isfinite(lo_c); hi_inf = ~np.isfinite(hi_c); lo_f = np.where(lo_inf, 0, lo_c); hi_f = np.where(hi_inf, 0, hi_c); del lo_c, hi_c
        rmin = np.bincount(rows, lo_f, nr); rmax = np.bincount(rows, hi_f, nr); nlo = np.bincount(rows, lo_inf, nr); nhi = np.bincount(rows, hi_inf, nr)
        rabs = np.bincount(rows, np.abs(lo_f) + np.abs(hi_f), nr)
        o_min = np.where(lo_inf, np.where(nlo[rows] == 1, rmin[rows], np.nan), np.where(nlo[rows] == 0, rmin[rows] - lo_f, np.nan))
        o_max = np.where(hi_inf, np.where(nhi[rows] == 1, rmax[rows], np.nan), np.where(nhi[rows] == 0, rmax[rows] - hi_f, np.nan)); del lo_f, hi_f, lo_inf, hi_inf
        sc = rabs[rows] / np.abs(a); newU = np.full(len(a), np.inf); newL = np.full(len(a), -np.inf)
        ok = np.isfinite(rux[rows]) & np.isfinite(o_min); v = (rux[rows] - o_min) / a; pos = ok & (a > 0); neg = ok & (a < 0)
        newU[pos] = outward_hi(v[pos], sc[pos]); newL[neg] = outward_lo(v[neg], sc[neg])
        ok2 = np.isfinite(rlx[rows]) & np.isfinite(o_max); v2 = (rlx[rows] - o_max) / a; pos2 = ok2 & (a > 0); neg2 = ok2 & (a < 0)
        newL[pos2] = np.maximum(newL[pos2], outward_lo(v2[pos2], sc[pos2])); newU[neg2] = np.minimum(newU[neg2], outward_hi(v2[neg2], sc[neg2]))
        del o_min, o_max, v, v2, sc
        Unew = U.copy(); Lnew = L.copy(); np.minimum.at(Unew, cols, newU); np.maximum.at(Lnew, cols, newL); del newU, newL
        cross = (Lnew > Unew + 1e-6 * (1 + np.abs(Unew))); impU = np.sum(Unew < U * (1 - 1e-6) - 1e-9); impL = np.sum(Lnew > L * (1 + 1e-6) + 1e-9)
        U, L = Unew, Lnew
        hist.append({'it': it, 'finite_U': int(np.isfinite(U).sum()), 'finite_L': int(np.isfinite(L).sum()), 'improved': int(impU + impL), 'crossings': int(cross.sum())}); stage(f'FBBT_delta{DELTA:g}_it{it}')
        if impU + impL == 0: break
    with np.errstate(invalid='ignore'): colterm = minprod(rlo, rhi, L, U)
    colterm = np.where(np.isnan(colterm), 0.0, colterm); bad = np.isneginf(colterm)
    res = {'assumption_H': f'optimal objective <= U = P_hat*(1+{DELTA})', 'U_EUR': Ucut, 'propagation_history': hist,
           'columns_with_minus_inf_contribution': int(bad.sum()), 'bad_by_family': dict(collections.Counter(names[k] for k in colfam[Mc][bad])),
           'xhat_outside_bounds_max': float(max(np.max(np.where(np.isfinite(L), L - xm, 0)), np.max(np.where(np.isfinite(U), xm - U, 0))))}
    if not bad.any():
        terms = np.concatenate([colterm, rowterm]); safety = EPS * 4 * math.fsum(np.abs(terms)) + EPS * abs(off)
        Lb = math.fsum(terms) + off - safety
        res.update({'rigorous_lower_bound_EUR': Lb, 'gap_EUR': P - Lb, 'relative_gap': (P - Lb) / abs(P), 'summation_safety_EUR': safety,
                    'colterm_sum': math.fsum(colterm), 'rowterm_sum': math.fsum(rowterm)})
        top = np.argsort(colterm - r * xm)[:5]
        res['largest_negative_colterms'] = [{'family': names[colfam[midx[j]]], 'r_interval': [float(rlo[j]), float(rhi[j])], 'L': float(L[j]), 'U': float(U[j]), 'term': float(colterm[j] - r[j] * xm[j])} for j in top]
    summary['deltas'][str(DELTA)] = res; put(f'D6_BOUND_delta{DELTA:g}.json', res)
    np.savez_compressed(OUT / f'd6_bounds_delta{DELTA:g}.npz', L=L, U=U)
summary.update(status='DONE', seconds=time.time() - t0, solver_calls=0, inputs={'math_problem_manifest_sha256': sha(MP / 'MATH_PROBLEM.json'), 'merged_receipt_sha256': sha(D5 / 'merged_for_V4/vectors/RAW_RECEIPT.json'), 'block_receipt_sha256': sha(BLK / 'BLOCK_RECEIPT.json')})
put('D6_BOUND_SUMMARY.json', summary); stage('DONE')
