#!/usr/bin/env python3
"""C01 migration identity bridge. Read-only sources, fresh JSON receipt only.

This is NOT a solver, network builder, aggregation rerun, or launcher. It reuses
the completed Fraction audit only when the migrated NetCDF is byte-identical.
No connection, subprocess, credentials, process control, or file search.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import resource
import signal
import stat
import sys
import time
import uuid

ROOT = Path('/root/autodl-tmp/SGP')
NETWORK_REL = ('worktrees/gate6_capture_20261008T200734Z/results_project/'
               'assembly_v1/research_fullsc_2050_assembly_v1_unsolved.nc')
NETWORK_SHA = '238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d'
NETWORK_BYTES = 72082285
PRIOR_COMMIT = 'efb0ddb5b66c0305715d285c9d622ed65228b728'
SCHEME_COMMIT = '8883de6fb3e15767c632ac92f535e8a423e90b69'
SCHEME_FILES = {
    'EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json': (8968, 'a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720'),
    'LOADS_AND_WEIGHTS_REFERENCE.json': (567838, 'a5abcbfdd03a66d5b8bb16457b99eb5c860a32544a671440e1f5a97de2a467cd'),
    'external_pending_fixed_accounts.json': (854776, '20d9d0dc2028f1ca4e07b8e4e02fe51fce3a4a357c0d86366076a528b9a2a8e0'),
    'carrier_fragment.json': (4932207, '1b0ea897bc17d652a6ac5047935dc6af6c53536a51b197582b3567313d155e8e'),
}
EXPECTED = {
    'generators_t_p_max_pu': [2920, 460],
    'loads_t_p_set': [2920, 1737],
    'storage_units_t_inflow': [2920, 40],
}


class StopAudit(Exception):
    pass


def require(condition, reason):
    if not condition:
        raise StopAudit(reason)


def signature(st):
    return [st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns]


def checked_file(path, root, size, digest):
    """Check only an explicitly selected regular file, allowing internal links."""
    root = root.resolve(strict=True)
    path = Path(path)
    resolved = path.resolve(strict=True)
    require(resolved.is_relative_to(root), 'SOURCE_OUTSIDE_SGP_ROOT')
    before = resolved.stat()
    require(stat.S_ISREG(before.st_mode), 'SOURCE_NOT_REGULAR_FILE')
    require(before.st_size == size, 'SOURCE_SIZE_MISMATCH')
    h = hashlib.sha256()
    with resolved.open('rb') as f:
        require(signature(os.fstat(f.fileno())) == signature(before), 'SOURCE_CHANGED_BEFORE_READ')
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
        require(signature(os.fstat(f.fileno())) == signature(before), 'SOURCE_CHANGED_DURING_READ')
    require(h.hexdigest() == digest, 'SOURCE_SHA256_MISMATCH')
    require(path.resolve(strict=True) == resolved, 'SOURCE_LINK_TARGET_CHANGED')
    require(signature(resolved.stat()) == signature(before), 'SOURCE_CHANGED_AFTER_READ')
    return {'requested_path': str(path), 'resolved_path': str(resolved),
            'bytes': size, 'sha256': h.hexdigest(), 'stat_signature': signature(before),
            'internal_link_or_alias': path.absolute() != resolved, 'status': 'PASS'}


def inventory(dataset):
    """Metadata only: no time-series table or new daily array is materialized."""
    rows = []
    for name, variable in dataset.variables.items():
        if 'snapshots' not in variable.dimensions or variable.size == 0:
            continue
        if name.startswith('snapshots'):
            continue
        rows.append({'variable': name, 'shape': list(variable.shape),
                     'dtype': str(variable.dtype), 'dimensions': list(variable.dimensions)})
    actual = {r['variable']: r['shape'] for r in rows}
    require(actual == EXPECTED, 'BLOCKED_PROTOCOL_EXTENSION_OR_SHAPE_MISMATCH')
    require(all(r['dtype'] == 'float64' for r in rows), 'DYNAMIC_DTYPE_MISMATCH')
    require(len(dataset.dimensions['snapshots']) == 2920, 'SNAPSHOT_COUNT_MISMATCH')
    return sorted(rows, key=lambda r: r['variable'])


def timeout_handler(signum, frame):
    raise StopAudit('READ_ONLY_IDENTITY_WINDOW_EXPIRED_120_SECONDS')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--network', default=str(ROOT / NETWORK_REL),
                        help='Exact historical NetCDF; explicit alternative must remain within SGP.')
    parser.add_argument('--scheme-a-directory', default=None,
                        help='Optional EXACT existing Scheme A directory, if already present. No search/upload.')
    args = parser.parse_args()
    started = time.monotonic()
    now = datetime.datetime.now(datetime.timezone.utc)
    receipt = {
        'schema': 'C01_INSTANCE122_READONLY_IDENTITY_V1',
        'execution_host_claim': 'USER_REPORTED_AUTODL_122_NOT_CONTROL_PLANE_VERIFIED',
        'started_utc': now.isoformat(), 'time_limit_seconds': 120,
        'status': 'C01_BLOCKED_WITH_EVIDENCE',
        'prior_exact_audit_commit': PRIOR_COMMIT,
        'prior_evidence_path': 'research/05_baseline_evolution/20261011/c01/evidence',
        'calculation_mode': 'REUSE_COMPLETED_EXACT_FRACTION_AUDIT_IF_FILE_IDENTITY_MATCHES',
        'exact_aggregation_rerun': False,
        'Scheme_A': {'commit': SCHEME_COMMIT,
                     'manifest_sha256': SCHEME_FILES['EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json'][1],
                     'local_approved_evidence': '385_GROUPS_807_ACCOUNTS_VERIFIED_IN_PRIOR_C01',
                     'cloud_recipe_status': 'NOT_CHECKED_NO_DIRECTORY_SUPPLIED',
                     'new_Scheme_A_network_assembled': False},
        'license_status': 'NOT_CHECKED_NOT_NEEDED_FOR_C01',
        'G6_05': 'PAUSED_BY_USER', 'solver_calls': 0, 'model_builds': 0,
        'source_write_operations': 0, 'process_control_operations': 0,
        'remote_connections_from_script': 0, 'daily_model_GO': False,
    }
    alarm_set = False
    code = 2
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.setitimer(signal.ITIMER_REAL, 120)
        alarm_set = True
        root = ROOT.resolve(strict=True)
        require(root.is_dir(), 'SGP_ROOT_NOT_DIRECTORY')
        network = Path(args.network)
        require(network.name == 'research_fullsc_2050_assembly_v1_unsolved.nc', 'UNEXPECTED_NETWORK_NAME')
        receipt['network'] = checked_file(network, root, NETWORK_BYTES, NETWORK_SHA)
        # Import only the file reader after whole-file identity succeeds.
        import netCDF4
        with netCDF4.Dataset(receipt['network']['resolved_path'], 'r') as ds:
            receipt['dynamic_attributes_metadata_read_on_this_host'] = inventory(ds)
        require(signature(Path(receipt['network']['resolved_path']).stat()) == receipt['network']['stat_signature'],
                'SOURCE_CHANGED_DURING_METADATA_READ')
        require(network.resolve(strict=True) == Path(receipt['network']['resolved_path']), 'SOURCE_LINK_TARGET_CHANGED')
        if args.scheme_a_directory is not None:
            scheme = Path(args.scheme_a_directory)
            receipt['Scheme_A']['cloud_files'] = {}
            for name, (size, digest) in SCHEME_FILES.items():
                receipt['Scheme_A']['cloud_files'][name] = checked_file(scheme / name, root, size, digest)
            receipt['Scheme_A']['cloud_recipe_status'] = 'FOUR_FILES_SHA_MATCH_PINNED_LOCAL_RECIPE'
        receipt['identity_status'] = 'MIGRATED_NETCDF_MATCHES_PRIOR_EXACT_AUDIT'
        receipt['status'] = 'C01_REPRESENTATION_DECISION_REQUIRED'
        receipt['reused_exact_results_not_new_cloud_calculations'] = {
            'Load_count': 1737, 'varying_electric_Load_count': 96,
            'annual_exact_Load_count': 1642, 'positive_drift_count': 52, 'negative_drift_count': 43,
            'max_absolute_Load_annual_drift_MWh': '159/137438953472',
            'CF_assets': 460, 'inflow_assets': 40, 'all_CF_inflow_half_ULP_bounds_pass': True,
            'Scheme_A_groups_exact_annual_preserved': 385, 'Scheme_A_groups_D_le_Q_prime': 385,
            'Scheme_A_accounts_unchanged': 807, 'extra_dynamic_attributes': [],
            'CF_source_values_above_one': 44, 'CF_source_assets_above_one': 6,
        }
        receipt['limit'] = ('File identity permits reuse of the completed exact arithmetic on identical bytes. '
                            'It does not certify cloud deployment of Scheme A unless its optional four files pass; '
                            'it does not implement or approve a representation repair or authorize a model/solve.')
        code = 0
    except Exception as exc:
        # No environment dump or native/license error strings; selected file paths are non-secret.
        receipt['failure'] = {'exception_class': type(exc).__name__,
                              'reason': str(exc) if isinstance(exc, StopAudit) else 'FILE_OR_METADATA_CHECK_FAILED',
                              'missing_path': str(exc.filename) if isinstance(exc, FileNotFoundError) else None}
    finally:
        if alarm_set:
            signal.setitimer(signal.ITIMER_REAL, 0)
        receipt['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        receipt['wall_seconds'] = time.monotonic() - started
        receipt['peak_RSS_MiB'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        receipt['script_SHA256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    # The only writes are a new receipt under a dedicated evidence directory.
    # Never write into runs, worktrees, releases or source locations; never overwrite.
    try:
        root = ROOT.resolve(strict=True)
        out = root / 'c01_readonly_receipts'
        if out.exists() or out.is_symlink():
            require(out.is_dir() and not out.is_symlink(), 'UNSAFE_RECEIPT_DIRECTORY')
        else:
            out.mkdir(mode=0o700)
        require(out.resolve(strict=True).parent == root, 'RECEIPT_DIRECTORY_OUTSIDE_ROOT')
        target = out / ('C01_122_' + now.strftime('%Y%m%dT%H%M%S%fZ') + '_' + uuid.uuid4().hex[:8] + '.json')
        data = (json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
        with target.open('xb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        print(json.dumps({'receipt': str(target), 'sha256': hashlib.sha256(data).hexdigest(),
                          'status': receipt['status'], 'daily_model_GO': False}, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False))
        print('RECEIPT_WRITE_FAILED_' + type(exc).__name__, file=sys.stderr)
        code = 2
    return code


if __name__ == '__main__':
    sys.exit(main())
