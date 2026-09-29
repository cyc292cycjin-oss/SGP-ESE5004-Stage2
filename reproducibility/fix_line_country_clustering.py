"""Install the project-local direction-aware line-country clustering adapter."""
import argparse
import difflib
from datetime import datetime
from pathlib import Path
import shutil

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    root = args.project.resolve()
    helper = Path(__file__).with_name('line_country_clustering.py').read_text(encoding='utf-8')
    compile(helper, 'line_country_clustering.py', 'exec')
    changes = []
    for name in ['simplify_network.py', 'cluster_network.py']:
        path = root / 'scripts' / name
        before = path.read_text(encoding='utf-8')
        if 'from line_country_clustering import get_clustering_from_busmap' in before:
            continue
        item = '    get_clustering_from_busmap,\n'
        anchor = 'from pypsa.clustering.spatial import ('
        if before.count(item) != 1 or before.count(anchor) != 1:
            raise SystemExit(f'Unexpected import layout in {name}; no files changed.')
        after = before.replace(item, '').replace(anchor,
            'from line_country_clustering import get_clustering_from_busmap\n' + anchor)
        network, output = ('n', 'snakemake.output.network') if name == 'simplify_network.py' else ('clustering.network', 'outputs.network')
        export = f'    {network}.export_to_netcdf({output})'
        if after.count(export) != 1:
            raise SystemExit(f'Unexpected export location in {name}; no files changed.')
        after = after.replace(export,
            '    # SGP: refresh derived labels after restoring national bus countries.\n'
            f'    if "country" in {network}.lines.columns:\n'
            f'        {network}.lines["country"] = {network}.lines["bus0"].map({network}.buses["country"])\n'
            + export)
        compile(after, str(path), 'exec')
        changes.append((path, before, after))
    destination = root / 'scripts/line_country_clustering.py'
    if destination.exists() and destination.read_text(encoding='utf-8') != helper:
        raise SystemExit('Existing adapter differs; refusing to overwrite it.')
    for path, before, after in changes:
        print(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
              fromfile='a/scripts/'+path.name, tofile='b/scripts/'+path.name)))
    if args.check_only:
        print('CHECK PASS: imports and syntax validated; project files unchanged.')
        return
    logs = root / 'logs/reproduction'
    logs.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    for path, before, after in changes:
        shutil.copy2(path, logs / (path.name + '.' + stamp + '.bak'))
        path.write_text(after, encoding='utf-8')
    destination.write_text(helper, encoding='utf-8')
    report = root / 'reproducibility/LINE_DIRECTION_FIX.md'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text('''# Direction-aware line country metadata

## Evidence
The prior blank-label repair succeeded (23 labels filled). The next failure
in simplify_network concerned lines 1274599202-1_0 and 1274599211-1_0.
Their respective bus0/bus1 pairs are 1098/2114 and 2114/1098; the endpoint
countries are VN/KH and KH/VN. Both original country labels follow bus0.
PyPSA 0.30.3 aggregatelines sorts the mapped endpoint IDs before grouping,
but retains the original direction-dependent country labels.

## Fix and scope
A project-local adapter recomputes only line.country using mapped, ordered
bus0 and the corresponding clustered bus country before delegating to the
original PyPSA function. Bus country consensus, all electrical strategies,
line groupings and bus mapping remain active. The input line table is restored
in a finally block. Both simplify_network and cluster_network use the adapter.
Before exporting, line.country is refreshed from bus0 again after the workflow
has restored national bus countries from temporary subregion classifications.
The installed PyPSA library is not edited; the earlier missing-label fix stays.

## Verified checks
- Original opposite-direction country assertion reproduced in a two-bus test.
- Adapter succeeds with identity and order-reversing cluster IDs.
- Input line table is restored unchanged.
- Every non-country aggregated line attribute matches original PyPSA on the
  same small network with the redundant country column omitted.
- The real conflicting VN/KH pair passes with the workflow's existing
  descriptive-field aggregation strategies.

These checks do not establish full workflow success or paper equivalence.
Next run only the concrete elec_s.nc target, retaining the low-memory settings.
Do not force add_transmission_projects again: its repaired output already exists.
Save the new log and exit code and commit this repair separately after review.
''', encoding='utf-8')
    print('APPLIED: adapter, import changes, backups and LINE_DIRECTION_FIX.md saved.')

if __name__ == '__main__':
    main()
