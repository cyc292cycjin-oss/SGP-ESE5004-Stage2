"""Apply the base-network bus0 country convention to unlabeled added lines."""
import argparse
import difflib
from datetime import datetime
from pathlib import Path
import shutil

BLOCK = '''    # SGP: follow base_network's bus0 convention for missing line country labels.
    missing_country = n.lines["country"].fillna("").eq("")
    inferred_country = n.lines.loc[missing_country, "bus0"].map(n.buses["country"])
    if inferred_country.fillna("").eq("").any():
        raise ValueError("Cannot label added lines: bus0 country is missing")
    n.lines.loc[missing_country, "country"] = inferred_country
    logger.info("Filled country metadata for %s lines from bus0", int(missing_country.sum()))

'''

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    root = args.project.resolve()
    script = root / 'scripts/add_transmission_projects.py'
    before = script.read_text(encoding='utf-8')
    if '# SGP: follow base_network' in before:
        print('Already applied; no files changed.')
        return
    anchor = '    n.export_to_netcdf(snakemake.output[0])'
    if before.count(anchor) != 1:
        raise SystemExit('Unexpected source version: no files changed.')
    after = before.replace(anchor, BLOCK + anchor)
    compile(after, str(script), 'exec')
    diff = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                       fromfile='a/scripts/add_transmission_projects.py',
                                       tofile='b/scripts/add_transmission_projects.py'))
    print(diff)
    if args.check_only:
        print('CHECK PASS: source insertion and Python syntax verified; no project files changed.')
        return
    logs = root / 'logs/reproduction'
    logs.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    shutil.copy2(script, logs / f'add_transmission_projects.{stamp}.bak')
    script.write_text(after, encoding='utf-8')
    (logs / 'transmission-country-fix.patch').write_text(diff, encoding='utf-8')
    report = root / 'reproducibility/LINE_COUNTRY_FIX.md'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text('''# Added transmission-line country metadata repair

## Problem and evidence
On 2026-09-29 the tutorial failed in simplify_network with a country-consensus
assertion. Four existing lines were MY; Mambong – Bengkayang had a blank label.
The latter connects an MY bus0 to an ID bus1. In this upstream version,
base_network.py defines line.country from bus0 country, not as proof that the
line lies within one country. add_transmission_projects.py omitted this label.

## Change
Fill only blank/NaN line.country from bus0 after transmission projects have
been attached, before exporting the network. Fail if the bus country is absent.
Do not change bus0/bus1, capacities, impedances, voltages, lengths or project selection.

## Validation and limits
An in-memory check on the failed elec.nc found 23 missing labels. All could be
filled. Every other line column, the complete bus table and existing nonblank
country labels remained identical. The named interconnector remained MY–ID.
Source insertion and Python syntax were checked. This is not a successful
end-to-end workflow run or a demonstration of paper-result equivalence.

## Next run
Run simplify_network with the same three tutorial configuration files and
low-memory resource setting. Force add_transmission_projects once so dependent
networks are regenerated. Save the complete log and exit code, and record any
subsequent failure separately. Commit this repair separately after verification.
''', encoding='utf-8')
    print('APPLIED. Backup, diff, and reproducibility/LINE_COUNTRY_FIX.md saved.')

if __name__ == '__main__':
    main()
