"""Derive the D-5 release modules from the frozen C09 release by explicit text patches; write unified diffs as evidence.

Each replacement must match exactly once. Unchanged modules are copied byte-for-byte.
Usage: python make_d5_sources.py <extracted C09 release dir>
"""
from pathlib import Path
import difflib, re, shutil, sys

C9 = Path(sys.argv[1]); W = Path(__file__).resolve().parents[1]; D = W / 'release_d5'; EV = W / 'evidence'
UNCHANGED = ['adapter.py', 'author_objective.py', 'basis_free.py', 'c02_common.py', 'daily_physics.py', 'license_binding.py', 'scatter.py',
             'validation_dynamics.py', 'V4_APPROVED.json', 'C03_EFFECTIVE_MODEL_PARAMETERS.json', 'C06_EFFECTIVE_MODEL_PARAMETERS.json',
             'NATIVE_PARAMETER_EVIDENCE.json', 'LOCAL_INTERFACE_TESTS.json', 'helpers/assembly_components.py', 'helpers/carrier_architecture.py',
             'helpers/fixed_account_scope.py', 'helpers/fixed_accounts.py', 'helpers/fixed_resource_acceptance.py', 'helpers/v4_algebra_extracted.py']


def patch(src, dst, edits, global_edits=()):
    text = (C9 / src).read_text(encoding='utf-8'); new = text
    for old, rep in edits:
        assert new.count(old) == 1, (src, old[:100], new.count(old)); new = new.replace(old, rep)
    for old, rep in global_edits: new = new.replace(old, rep)
    (D / dst).write_text(new, encoding='utf-8')
    (EV / ('DIFF_D5_' + dst + '.patch')).write_text(''.join(difflib.unified_diff(text.splitlines(True), new.splitlines(True), 'c09_release/' + src, 'release_d5/' + dst)), encoding='utf-8')


NAMES = [('C09_BLOCK_VERIFICATION', 'D5_BLOCK_VERIFICATION'), ('C09_MAIN_PROBLEM_IDENTITY', 'D5_MAIN_PROBLEM_IDENTITY'),
         ('C09_MAIN_COLUMNS', 'D5_MAIN_COLUMNS'), ('C09_MAIN_ROWS', 'D5_MAIN_ROWS'), ('C09_PARAMETER_DIFF', 'D5_PARAMETER_DIFF'),
         ('C09_EXECUTION_METADATA', 'D5_EXECUTION_METADATA'), ('C09_NATIVE_OPTIMIZE_ENTERED', 'D5_NATIVE_OPTIMIZE_ENTERED'),
         ('C09_MERGE', 'D5_MERGE'), ('C09_MAIN_LP_C03_COORDINATES', 'D5_MAIN_LP_D1_COORDINATES'),
         ('from production_control import', 'from d_production_control import'), ('from c09_checks import', 'from d5_checks import'),
         ('from c09_decompose import', 'from d5_decompose import')]

CHECKS = [
    ('"""C09 identity and one-factor gates; no environment or solver creation."""',
     '"""D-5 identity and authorized-parameter gates (derived from c09_checks.py); no environment or solver creation."""'),
    ("ROOT = Path('/root/autodl-tmp/SGP'); HERE = Path(__file__).resolve().parent\nIDENTITY = 'C09_EXACT_BLOCK_DECOMPOSITION_DAILY122_USER_20261013_V1'",
     "ROOT = Path('/root/autodl-tmp/SGP'); HERE = Path(__file__).resolve().parent\n"
     "SYSROOT = Path('/root/sgp_d_stage'); RUNROOT = SYSROOT / 'runs'   # user decision: D-5 run directory on the system disk\n"
     "IDENTITY = 'D5_GATE6_2920_EXACT_DECOMPOSITION_MAIN_LP_USER_20261013_V1'\nGIB = 1024 ** 3"),
    ('    """Only authorized algorithm change vs C06/C07A: Crossover 0 -> -1 (identical to C07B)."""',
     '    """Authorized changes vs C06/C07A: Crossover 0 -> -1 (as C07B/C09) and the D-stage native TimeLimit up to 14,400 s."""'),
    ("            elif k == 'TimeLimit' and 0 < v <= min(3600, b): kind = 'FIXED_DEADLINE_PROTECTION'",
     "            elif k == 'TimeLimit' and 0 < v <= 14400: kind = 'AUTHORIZED_D_STAGE_TIME_LIMIT_MAX_14400'"),
    ("        rows.append({'parameter': k, 'C06': b, 'C09': v, 'classification': kind})", "        rows.append({'parameter': k, 'C06': b, 'D5': v, 'classification': kind})"),
    ("    assert sha(HERE / 'C09_RELEASE_MANIFEST.json') == expected\n    m = read(HERE / 'C09_RELEASE_MANIFEST.json')",
     "    assert sha(HERE / 'D5_RELEASE_MANIFEST.json') == expected\n    m = read(HERE / 'D5_RELEASE_MANIFEST.json')"),
    ("    assert read(HERE / 'C09_APPROVAL_RECORD.json')['approved_by_user'] is True", "    assert read(HERE / 'D5_APPROVAL_RECORD.json')['approved_by_user'] is True"),
    ("    assert read(HERE / 'C09_LOCAL_TESTS.json')['status'] == 'PASS'", "    assert read(HERE / 'D5_LOCAL_TESTS.json')['status'] == 'PASS'\n    assert read(HERE / 'D2_CLOUD_READONLY_CHECKS.json')['status'] == 'PASS'"),
    ("    r = resources(ROOT); resource_gate(r, start=True)\n    assert r['disk_free'] - 4 * 1024 ** 3 >= 8 * 1024 ** 3",
     "    # Run directory filesystem (system disk): unchanged start gate (>=20 GiB, 6 GiB reserve) plus projected D-5 outputs.\n"
     "    assert os.stat('/root').st_dev != os.stat(ROOT).st_dev, 'SYSTEM_DISK_NOT_SEPARATE'\n"
     "    r = resources(Path('/root')); resource_gate(r, start=True)\n    assert r['disk_free'] - 8 * GIB >= 8 * GIB, 'RUN_DISK_PROJECTION'\n"
     "    # Data disk keeps the D-1 inputs and receives the sealed archive: unchanged 8 GiB floor plus archive reserve.\n"
     "    rd = resources(ROOT); assert rd['disk_free'] - 2 * GIB >= 8 * GIB, 'DATA_DISK_ARCHIVE_PROJECTION'"),
    ("    active = []; names = {'c05_native.py', 'c05_worker.py', 'c06_native.py', 'c06_worker.py', 'c07_native.py', 'c07_worker.py',\n                          'c09_native.py', 'c09_worker.py', 'c03_native.py', 'combined_worker.py', 'c02r_build.py'}",
     "    active = []; names = {'c05_native.py', 'c05_worker.py', 'c06_native.py', 'c06_worker.py', 'c07_native.py', 'c07_worker.py',\n                          'c09_native.py', 'c09_worker.py', 'c03_native.py', 'combined_worker.py', 'c02r_build.py',\n                          'd1_build.py', 'd1_worker.py', 'd5_native.py', 'd5_worker.py', 'block_tools.py', 'd2_job.py'}"),
    ("    return {'hostname': platform.node(), 'resources': r, 'versions': v, 'license_path_binding': lic,\n            'active_daily_tasks': active, 'new_output_reserve_bytes': 4 * 1024 ** 3, 'epoch': time.time()}",
     "    return {'hostname': platform.node(), 'resources_run_disk': r, 'resources_data_disk': rd, 'versions': v, 'license_path_binding': lic,\n            'active_tasks': active, 'run_output_reserve_bytes': 8 * GIB, 'archive_reserve_bytes': 2 * GIB, 'epoch': time.time()}"),
    ('    """Identical immutable C03 baseline binding as C07 (17,369 files, SHA each)."""\n    s = read(HERE / \'SOURCE_BINDING.json\'); base = Path(s[\'baseline_path\'])\n    assert base == ROOT / \'runs/c02r_c03_daily122_20261012T044259Z_25e62c10\'',
     '    """Immutable D-1 build binding: every artifact/bridge file of the single D-1 run, SHA each (no rebuild, no conversion)."""\n    s = read(HERE / \'SOURCE_BINDING.json\'); base = Path(s[\'baseline_path\'])\n    assert base.parent == ROOT / \'runs\' and base.name.startswith(\'d1_build2920_\')\n    assert read(base / \'D1_BUILD_GATES.json\')[\'status\'] == \'D1_BUILD_GATES_PASS\''),
    ("    assert sha(base / 'BACKUP_INDEX.json') == s['baseline_BACKUP_INDEX_sha256']", "    assert sha(base / 'ARTIFACT_SHA_INDEX.json') == s['baseline_ARTIFACT_SHA_INDEX_sha256']"),
    ("          'core': s['core'], 'baseline_BACKUP_INDEX_sha256': s['baseline_BACKUP_INDEX_sha256'],", "          'core': s['core'], 'baseline_ARTIFACT_SHA_INDEX_sha256': s['baseline_ARTIFACT_SHA_INDEX_sha256'],"),
]

DECOMP = [
    ('"""C09 exact block decomposition. No optimizer, environment or launch.', '"""D-5 exact block decomposition (derived from c09_decompose.py; dimensions and block files bound to D-1/D-2 receipts). No optimizer, environment or launch.'),
    ("BLOCK = HERE / 'block'\nEXPECTED = {'block_columns': 884472, 'block_rows': 2203217, 'num_col': 2450005, 'num_row': 6042238,\n            'nnz': 11403496}",
     "EXPECTED = json.loads((HERE / 'D5_EXPECTED.json').read_text())\nBLOCK = Path(EXPECTED['block_dir'])"),
    ("    rec = json.loads((BLOCK / 'C09_BLOCK_PRIMAL_RECEIPT.json').read_text())", "    if sha(BLOCK / 'BLOCK_RECEIPT.json') != EXPECTED['block_receipt_sha256']: raise ValueError('BLOCK_RECEIPT_SHA')\n    rec = json.loads((BLOCK / 'BLOCK_RECEIPT.json').read_text())"),
    ("    cols = np.load(BLOCK / 'C09_BLOCK_COLUMNS.npy')\n    rows = np.load(BLOCK / 'C09_BLOCK_ROWS.npy')\n    xb = np.load(BLOCK / 'C09_BLOCK_PRIMAL.npy')",
     "    if set(rec['files']) != {'BLOCK_COLUMNS.npy', 'BLOCK_ROWS.npy', 'BLOCK_PRIMAL.npy'}: raise ValueError('BLOCK_FILE_SET')\n    cols = np.load(BLOCK / 'BLOCK_COLUMNS.npy')\n    rows = np.load(BLOCK / 'BLOCK_ROWS.npy')\n    xb = np.load(BLOCK / 'BLOCK_PRIMAL.npy')"),
    ("'derivation': 'C09 restriction of frozen C03 CSC'}", "'derivation': 'D5 restriction of frozen D-1 2920 CSC'}"),
]

NATIVE = [
    ('"""C09 native worker. Sole optimize call site, on the MAIN LP only, after full same-model readback."""', '"""D-5 native worker (derived from c09_native.py). Sole optimize call site, on the 2920 MAIN LP only, after full same-model readback."""'),
    ("        assert a['scope'] == 'C09_EXACT_BLOCK_DECOMPOSITION_SINGLE_DAILY_MAIN_LP' and a['maximum_native_seconds'] == 3600\n        assert read(run / 'BUILD_RESULT.json')['status'] == 'C02_BUILD_STATIC_ACCEPTED_NO_SOLVE'",
     "        assert a['scope'] == 'D5_GATE6_2920_EXACT_DECOMPOSITION_SINGLE_MAIN_LP' and a['maximum_native_seconds'] == 14400\n        assert read(run / 'BUILD_RESULT.json')['status'] == 'D1_BUILD_STATIC_ACCEPTED_NO_SOLVE'"),
    ("parameters(lib, env, expected, types, 3600., apply=True)", "parameters(lib, env, expected, types, 14400., apply=True)"),
    ("        if time.time() >= min(current['entered_epoch'] + 900, a['load_absolute_deadline_epoch']): raise TimeoutError('NATIVE_HANDOFF_DEADLINE')\n        limit = min(3600., a['native_absolute_deadline_epoch'] - time.time()); assert limit > 0",
     "        if time.time() >= min(current['entered_epoch'] + a['bridge_phase_seconds'], a['load_absolute_deadline_epoch']): raise TimeoutError('NATIVE_HANDOFF_DEADLINE')\n        limit = min(14400., a['native_absolute_deadline_epoch'] - time.time()); assert limit > 0"),
    ("call_site='c09_native.main:lib.GRBoptimize(backend.model)'", "call_site='d5_native.main:lib.GRBoptimize(backend.model)'"),
]

WORKER = [
    ("from production_control import alive,phase_deadline,stop_blocks_stage\nfrom c09_checks import verify_release,verify_inputs",
     "from d_production_control import alive,phase_deadline,stop_blocks_stage\nfrom d5_checks import verify_release,verify_inputs"),
    ("subprocess.run([sys.executable,'-B',str(HERE/'c09_native.py'),str(run)],check=True)", "subprocess.run([sys.executable,'-B',str(HERE/'d5_native.py'),str(run)],check=True)"),
    ("            from c09_decompose import load_block,merge", "            from d5_decompose import load_block,merge"),
    ("            mc=np.load(run/'C09_MAIN_COLUMNS.npy');mr=np.load(run/'C09_MAIN_ROWS.npy')", "            mc=np.load(run/'D5_MAIN_COLUMNS.npy');mr=np.load(run/'D5_MAIN_ROWS.npy')"),
    ("            write(run/'C09_MERGE.json',", "            write(run/'D5_MERGE.json',"),
    ("            from daily_acceptance import postprocess", "            from d5_acceptance import postprocess"),
]

LAUNCH = [
    ('"""One C09 authorization and detached protection chain. Exactly one optimize, no retry."""', '"""One D-5 authorization and detached protection chain (derived from c09_launch.py). Exactly one optimize on the 2920 main LP, no retry."""'),
    ("from c09_checks import ROOT,HERE,IDENTITY,verify_release,admission", "from d5_checks import ROOT,RUNROOT,HERE,IDENTITY,verify_release,admission"),
    ("    claims=ROOT/'c09_claims';claims.mkdir(exist_ok=True)", "    claims=ROOT/'d_claims';claims.mkdir(exist_ok=True)"),
    ("    if intent.exists() or opt.exists():raise RuntimeError('C09_AUTHORIZATION_ALREADY_RESERVED_NO_RETRY')\n    if any((ROOT/'runs').glob('c09_daily122_*')):raise RuntimeError('PRIOR_C09_RUN_REQUIRES_RECONCILIATION')\n    now=time.time();rid='c09_daily122_'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime(now))+'_'+uuid.uuid4().hex[:8]\n    run=ROOT/'runs'/rid",
     "    if intent.exists() or opt.exists():raise RuntimeError('D5_AUTHORIZATION_ALREADY_RESERVED_NO_RETRY')\n    RUNROOT.mkdir(parents=True,exist_ok=True)\n    if any(RUNROOT.glob('d5_main2920_*')):raise RuntimeError('PRIOR_D5_RUN_REQUIRES_RECONCILIATION')\n    now=time.time();rid='d5_main2920_'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime(now))+'_'+uuid.uuid4().hex[:8]\n    run=RUNROOT/rid"),
    ("    a={'scope':'C09_EXACT_BLOCK_DECOMPOSITION_SINGLE_DAILY_MAIN_LP',", "    a={'scope':'D5_GATE6_2920_EXACT_DECOMPOSITION_SINGLE_MAIN_LP',"),
    ("'user_authorization_sha256':sha(HERE/'C09_APPROVAL_RECORD.json'),", "'user_authorization_sha256':sha(HERE/'D5_APPROVAL_RECORD.json'),"),
    ("       'load_absolute_deadline_epoch':now+900,'native_absolute_deadline_epoch':now+4500,'raw_absolute_deadline_epoch':now+4950,'post_absolute_deadline_epoch':now+6150,\n       'absolute_deadline_epoch':now+7200,'maximum_native_seconds':3600,",
     "       'build_phase_seconds':1,'build_absolute_deadline_epoch':now+1,'bridge_phase_seconds':2400,'post_phase_seconds':3000,\n       'load_absolute_deadline_epoch':now+2400,'native_absolute_deadline_epoch':now+16800,'raw_absolute_deadline_epoch':now+17700,'post_absolute_deadline_epoch':now+20400,\n       'absolute_deadline_epoch':now+21600,'maximum_native_seconds':14400,"),
    ("'raw_save_seconds':300,", "'raw_save_seconds':600,"),
    ("       'baseline_run_id':'c02r_c03_daily122_20261012T044259Z_25e62c10','input_binding_sha256':sha(HERE/'SOURCE_BINDING.json'),",
     "       'baseline_run_id':read(HERE/'SOURCE_BINDING.json')['baseline_run_id'],'input_binding_sha256':sha(HERE/'SOURCE_BINDING.json'),'run_disk':'SYSTEM_DISK_/root','threads':4,"),
    ("'proposed_algorithm_override':{'Crossover':-1},'algorithm_baseline':'C06/C07A (154 parameters)','comparison_runs':['c07a_daily122_20261012T162928Z_0d9301f2','c07b_daily122_20261012T163744Z_4250e585'],",
     "'proposed_algorithm_override':{'Crossover':-1,'TimeLimit':14400},'algorithm_baseline':'C06/C07A (154 parameters)','comparison_runs':['c09_daily122_20261012T185116Z_b867e3d3'],"),
    ("       'preregistered_decision_rule':read(HERE/'C09_APPROVAL_RECORD.json')['preregistered_decision_rule'],", "       'preregistered_decision_rule':read(HERE/'D5_APPROVAL_RECORD.json')['preregistered_decision_rule'],"),
    ("    from production_control import limits_valid", "    from d_production_control import limits_valid"),
    ("        p=subprocess.Popen([sys.executable,'-B',str(HERE/'c09_launch.py'),'supervise',str(control)]", "        p=subprocess.Popen([sys.executable,'-B',str(HERE/'d5_launch.py'),'supervise',str(control)]"),
    ("    from production_control import supervise as protect", "    from d_production_control import supervise as protect"),
    ("    try:protect([sys.executable,'-B',str(HERE/'c09_worker.py'),str(run)],run,a,require_cgroup=True,launch_closeout=False)", "    try:protect([sys.executable,'-B',str(HERE/'d5_worker.py'),str(run)],run,a,require_cgroup=True,launch_closeout=False)"),
    ("            from c09_seal import guarded_seal", "            from d5_seal import guarded_seal"),
]

SEAL = [
    ('"""C09 new-results-only seal (copied unchanged from C07 except names). Inputs remain immutable references; bounded standalone guard."""', '"""D-5 new-results-only seal (C09 seal with D names and D-1 binding). Inputs remain immutable references; bounded standalone guard."""'),
    ("from production_control import alive,ident,resources as process_resources", "from d_production_control import alive,ident,resources as process_resources"),
    ("    write(run/'BACKUP_INDEX.json',{'run_id':a['run_id'],'files':files,'cloud_originals_preserved':True,'local_sync':'LOCAL_SYNC_PENDING','immutable_references':{'baseline_path':source['baseline_path'],'baseline_BACKUP_INDEX_sha256':source['baseline_BACKUP_INDEX_sha256'],'source_binding_path':str(HERE/'SOURCE_BINDING.json'),'source_binding_sha256':sha(HERE/'SOURCE_BINDING.json'),'release_manifest_path':str(HERE/'C09_RELEASE_MANIFEST.json'),",
     "    write(run/'BACKUP_INDEX.json',{'run_id':a['run_id'],'files':files,'cloud_originals_preserved':True,'local_sync':'LOCAL_SYNC_PENDING','immutable_references':{'baseline_path':source['baseline_path'],'baseline_ARTIFACT_SHA_INDEX_sha256':source['baseline_ARTIFACT_SHA_INDEX_sha256'],'source_binding_path':str(HERE/'SOURCE_BINDING.json'),'source_binding_sha256':sha(HERE/'SOURCE_BINDING.json'),'release_manifest_path':str(HERE/'D5_RELEASE_MANIFEST.json'),"),
    ("    with (HERE.parent/(a['run_id']+'_seal_guard.log')).open('xb') as log:\n        p=subprocess.Popen([sys.executable,'-B',str(HERE/'c09_seal.py'),'guard',str(control)]", "    with (HERE.parent/(a['run_id']+'_seal_guard.log')).open('xb') as log:\n        p=subprocess.Popen([sys.executable,'-B',str(HERE/'d5_seal.py'),'guard',str(control)]"),
    ("        child=subprocess.Popen([sys.executable,'-B',str(HERE/'c09_seal.py'),'seal',str(run),str(deadline)]", "        child=subprocess.Popen([sys.executable,'-B',str(HERE/'d5_seal.py'),'seal',str(run),str(deadline)]"),
]

ACCEPT = [
    ('"""365-day label bridge to unchanged V4 algebra and frozen physical equations."""', '"""2920x3h label bridge to unchanged V4 algebra and frozen physical equations (C09 daily_acceptance module with dimensions and file names re-bound only)."""'),
    ("def restore_daily(n,folder,active,x):\n    folder=Path(folder);mapping=read(folder/'LABELS.json');scalars={};covered=[]\n    assert len(n.snapshots)==365",
     "def restore_network(n,folder,active,x,snapshots):\n    folder=Path(folder);mapping=read(folder/'LABELS.json');scalars={};covered=[]\n    assert len(n.snapshots)==snapshots==2920"),
    ("    binding=read(source/'DAILY_V4_BINDING.json');meta,a=open_problem(bridge/'math_problem')", "    binding=read(source/'GATE6_2920_V4_BINDING.json');meta,a=open_problem(bridge/'math_problem')"),
    ("    assert binding['network_SHA256']==sha(source/'daily_365_unsolved.nc') and binding['LP_manifest_SHA256']==sha(source/'lp/MATH_PROBLEM.json')",
     "    assert binding['network_SHA256']==sha(source/'gate6_2920_scheme_a_unsolved.nc') and binding['LP_manifest_SHA256']==sha(source/'lp/MATH_PROBLEM.json')\n    assert binding['snapshots']==binding['expected_snapshots']==2920 and binding['hours_per_snapshot']==3 and binding['V4_formulas_changed'] is False"),
    ("    n=pypsa.Network(source/'daily_365_unsolved.nc')\n    scalars=restore_daily(n,source/'mapping',np.load(bridge/'mapping/vlabels.npy',mmap_mode='r'),np.load(out/'original_vectors/X_original.npy',mmap_mode='r'))",
     "    n=pypsa.Network(source/'gate6_2920_scheme_a_unsolved.nc')\n    scalars=restore_network(n,source/'mapping',np.load(bridge/'mapping/vlabels.npy',mmap_mode='r'),np.load(out/'original_vectors/X_original.npy',mmap_mode='r'),binding['snapshots'])"),
    ("    back,export=netcdf_roundtrip(n,out/'daily_candidate_UNQUALIFIED.nc','UNQUALIFIED_PENDING_ALL_GATES')", "    back,export=netcdf_roundtrip(n,out/'gate6_2920_candidate_UNQUALIFIED.nc','UNQUALIFIED_PENDING_ALL_GATES')"),
    ("'NetCDF_exact_readback':True,'daily_binding':True}", "'NetCDF_exact_readback':True,'binding_2920':True}"),
    ("'original_scientific_objective_optimality':'NOT_PROVEN','Gate6_2920_PASS':False,", "'original_scientific_objective_optimality':'NOT_PROVEN','Gate6_2920_PASS':'DECIDED_BY_PREREGISTERED_DR_RULE',"),
]

if __name__ == '__main__':
    if D.exists(): shutil.rmtree(D)
    (D / 'helpers').mkdir(parents=True); EV.mkdir(exist_ok=True)
    for f in UNCHANGED: shutil.copyfile(C9 / f, D / f)
    shutil.copyfile(W / 'release_d1' / 'd_production_control.py', D / 'd_production_control.py')
    patch('c09_checks.py', 'd5_checks.py', CHECKS)
    patch('c09_decompose.py', 'd5_decompose.py', DECOMP)
    patch('c09_native.py', 'd5_native.py', NATIVE, NAMES)
    patch('c09_worker.py', 'd5_worker.py', WORKER, NAMES)
    patch('c09_launch.py', 'd5_launch.py', LAUNCH)
    patch('c09_seal.py', 'd5_seal.py', SEAL)
    patch('daily_acceptance.py', 'd5_acceptance.py', ACCEPT)
    for f in D.glob('*.py'):
        t = f.read_text(encoding='utf-8')
        bad = re.findall(r'^\s*(?:from|import)\s+(?:c09_\w+|production_control|daily_acceptance)\b|HERE ?/ ?.c09_', t, re.M)
        assert not bad, (f.name, bad)
    print('ok')
