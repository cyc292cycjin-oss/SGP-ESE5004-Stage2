"""D-5 identity and authorized-parameter gates (derived from c09_checks.py); no environment or solver creation."""
from pathlib import Path
import os, sys, platform, base64, hashlib, time
from c02_common import read, write, sha, resources, resource_gate, versions
ROOT = Path('/root/autodl-tmp/SGP'); HERE = Path(__file__).resolve().parent
SYSROOT = Path('/root/sgp_d_stage'); RUNROOT = SYSROOT / 'runs'   # user decision: D-5 run directory on the system disk
IDENTITY = 'D5_GATE6_2920_EXACT_DECOMPOSITION_MAIN_LP_USER_20261013_V1'
GIB = 1024 ** 3
BASELINE = 'C06_EFFECTIVE_MODEL_PARAMETERS.json'   # frozen C06 = C07A algorithm (Aggregate 1, BarConvTol 1e-9)


def parameter_diff(base, actual):
    """Authorized changes vs C06/C07A: Crossover 0 -> -1 (as C07B/C09) and the D-stage native TimeLimit up to 14,400 s."""
    if set(base) != set(actual) or len(base) != 154:
        raise ValueError('154_PARAMETER_COVERAGE')
    rows = []; bad = []
    for k, b in base.items():
        v = actual[k]; kind = 'UNCHANGED'
        if v != b:
            if k == 'Crossover' and b == 0 and v == -1: kind = 'AUTHORIZED_CROSSOVER_AS_C07B'
            elif k == 'TimeLimit' and 0 < v <= 14400: kind = 'AUTHORIZED_D_STAGE_TIME_LIMIT_MAX_14400'
            else: kind = 'UNAUTHORIZED'; bad.append(k)
        rows.append({'parameter': k, 'C06': b, 'D5': v, 'classification': kind})
    if actual['Crossover'] != -1: bad.append('Crossover')
    if actual['Aggregate'] != 1 or actual['BarConvTol'] != 1e-9 or actual['Method'] != 2: bad.append('frozen_base')
    return {'status': 'PASS' if not bad else 'FAIL', 'count': 154, 'unauthorized': bad,
            'differences': [x for x in rows if x['classification'] != 'UNCHANGED'], 'parameters': rows}


def verify_release(expected):
    assert sha(HERE / 'D5_RELEASE_MANIFEST.json') == expected
    m = read(HERE / 'D5_RELEASE_MANIFEST.json')
    for rel, r in m['files'].items():
        p = HERE / rel
        assert not p.is_symlink() and p.is_file() and p.resolve().is_relative_to(HERE)
        assert p.stat().st_size == r['bytes'] and sha(p) == r['sha256'], rel
    assert read(HERE / 'D5_APPROVAL_RECORD.json')['approved_by_user'] is True
    assert sha(HERE / 'V4_APPROVED.json') == '955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f'
    assert sha(HERE / 'C06_EFFECTIVE_MODEL_PARAMETERS.json') == 'f2f4bc219e3757dff6deda9035d67464e86e96e8ee9186427d2e27aced112f3c'
    assert sha(HERE / 'C03_EFFECTIVE_MODEL_PARAMETERS.json') == '9514025d6234626f26d0f7dca7f9cf8070de4d24360a64429edbed790b9432a2'
    assert read(HERE / 'LOCAL_INTERFACE_TESTS.json')['status'] == 'PASS'
    assert read(HERE / 'D5_LOCAL_TESTS.json')['status'] == 'PASS'
    assert read(HERE / 'D2_CLOUD_READONLY_CHECKS.json')['status'] == 'PASS'
    return m


def admission():
    import psutil
    assert platform.node() == 'autodl-container-21104cb00b-43be1fed'
    assert sys.executable == '/root/autodl-tmp/SGP/env/gate5/bin/python3.11' and sys.version_info[:3] == (3, 11, 13)
    pub = Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().split()
    assert pub[0] == 'ssh-ed25519' and base64.b64encode(hashlib.sha256(base64.b64decode(pub[1])).digest()).decode().rstrip('=') == 'liZ36vNCsNcNdXeWs4f+g5ZIhPM/ZihP834vxs8Ulqc'
    v = versions(); assert v == {'pypsa': '0.30.3', 'linopy': '0.5.5', 'numpy': '1.26.4', 'scipy': '1.15.2', 'pandas': '2.3.1', 'xarray': '2025.1.2', 'netCDF4': '1.7.2', 'psutil': '7.0.0'}
    # Run directory filesystem (system disk): unchanged start gate (>=20 GiB, 6 GiB reserve) plus projected D-5 outputs.
    assert os.stat('/root').st_dev != os.stat(ROOT).st_dev, 'SYSTEM_DISK_NOT_SEPARATE'
    r = resources(Path('/root')); resource_gate(r, start=True)
    assert r['disk_free'] - 8 * GIB >= 8 * GIB, 'RUN_DISK_PROJECTION'
    # Data disk keeps the D-1 inputs and receives the sealed archive: unchanged 8 GiB floor plus archive reserve.
    rd = resources(ROOT); assert rd['disk_free'] - 2 * GIB >= 8 * GIB, 'DATA_DISK_ARCHIVE_PROJECTION'
    from license_binding import bind_license
    lic = bind_license()
    active = []; names = {'c05_native.py', 'c05_worker.py', 'c06_native.py', 'c06_worker.py', 'c07_native.py', 'c07_worker.py',
                          'c09_native.py', 'c09_worker.py', 'c03_native.py', 'combined_worker.py', 'c02r_build.py',
                          'd1_build.py', 'd1_worker.py', 'd5_native.py', 'd5_worker.py', 'block_tools.py', 'd2_job.py'}
    for p in psutil.process_iter(['pid', 'cmdline', 'status']):
        cmd = p.info['cmdline'] or []
        if p.pid != os.getpid() and any(Path(s).name in names for s in cmd): active.append(p.pid)
    assert not active, 'ACTIVE_DAILY_TASK_NO_DUPLICATE'
    return {'hostname': platform.node(), 'resources_run_disk': r, 'resources_data_disk': rd, 'versions': v, 'license_path_binding': lic,
            'active_tasks': active, 'run_output_reserve_bytes': 8 * GIB, 'archive_reserve_bytes': 2 * GIB, 'epoch': time.time()}


def verify_inputs(run, progress):
    """Immutable D-1 build binding: every artifact/bridge file of the single D-1 run, SHA each (no rebuild, no conversion)."""
    s = read(HERE / 'SOURCE_BINDING.json'); base = Path(s['baseline_path'])
    assert base.parent == ROOT / 'runs' and base.name.startswith('d1_build2920_')
    assert read(base / 'D1_BUILD_GATES.json')['status'] == 'D1_BUILD_GATES_PASS'
    assert sha(base / 'ARTIFACT_SHA_INDEX.json') == s['baseline_ARTIFACT_SHA_INDEX_sha256']
    for rel, h in s['core'].items(): assert sha(base / rel) == h, rel
    for j, r in enumerate(s['files']):
        p = base / r['relative']; real = p.resolve(strict=True)
        assert real.is_relative_to(ROOT) and real.is_file() and p.stat().st_size == r['bytes'], r['relative']
        assert sha(p) == r['sha256'], r['relative']
        if j % 200 == 0: progress('IMMUTABLE_INPUT_SHA')
    for name in ('artifacts', 'bridge'):
        dest = run / name; assert not dest.exists() and not dest.is_symlink(); dest.symlink_to(base / name, target_is_directory=True)
    write(run / 'BUILD_RESULT.json', read(base / 'BUILD_RESULT.json'))
    write(run / 'IMMUTABLE_INPUTS.json', {'status': 'ALL_REFERENCED_INPUT_SHA_PASS', 'baseline': str(base),
          'source_binding_sha256': sha(HERE / 'SOURCE_BINDING.json'), 'file_count': len(s['files']), 'bytes': s['bytes'],
          'core': s['core'], 'baseline_ARTIFACT_SHA_INDEX_sha256': s['baseline_ARTIFACT_SHA_INDEX_sha256'],
          'read_only_directory_links': {'artifacts': str(base / 'artifacts'), 'bridge': str(base / 'bridge')},
          'new_model_builds': 0, 'CSR_to_CSC_conversions': 0, 'old_candidate_warm_start': False})
    return s
