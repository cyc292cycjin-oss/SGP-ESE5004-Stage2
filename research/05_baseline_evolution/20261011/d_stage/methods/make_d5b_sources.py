"""D-5b（仅当 DR3 情况 1 时使用）：从 release_d5 派生，只改授权允许的内容并写出差异证据。

授权改动（D_STAGE_DELEGATION.md 第 3 条）：TimeLimit 43,200 s；整个 Run 约 50,400 s，阶段时限相应调整；
额外保存最终基 VBasis/CBasis（只保存，不用于热启动）。其余 154 项参数、模型、分解、V4 全部不变。
"""
from pathlib import Path
import difflib, shutil

W = Path(__file__).resolve().parents[1]; S = W / 'release_d5'; D = W / 'release_d5b'; EV = W / 'evidence'


def patch(name, edits):
    text = (S / name).read_text(encoding='utf-8'); new = text
    for old, rep in edits:
        assert new.count(old) == 1, (name, old[:90], new.count(old)); new = new.replace(old, rep)
    (D / name).write_text(new, encoding='utf-8')
    (EV / ('DIFF_D5B_' + name + '.patch')).write_text(''.join(difflib.unified_diff(text.splitlines(True), new.splitlines(True), 'release_d5/' + name, 'release_d5b/' + name)), encoding='utf-8')


CHECKS = [
    ("IDENTITY = 'D5_GATE6_2920_EXACT_DECOMPOSITION_MAIN_LP_USER_20261013_V1'", "IDENTITY = 'D5B_GATE6_2920_EXACT_DECOMPOSITION_MAIN_LP_TIMELIMIT43200_USER_20261013_V1'"),
    ("            elif k == 'TimeLimit' and 0 < v <= 14400: kind = 'AUTHORIZED_D_STAGE_TIME_LIMIT_MAX_14400'",
     "            elif k == 'TimeLimit' and 0 < v <= 43200: kind = 'AUTHORIZED_D5B_TIME_LIMIT_MAX_43200'"),
    ("    assert sha(HERE / 'D5_RELEASE_MANIFEST.json') == expected\n    m = read(HERE / 'D5_RELEASE_MANIFEST.json')",
     "    assert sha(HERE / 'D5B_RELEASE_MANIFEST.json') == expected\n    m = read(HERE / 'D5B_RELEASE_MANIFEST.json')"),
    ("    assert read(HERE / 'D5_APPROVAL_RECORD.json')['approved_by_user'] is True", "    assert read(HERE / 'D5B_APPROVAL_RECORD.json')['approved_by_user'] is True"),
    ("    assert read(HERE / 'D5_LOCAL_TESTS.json')['status'] == 'PASS'", "    assert read(HERE / 'D5B_LOCAL_TESTS.json')['status'] == 'PASS'"),
]

NATIVE = [
    ("        assert a['scope'] == 'D5_GATE6_2920_EXACT_DECOMPOSITION_SINGLE_MAIN_LP' and a['maximum_native_seconds'] == 14400",
     "        assert a['scope'] == 'D5B_GATE6_2920_EXACT_DECOMPOSITION_SINGLE_MAIN_LP_TL43200' and a['maximum_native_seconds'] == 43200"),
    ("parameters(lib, env, expected, types, 14400., apply=True)", "parameters(lib, env, expected, types, 43200., apply=True)"),
    ("        limit = min(14400., a['native_absolute_deadline_epoch'] - time.time()); assert limit > 0", "        limit = min(43200., a['native_absolute_deadline_epoch'] - time.time()); assert limit > 0"),
    ("        write(run / 'NATIVE_CALL_EXIT.json', call); stage(run, 'RAW_SAVE'); raw_save(backend, mmeta, run, a, call)",
     "        write(run / 'NATIVE_CALL_EXIT.json', call); stage(run, 'RAW_SAVE'); raw_save(backend, mmeta, run, a, call)\n"
     "        save_basis(lib, backend, mmeta, run, a)  # D-5b: final basis saved only; never used for a warm start"),
    ("def main(run):",
     "def save_basis(lib, b, meta, run, authorization):\n"
     "    \"\"\"Save VBasis/CBasis (int32) after the raw vectors; failures are recorded and never change the run status.\"\"\"\n"
     "    folder = run / 'raw' / 'basis'; folder.mkdir(exist_ok=False); out = {'run_id': authorization['run_id'], 'use': 'SAVED_ONLY_NOT_FOR_WARM_START', 'arrays': {}}\n"
     "    f = lib.GRBgetintattrarray; f.argtypes = [C.c_void_p, C.c_char_p, C.c_int, C.c_int, C.c_void_p]; f.restype = C.c_int\n"
     "    for name, count in [('VBasis', meta['num_col']), ('CBasis', meta['num_row'])]:\n"
     "        try:\n"
     "            arr = np.empty(count, dtype=np.int32)\n"
     "            for s, e in ranges(count):\n"
     "                if time.time() >= authorization['raw_absolute_deadline_epoch']: raise TimeoutError('RAW_ABSOLUTE_DEADLINE')\n"
     "                code = f(b.model, name.encode(), s, e - s, arr[s:].ctypes.data_as(C.c_void_p))\n"
     "                if code: raise RuntimeError('GRBgetintattrarray native error ' + str(code))\n"
     "            p = folder / (name + '.npy'); np.save(p, arr)\n"
     "            with p.open('rb') as fh: os.fsync(fh.fileno())\n"
     "            out['arrays'][name] = {'status': 'SAVED', 'count': count, 'sha256': sha(p), 'values': {str(k): int(v) for k, v in zip(*np.unique(arr, return_counts=True))}}\n"
     "        except Exception as e: out['arrays'][name] = {'status': 'NOT_AVAILABLE', 'error': type(e).__name__ + ': ' + str(e)[:300]}\n"
     "    write(folder / 'BASIS_RECEIPT.json', out); return out\n\n\n"
     "def main(run):"),
    ("call_site='d5_native.main:lib.GRBoptimize(backend.model)'", "call_site='d5_native.main:lib.GRBoptimize(backend.model) [D-5b]'"),
]

LAUNCH = [
    ("    if intent.exists() or opt.exists():raise RuntimeError('D5_AUTHORIZATION_ALREADY_RESERVED_NO_RETRY')\n    RUNROOT.mkdir(parents=True,exist_ok=True)\n    if any(RUNROOT.glob('d5_main2920_*')):raise RuntimeError('PRIOR_D5_RUN_REQUIRES_RECONCILIATION')\n    now=time.time();rid='d5_main2920_'",
     "    if intent.exists() or opt.exists():raise RuntimeError('D5B_AUTHORIZATION_ALREADY_RESERVED_NO_RETRY')\n    RUNROOT.mkdir(parents=True,exist_ok=True)\n    if any(RUNROOT.glob('d5b_main2920_*')):raise RuntimeError('PRIOR_D5B_RUN_REQUIRES_RECONCILIATION')\n    if not any(RUNROOT.glob('d5_main2920_*')):raise RuntimeError('D5B_REQUIRES_COMPLETED_D5')\n    now=time.time();rid='d5b_main2920_'"),
    ("    a={'scope':'D5_GATE6_2920_EXACT_DECOMPOSITION_SINGLE_MAIN_LP',", "    a={'scope':'D5B_GATE6_2920_EXACT_DECOMPOSITION_SINGLE_MAIN_LP_TL43200',"),
    ("'user_authorization_sha256':sha(HERE/'D5_APPROVAL_RECORD.json'),", "'user_authorization_sha256':sha(HERE/'D5B_APPROVAL_RECORD.json'),"),
    ("       'load_absolute_deadline_epoch':now+2400,'native_absolute_deadline_epoch':now+16800,'raw_absolute_deadline_epoch':now+17700,'post_absolute_deadline_epoch':now+20400,\n       'absolute_deadline_epoch':now+21600,'maximum_native_seconds':14400,",
     "       'load_absolute_deadline_epoch':now+2400,'native_absolute_deadline_epoch':now+45600,'raw_absolute_deadline_epoch':now+46500,'post_absolute_deadline_epoch':now+49500,\n       'absolute_deadline_epoch':now+50400,'maximum_native_seconds':43200,"),
    ("'proposed_algorithm_override':{'Crossover':-1,'TimeLimit':14400},", "'proposed_algorithm_override':{'Crossover':-1,'TimeLimit':43200},'save_final_basis':'VBasis/CBasis saved only, never used for warm start',"),
    ("'comparison_runs':['c09_daily122_20261012T185116Z_b867e3d3'],", "'comparison_runs':['c09_daily122_20261012T185116Z_b867e3d3','d5_main2920_20261012T212658Z_0162bbf4'],"),
    ("       'preregistered_decision_rule':read(HERE/'D5_APPROVAL_RECORD.json')['preregistered_decision_rule'],", "       'preregistered_decision_rule':read(HERE/'D5B_APPROVAL_RECORD.json')['preregistered_decision_rule'],"),
]

SEAL = [("'release_manifest_path':str(HERE/'D5_RELEASE_MANIFEST.json'),", "'release_manifest_path':str(HERE/'D5B_RELEASE_MANIFEST.json'),")]

if __name__ == '__main__':
    if D.exists(): shutil.rmtree(D)
    shutil.copytree(S, D, ignore=shutil.ignore_patterns('__pycache__', 'D5_RELEASE_MANIFEST.json', 'D5_LOCAL_TESTS.json', 'D5_APPROVAL_RECORD.json'))
    patch('d5_checks.py', CHECKS); patch('d5_native.py', NATIVE); patch('d5_launch.py', LAUNCH); patch('d5_seal.py', SEAL)
    print('ok')
