"""Convert a user-exported NGA WPI GDB for the PyPSA-ASEAN tutorial only."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from datetime import datetime, timezone

sys.dont_write_bytecode = True
import pyproj
os.environ['PROJ_DATA'] = pyproj.datadir.get_data_dir()
import pandas as pd
import pyogrio

EXPECTED_ZIP_SHA256 = '34461849e406f2b1fc92009dd928e2f35785ddf1549971c397b4eddfc873e224'
MAPPING = {
    'wpinumber': 'World Port Index Number',
    'regionname': 'Region Name',
    'main_port_name': 'Main Port Name',
    'alternate_name': 'Alternate Port Name',
    'wpi_cc': 'Country Code',
    'dodwaterbody': 'World Water Body',
    'lng_terminal_depth': 'Liquified Natural Gas Terminal Depth (m)',
    'harbor_size_code': 'Harbor Size',
    'harbor_type_code': 'Harbor Type',
    'harbor_use_code': 'Harbor Use',
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    archive = args.archive.resolve()
    project = args.project.resolve()
    if digest(archive) != EXPECTED_ZIP_SHA256:
        raise ValueError('Archive differs from the inspected user download. No project files changed.')
    data = pyogrio.read_dataframe(
        f'/vsizip/{archive.as_posix()}/wpi_data_download.gdb', layer='WPI'
    )
    missing = set(MAPPING) - set(data.columns)
    if missing:
        raise ValueError(f'Missing source fields: {missing}')
    if data.crs.to_epsg() != 4326 or not data.geom_type.eq('Point').all():
        raise ValueError('Unexpected CRS or geometry; do not infer coordinates.')
    if data.geometry.isna().any() or data.geometry.is_empty.any():
        raise ValueError('Missing coordinates.')
    result = pd.DataFrame(data[list(MAPPING)].rename(columns=MAPPING))
    result['Latitude'] = data.geometry.y
    result['Longitude'] = data.geometry.x
    if not (result['Latitude'].between(-90,90).all() and result['Longitude'].between(-180,180).all()):
        raise ValueError('Coordinates outside valid range.')
    script = project / 'scripts/prepare_ports.py'
    original = script.read_text(encoding='utf-8')
    read_line = '    wpi_csv = read_csv_nafix(fn, index_col=0)'
    marker = '# SGP: use frozen local WPI export for tutorial only.'
    local_csv = project / 'data/ports/wpi_tutorial_from_gdb.csv'
    insertion = '\n'.join([
        '    ' + marker,
        '    if snakemake.config.get("tutorial", False):',
        '        fn = Path(BASE_DIR) / "data/ports/wpi_tutorial_from_gdb.csv"',
        '        if not fn.is_file():',
        '            raise FileNotFoundError(f"Tutorial WPI CSV missing: {fn}")',
        read_line,
    ])
    if original.count(read_line) != 1:
        raise ValueError('Unexpected prepare_ports.py content. No project files changed.')
    patched = original if marker in original else original.replace(read_line, insertion)
    compile(patched, str(script), 'exec')

    # Exercise the actual existing preprocessing code with the converted data.
    from types import SimpleNamespace
    sys.path.insert(0, str(project / 'scripts'))
    with tempfile.TemporaryDirectory(prefix='wpi-check-') as td:
        temporary = Path(td)
        candidate = temporary / 'wpi.csv'
        result.to_csv(candidate, index=False)
        check_source = patched.replace(
            'fn = Path(BASE_DIR) / "data/ports/wpi_tutorial_from_gdb.csv"',
            f'fn = Path({str(candidate)!r})',
        )
        outputs = [temporary / 'ports.csv', temporary / 'export_ports.csv']
        mock = SimpleNamespace(config={'tutorial': True}, params=SimpleNamespace(custom_export=False), output=outputs)
        namespace = {'__name__': '__main__', '__file__': str(script), 'snakemake': mock}
        exec(compile(check_source, str(script), 'exec'), namespace)
        ports, exports = [pd.read_csv(p, keep_default_na=False) for p in outputs]
        if ports.empty or exports.empty:
            raise ValueError('Existing port preprocessing produced empty output.')
        sums = ports.groupby('country_full_name')['fraction'].sum()
        if not sums.sub(1).abs().lt(1e-10).all():
            raise ValueError('Country port fractions do not sum to one.')
        counts = {'raw_rows': len(result), 'ports_rows': len(ports), 'export_ports_rows': len(exports),
                  'duplicate_wpi_ids_preserved': int(result['World Port Index Number'].duplicated().sum()),
                  'ports_by_country': ports['country'].value_counts().sort_index().to_dict()}
    print('CHECK PASS:', json.dumps(counts, ensure_ascii=False))
    if args.check_only:
        print('Check only: no project data or source files changed.')
        return

    local_csv.parent.mkdir(parents=True, exist_ok=True)
    raw_copy = local_csv.parent / 'wpi_data_download_original.zip'
    if raw_copy.exists() and digest(raw_copy) != EXPECTED_ZIP_SHA256:
        raise ValueError('Existing archive differs; refusing to overwrite it.')
    if not raw_copy.exists():
        shutil.copy2(archive, raw_copy)
    result.to_csv(local_csv, index=False)
    manifest = {
        'purpose': 'Tutorial engineering test only; not verified as author paper input.',
        'source_url': 'https://fgmod.nga.mil/apps/WPI-Viewer/',
        'provenance': 'User manually exported all ports through official viewer on 2026-09-29.',
        'converted_utc': datetime.now(timezone.utc).isoformat(),
        'archive_sha256': EXPECTED_ZIP_SHA256, 'csv_sha256': digest(local_csv),
        'layer': 'WPI', 'source_crs': str(data.crs), 'field_mapping': MAPPING,
        'coordinates': 'Longitude/Latitude from EPSG:4326 Point geometry; no reprojection.',
        'records': 'No input rows deduplicated or filled with synthetic values.',
        'validation': counts,
    }
    local_csv.with_suffix('.provenance.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    logs = project / 'logs/reproduction'
    logs.mkdir(parents=True, exist_ok=True)
    if original != patched:
        backup = logs / ('prepare_ports.' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.bak')
        shutil.copy2(script, backup)
        script.write_text(patched, encoding='utf-8')
        diff = ''.join(difflib.unified_diff(original.splitlines(True), patched.splitlines(True),
                                           fromfile='a/scripts/prepare_ports.py', tofile='b/scripts/prepare_ports.py'))
        (logs / 'ports-local-input.patch').write_text(diff, encoding='utf-8')
    print('READY:', local_csv)
    print('Original archive, provenance, and source backup retained. Run prepare_ports next.')

if __name__ == '__main__':
    main()
