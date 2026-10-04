"""Verify Gate4 reports and commit audit evidence; never build, solve or push."""
from pathlib import Path
import csv
import decimal
import hashlib
import json
import shutil
import subprocess as sp
import sys
import yaml

W = Path(__file__).resolve().parent
S, E = W / 'stage', W / 'evidence'
R = Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
G = S / 'research/04_model_assembly/gate4'
GE = G / 'evidence'

def git(*args):
    return sp.check_output(['git', *args], cwd=R, text=True).strip()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def refs(value):
    return {line.split('\t')[1]: line.split('\t')[0] for line in value.splitlines()}

start = json.loads((E / 'START.json').read_text())
head = json.loads((E / 'INPUT_COMMITS.json').read_text())[-1]['head']
assert git('rev-parse', 'HEAD') == head
assert git('branch', '--show-current') == 'research/full-sc-baseline'
if git('status', '--porcelain'):
    # Resume only this script's previously verified report staging after a
    # pre-commit completeness check; never absorb unrelated working changes.
    staged_retry = git('diff', '--cached', '--name-only').splitlines()
    assert staged_retry and all(p.startswith('research/04_model_assembly/gate4/') for p in staged_retry)
    assert not git('diff', '--name-only')
    for rel in staged_retry:
        data = sp.check_output(['git', 'show', ':' + rel], cwd=R)
        assert hashlib.sha256(data).hexdigest() == sha(S / rel), rel
before, remote = refs(start['remote_refs']), refs(git('ls-remote', 'origin'))
protected = {k: v for k, v in before.items() if k.startswith(('refs/heads/', 'refs/tags/')) and k != 'refs/heads/research/full-sc-baseline'}
assert all(remote.get(k) == v for k, v in protected.items())
assert remote['refs/heads/research/full-sc-baseline'] == start['head']

allow = set(json.loads((E / 'TOPOLOGY_COMMIT.json').read_text())['paths'])
allow.update(p.relative_to(S).as_posix() for p in (S / 'research_inputs/assembly_v1').rglob('*') if p.is_file())
allow.update(['scripts_project/check_assembly_inputs.py', 'tests/research/test_assembly_input_freeze.py',
              'configs/research/baseline.yaml', 'configs/research/composition.json'])
changes = git('diff', '--name-only', start['head'], head).splitlines()
assert set(changes) == allow, (changes, sorted(allow))
dump(E / 'INTEGRATION_ALLOWLIST.json', sorted(allow))
implementation_hashes = {rel: sha(R / rel) for rel in sorted(allow)}
dump(E / 'FINAL_IMPLEMENTATION_HASHES.json', implementation_hashes)
(E / 'FINAL_IMPLEMENTATION.diff').write_bytes(sp.check_output(['git', 'diff', start['head'], head, '--', *sorted(allow)], cwd=R))
guard = {rel: sha(R / rel) == digest for rel, digest in start['gate2_hashes'].items()}
assert all(guard.values())
old_config = yaml.safe_load(sp.check_output(['git', 'show', start['head'] + ':configs/research/baseline.yaml'], cwd=R))
new_config = yaml.safe_load((R / 'configs/research/baseline.yaml').read_text())
assert all(new_config[k] == v for k, v in old_config.items())
assert not any(rel.startswith(('scripts/', 'tests/buildings/', 'tests/shipping/')) for rel in changes)
upstream_source = 'scripts/prepare_sector_network.py'
assert sha(R / upstream_source) == '05a000c45f5b18a3a91ad5c0bf900274ba2bf560d84517545a7975fac8e8155e'

# Preserve both the initial and current effective configuration, clearly named.
sys.path.insert(0, str(R / 'scripts_project'))
from phase4_static import config, json_evidence
dump(E / 'EFFECTIVE_CONFIG_AFTER.json', json_evidence(config(R)))
composition = json.loads((R / 'configs/research/composition.json').read_text())
config_files = composition['base_files'] + composition['identities']['baseline'] + ['configs/research/composition.json']
config_hashes = {rel: sha(R / rel) for rel in config_files}
manifest_path = G / 'PHASE4_FIRST_FULLSC_NETWORK_MANIFEST.json'
manifest = json.loads(manifest_path.read_text())
manifest['config'] = config_files
manifest['config_sha256'] = config_hashes
manifest['git_commit_role'] = 'tested_input_preflight_commit; not a network build commit'
manifest['carbon_architecture_version'] = '631b27bb92e68cc974fe17f15206f86727cade9e'
manifest['carrier_architecture_version'] = '140294807bffe5cc172d5226ee0af3d4f548d180'
manifest['requested_metadata_fields'] = ['year', 'weather_year', 'spatial_resolution']
manifest['effective_config_after_sha256'] = sha(E / 'EFFECTIVE_CONFIG_AFTER.json')
assert manifest['network_file'] is None and manifest['network_sha256'] is None
assert manifest['solver_status'] == 'NOT_RUN' and manifest['solver_runs'] == 0
assert manifest['input_registry_sha256'] == sha(R / 'research_inputs/assembly_v1/registry.json')
for key in ['carbon_architecture_version', 'carrier_architecture_version']:
    assert git('rev-parse', manifest[key] + '^{commit}') == manifest[key]
dump(manifest_path, manifest)

tables = json.loads((W / 'build/tables.json').read_text())
checks = []
for name, table in tables.items():
    with (G / name).open(encoding='utf-8-sig', newline='') as handle:
        data = list(csv.reader(handle))
    expected = table['export_values']
    assert len(data) == len(expected), name
    for ri, (row, source) in enumerate(zip(data, expected)):
        assert len(row) == len(source)
        for ci, (value, previous) in enumerate(zip(row, source)):
            if isinstance(previous, bool):
                assert value == str(previous).lower(), (name, ri, ci)
            elif isinstance(previous, (int, float)):
                assert decimal.Decimal(value) == decimal.Decimal(str(previous)), (name, ri, ci)
            else:
                assert value == previous, (name, ri, ci, value, previous)
    checks.append(dict(file=name, rows=len(data)-1, exact_source_values=True, sha256=sha(G / name)))
assert len(checks) == 9
dump(E / 'CSV_VALUE_CHECK.json', checks)

# Existing tests are reused only where tracked source is unchanged; no repeat solve.
prior_dir = GE / 'prior_gate_design'
prior_dir.mkdir(exist_ok=True)
prior = []
for rel in [
    'research/04_model_assembly/gate2/RESEARCH_DEMAND_ACCOUNTING_SPEC.md',
    'research/04_model_assembly/gate2/RESEARCH_ELECTRICITY_PARENT_ASTAR.md',
    'research/04_model_assembly/gate3/PHASE4_GATE3_TEST_REPORT.md',
    'research/04_model_assembly/gate3/PHASE4_GATE3_READINESS.md',
    'research/04_model_assembly/gate3/PHASE4_CARBON_ACCOUNTING_ARCHITECTURE.md',
]:
    path = R / rel
    assert path.is_file(), rel
    frozen = sp.check_output(['git', 'show', start['head'] + ':' + rel], cwd=R)
    assert hashlib.sha256(frozen).hexdigest() == sha(path)
    shutil.copyfile(path, prior_dir / path.name)
    prior.append(dict(file=rel, sha256=sha(path), commit=git('log', '-1', '--format=%H', '--', rel)))
dump(E / 'PRIOR_EVIDENCE_REUSE.json', dict(documents=prior, unchanged_model_source_sha256=sha(R / upstream_source),
     code_change_scope='Only new Gate4 project code plus one raw transformer row; prior buildings/shipping/accounting/carbon source untouched'))
dump(E / 'FINAL_DIFF_REVIEW.json', dict(base=start['head'], tested_implementation=head,
     changed_files=changes, only_allowlisted_files=True, upstream_code_unchanged=True,
     upstream_raw_topology_one_row_removed=True, gate2_hashes_preserved=guard,
     prior_research_config_blocks_unchanged=True, protected_refs=protected,
     csv_exact_values_pass=True, config_hashes=config_hashes, solver_runs=0,
     full_network_assemblies=0, gate4_pass=False))

for path in E.rglob('*'):
    if path.is_file() and path.name not in ('AUDIT_COMMIT.json', 'PACKAGE_RECEIPT.json', 'push.log'):
        target = GE / path.relative_to(E)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
for name in ['export_tables.mjs', 'finalize_audit.py', 'closeout.py']:
    shutil.copyfile(W / name, GE / 'tools' / name)
# Version only these nine small review previews despite the global PNG ignore.
ignore = G / '.gitignore'
ignore_text = ignore.read_text()
if '!evidence/previews/*.png' not in ignore_text:
    ignore.write_text(ignore_text.rstrip() + '\n!evidence/previews/*.png\n')
dump(GE / 'EVIDENCE_HASHES.json', {p.relative_to(GE).as_posix(): sha(p) for p in sorted(GE.rglob('*'))
                               if p.is_file() and p.name != 'EVIDENCE_HASHES.json'})
for path in G.rglob('*'):
    if path.is_file():
        rel = path.relative_to(S)
        target = R / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        target.chmod(0o644)
sp.run(['git', 'add', '--', 'research/04_model_assembly/gate4'], cwd=R, check=True)
staged = git('diff', '--cached', '--name-only').splitlines()
assert staged and all(p.startswith('research/04_model_assembly/gate4/') for p in staged)
assert set(staged) == {p.relative_to(S).as_posix() for p in G.rglob('*') if p.is_file()}, 'Report files must all be staged before commit'
assert not git('diff', '--name-only')
message = ('audit: report Gate4 input stop and topology validation\n\n'
           'Deliver all 16 requested evidence files with actual-network checks explicitly\n'
           'NOT_RUN. Freeze only source-qualified anchors and controls; consolidate\n'
           'target-year, external-supply and carbon-attribution gaps. Preserve prior\n'
           'contracts, exact CSV values, topology provenance and current config hashes.\n'
           'No Full-SC network was built, no scenario switched and no solver run.')
sp.run(['git', '-c', 'user.name=cyc292cycjin-oss', '-c',
        'user.email=329621298+cyc292cycjin-oss@users.noreply.github.com', 'commit', '-m', message], cwd=R, check=True)
assert not git('status', '--porcelain')
for path in G.rglob('*'):
    if path.is_file():
        rel = path.relative_to(S).as_posix()
        data = sp.check_output(['git', 'show', 'HEAD:' + rel], cwd=R)
        assert hashlib.sha256(data).hexdigest() == sha(path), ('Git byte mismatch', rel)
result = dict(head=git('rev-parse', 'HEAD'), tested_implementation=head, branch=git('branch', '--show-current'),
              clean=True, report_git_bytes_verified=True, gate4_pass=False)
dump(E / 'AUDIT_COMMIT.json', result)
print(json.dumps(result, indent=2))
