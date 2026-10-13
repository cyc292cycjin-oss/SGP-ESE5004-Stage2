"""只读拉回本地 V4 复核所需的 D-1 冻结 CSC、D/R 映射与 D-2 块文件（云端只执行 cat），逐个按已核验索引核对 SHA。

目的地：outputs/d_2920_diagnostic/inputs_readonly_copy/（新目录；已存在的文件若 SHA 一致则跳过）。
"""
from pathlib import Path
import sys, json, subprocess, shlex, hashlib, os, time
W = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(W.parent / 'c09_exact_decomposition_20261013'))
from c09_control import SSH, sha

D1RUN = json.loads((W / 'D1_LAUNCH_RECEIPT.json').read_text())['run']
idx = {f['relative']: f for f in json.loads((W / 'd1_light/ARTIFACT_SHA_INDEX.json').read_text())['files']}
exp = json.loads((W / 'release_d5/D5_EXPECTED.json').read_text())
blk = json.loads((W / 'evidence/D2_BLOCK_RECEIPT.json').read_text())
assert hashlib.sha256((W / 'evidence/D2_BLOCK_RECEIPT.json').read_bytes()).hexdigest() == exp['block_receipt_sha256']
OUT = W.parents[1] / 'outputs/d_2920_diagnostic/inputs_readonly_copy'
jobs = []
for rel in ['bridge/math_problem/' + n for n in ('MATH_PROBLEM.json', 'start.npy', 'index.npy', 'value.npy', 'row_lower.npy', 'row_upper.npy', 'cost.npy', 'col_lower.npy', 'col_upper.npy', 'cost_scientific.npy')] + \
           ['bridge/mapping/' + n for n in ('D.npy', 'R.npy', 'MAPPING_MANIFEST.json', 'vlabels.npy', 'clabels.npy')]:
    jobs.append((D1RUN + '/' + rel, OUT / 'd1' / rel, idx[rel]['bytes'], idx[rel]['sha256']))
for n in ('BLOCK_COLUMNS.npy', 'BLOCK_ROWS.npy', 'BLOCK_PRIMAL.npy'):
    jobs.append((exp['block_dir'] + '/' + n, OUT / 'd2_block' / n, None, blk['files'][n]))
(OUT / 'd2_block').mkdir(parents=True, exist_ok=True); (OUT / 'd2_block' / 'BLOCK_RECEIPT.json').write_bytes((W / 'evidence/D2_BLOCK_RECEIPT.json').read_bytes())
rec = []
for src, dst, size, h in jobs:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and sha(dst) == h: rec.append({'file': str(dst.relative_to(OUT)), 'status': 'ALREADY_PRESENT_SHA_PASS'}); continue
    part = dst.with_name(dst.name + '.partial'); t = time.time()
    with open(part, 'wb') as f:
        p = subprocess.Popen(SSH + ['cat ' + shlex.quote(src)], stdout=f, stderr=subprocess.PIPE); p.wait(timeout=7200)
    assert p.returncode == 0, ('FETCH_FAILED', src)
    assert (size is None or part.stat().st_size == size) and sha(part) == h, ('SHA_MISMATCH_PARTIAL_KEPT', src)
    os.replace(part, dst); rec.append({'file': str(dst.relative_to(OUT)), 'bytes': dst.stat().st_size, 'sha256': h, 'seconds': round(time.time() - t, 1), 'status': 'FETCHED_SHA_PASS'})
    print(rec[-1], flush=True)
(W / 'D_INPUTS_FETCH_RECEIPT.json').write_text(json.dumps({'status': 'ALL_SHA_PASS', 'destination': str(OUT), 'd1_run': D1RUN, 'files': rec,
                                                          'binding': 'D-1 ARTIFACT_SHA_INDEX.json (d1_light) and D-2 BLOCK_RECEIPT.json (sha bound in D5_EXPECTED)', 'cloud_actions': 'read-only cat'}, indent=1) + '\n')
print('ALL_SHA_PASS')
