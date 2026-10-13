"""D-5 本地只读复核（不调用求解器、不构建模型；由 c09_local_v4_recheck.py 改写为 2920）。

在 WSL pypsa-earth 环境（numpy 1.26.4 / scipy 1.15.2，与云端一致）中运行：
    python d5_local_v4_recheck.py <解压的 D5 发布包> <本地 cloud_run> <inputs_readonly_copy> <输出 json>

1. 用本地 SHA 核验过的 D-1 冻结 CSC 重新推导主 LP 限制，并与云端身份回执比对。
2. 在本地重新运行发布包的块校验（解耦、零成本、块可行性）。
3. 用独立于 d5_decompose.merge 的代码逐位核对合并结果。
4. 用普通 numpy 计算主 LP 在原生坐标下的残差（不走 V4 代码路径）。
5. 对合并向量重新运行原样的 V4 代数（complete_kkt），与云端 KKT.json 比对。
"""
import sys, json, time, tempfile, shutil
from pathlib import Path
import numpy as np

REL, RUN, INP, OUT = map(Path, sys.argv[1:5])
EXP = json.loads((REL / 'D5_EXPECTED.json').read_text())
LOC = Path(tempfile.mkdtemp(prefix='d5rc_')) / 'rel'; shutil.copytree(REL, LOC)
EXP_LOCAL = dict(EXP, block_dir=str(INP / 'd2_block')); (LOC / 'D5_EXPECTED.json').write_text(json.dumps(EXP_LOCAL))
sys.path.insert(0, str(LOC)); sys.path.insert(0, str(LOC / 'helpers'))
from adapter import open_problem
from d5_decompose import load_block, verify_block, main_problem
from v4_algebra_extracted import complete_kkt

t0 = time.time(); res = {'qualification': 'LOCAL_READ_ONLY_RECHECK_NO_SOLVER', 'run_id': RUN.parent.name, 'block_dir_local_copy_of': EXP['block_dir']}
BR = INP / 'd1' / 'bridge'
meta, a = open_problem(BR / 'math_problem', verify=True)
D = np.load(BR / 'mapping/D.npy', mmap_mode='r'); R = np.load(BR / 'mapping/R.npy', mmap_mode='r')
rec, cols, rows, xb = load_block()
mmeta, ma, mc, mr, ident = main_problem(meta, a, cols, rows)
cloud_id = json.loads((RUN / 'D5_MAIN_PROBLEM_IDENTITY.json').read_text())
res['main_identity'] = {'dims': [mmeta['num_col'], mmeta['num_row'], mmeta['nnz']], 'all_array_sha_match_cloud': ident == cloud_id['arrays_sha256'],
                        'main_columns_file_match': bool(np.array_equal(np.load(RUN / 'D5_MAIN_COLUMNS.npy'), mc)),
                        'main_rows_file_match': bool(np.array_equal(np.load(RUN / 'D5_MAIN_ROWS.npy'), mr))}
print('identity', res['main_identity'], flush=True)
res['block'] = verify_block(meta, a, cols, rows, xb)
res['block']['partition'] = bool(len(np.intersect1d(cols, mc)) == 0 and len(cols) + len(mc) == meta['num_col'] and len(np.intersect1d(rows, mr)) == 0 and len(rows) + len(mr) == meta['num_row'])
print('block', res['block']['status'], flush=True)
raw = {k: np.load(RUN / 'raw/vectors' / (k + '.npy')) for k in ('X', 'Pi', 'RC')}
mer = {k: np.load(RUN / 'merged_for_V4/vectors' / (k + '.npy'), mmap_mode='r') for k in ('X', 'Pi', 'RC')}
bits = lambda v: np.ascontiguousarray(v).view('u8')
res['merge'] = {'X_main_bitwise': bool(np.array_equal(bits(mer['X'][mc]), bits(raw['X']))), 'Pi_main_bitwise': bool(np.array_equal(bits(mer['Pi'][mr]), bits(raw['Pi']))),
                'RC_main_bitwise': bool(np.array_equal(bits(mer['RC'][mc]), bits(raw['RC']))), 'X_block_equals_prebuilt_primal': bool(np.array_equal(bits(mer['X'][cols]), bits(xb))),
                'Pi_block_all_zero': bool(not np.asarray(mer['Pi'][rows]).any()), 'RC_block_all_zero': bool(not np.asarray(mer['RC'][cols]).any())}
print('merge', res['merge'], flush=True)
x, pi, rc = raw['X'], raw['Pi'], raw['RC']; st, ix, va = ma['start'], ma['index'], ma['value']
colof = np.repeat(np.arange(mmeta['num_col'], dtype=np.int64), np.diff(st))
act = np.bincount(ix, weights=va * x[colof], minlength=mmeta['num_row']); lo, hi = ma['row_lower'], ma['row_upper']
rv = np.maximum(np.where(np.isfinite(lo), lo - act, 0), np.where(np.isfinite(hi), act - hi, 0)); del act
cv = np.maximum(np.where(np.isfinite(ma['col_lower']), ma['col_lower'] - x, 0), np.where(np.isfinite(ma['col_upper']), x - ma['col_upper'], 0))
aty = np.bincount(colof, weights=va * pi[ix], minlength=mmeta['num_col']); del colof
stat = np.abs(ma['cost'] - aty - rc)
res['main_native_plain'] = {'row_violation_max': float(rv.max()), 'column_violation_max': float(cv.max()), 'stationarity_abs_max_native': float(stat.max()),
                            'objective_cTx_plus_offset': float(ma['cost'] @ x + meta['offset'])}
print('plain', res['main_native_plain'], flush=True)
del ma, rv, cv, aty, stat
d = tempfile.mkdtemp(dir=str(INP))
try: kkt = complete_kkt(meta, a, mer['X'], mer['Pi'], mer['RC'], D, R, d + '/kkt', json.loads((LOC / 'V4_APPROVED.json').read_text()))
finally: shutil.rmtree(d)
cloud = json.loads((RUN / 'postprocess/KKT.json').read_text())
keys = [k for k in cloud if isinstance(cloud[k], (int, float, bool))]
res['V4_kkt_local'] = {k: kkt[k] for k in keys if k in kkt}
res['V4_kkt_identical_to_cloud'] = all(kkt.get(k) == cloud[k] for k in keys)
res['V4_kkt_mismatches'] = {k: [kkt.get(k), cloud[k]] for k in keys if kkt.get(k) != cloud[k]}
res['seconds'] = time.time() - t0
OUT.write_text(json.dumps(res, indent=2, default=lambda o: o.item() if hasattr(o, 'item') else str(o)) + '\n')
print(json.dumps({k: v for k, v in res.items() if k not in ('block',)}, indent=1, default=str))
shutil.rmtree(LOC.parent)
