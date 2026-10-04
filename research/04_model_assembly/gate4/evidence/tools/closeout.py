"""Push only Research and package committed Gate4 evidence. No model build/solve."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess as sp
import zipfile

W = Path(__file__).resolve().parent
E = W / 'evidence'
R = Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')

def git(*args):
    return sp.check_output(['git', *args], cwd=R, text=True).strip()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def refs(value):
    return {line.split('\t')[1]: line.split('\t')[0] for line in value.splitlines()}

base = json.loads((E / 'START.json').read_text())
audit = json.loads((E / 'AUDIT_COMMIT.json').read_text())
head = audit['head']
assert git('rev-parse', 'HEAD') == head
assert git('branch', '--show-current') == 'research/full-sc-baseline'
assert not git('status', '--porcelain')
before, pre = refs(base['remote_refs']), refs(git('ls-remote', 'origin'))
protected = {k: v for k, v in before.items() if k.startswith(('refs/heads/', 'refs/tags/')) and k != 'refs/heads/research/full-sc-baseline'}
assert all(pre.get(k) == v for k, v in protected.items())
assert pre['refs/heads/research/full-sc-baseline'] in (base['head'], head)
allow = set(json.loads((E / 'INTEGRATION_ALLOWLIST.json').read_text()))
prefix = 'research/04_model_assembly/gate4/'
changes = git('diff', '--name-only', base['head'], head).splitlines()
assert all(path in allow or path.startswith(prefix) for path in changes)
for rel, digest in base['gate2_hashes'].items():
    assert sha(R / rel) == digest
for rel, digest in json.loads((E / 'FINAL_IMPLEMENTATION_HASHES.json').read_text()).items():
    assert sha(R / rel) == digest
manifest = json.loads((R / prefix / 'PHASE4_FIRST_FULLSC_NETWORK_MANIFEST.json').read_text())
for rel, digest in manifest['config_sha256'].items():
    assert sha(R / rel) == digest
assert manifest['network_file'] is None and manifest['solver_runs'] == 0
out = W.parents[1] / 'outputs/phase4_gate4_20261005'
archive = out.with_suffix('.zip')
assert not out.exists() and not archive.exists(), 'Preserve any existing package; do not overwrite'
if pre['refs/heads/research/full-sc-baseline'] == base['head']:
    push = sp.run(['git', 'push', 'origin', 'HEAD:refs/heads/research/full-sc-baseline'],
                  cwd=R, stdout=sp.PIPE, stderr=sp.STDOUT)
    (E / 'push.log').write_bytes(push.stdout)
    print(push.stdout.decode())
    assert push.returncode == 0
else:
    assert (E / 'push.log').is_file(), 'Expected existing push receipt'
post = refs(git('ls-remote', 'origin'))
assert post['refs/heads/research/full-sc-baseline'] == head
assert all(post.get(k) == v for k, v in protected.items())
assert not git('status', '--porcelain')

mapping = {rel[len(prefix):]: rel for rel in git('ls-tree', '-r', '--name-only', head, '--', prefix).splitlines()}
for rel in sorted(allow | set(manifest['config'])):
    mapping['model_files/' + rel] = rel
out.mkdir(parents=True)
for name, rel in mapping.items():
    target = out / name
    target.parent.mkdir(parents=True, exist_ok=True)
    data = sp.check_output(['git', 'show', head + ':' + rel], cwd=R)
    target.write_bytes(data)
    assert sha(target) == sha(R / rel)
required = [
    'PHASE4_GATE4_START_IDENTITY.md', 'PHASE4_ASSEMBLY_INPUT_FREEZE.md',
    'PHASE4_ASSEMBLY_INPUT_REGISTRY.csv', 'PHASE4_TOPOLOGY_FIX_REPORT.md',
    'PHASE4_RESEARCH_BUILD_CONFIG.md', 'PHASE4_FIRST_FULLSC_NETWORK_MANIFEST.json',
    'PHASE4_NETWORK_COMPONENT_INVENTORY.csv', 'PHASE4_ACTUAL_DEMAND_CONSERVATION.csv',
    'PHASE4_ACTUAL_EXACTLY_ONCE_TESTS.csv', 'PHASE4_ACTUAL_CARRIER_REACHABILITY.csv',
    'PHASE4_ACTUAL_CARBON_ATTRIBUTION.csv', 'PHASE4_ACTUAL_ELECTRICITY_LINK_CLASSIFICATION.csv',
    'PHASE4_ACTIVE_SECTOR_COUPLING_PATHWAYS.csv', 'PHASE4_GATE4_BLOCKERS.csv',
    'PHASE4_GATE4_TEST_REPORT.md', 'PHASE4_GATE4_READINESS.md']
assert all((out / name).is_file() for name in required)
assert not list(out.rglob('*.nc'))
close = dict(completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    base_gate3=base['head'], final_head=head, tested_implementation=audit['tested_implementation'],
    branch='research/full-sc-baseline', remote_research_head=post['refs/heads/research/full-sc-baseline'],
    working_tree_clean=True, remote_main_unchanged=True, protected_refs_unchanged=protected,
    remote_before=pre, remote_after=post, changed_paths=changes, package_to_git_paths=mapping,
    all_package_git_bytes_verified=True, required_deliverables_present=16,
    solver_runs=0, full_network_assembly_runs=0, network_exported=False, network_file=None,
    topology_repair=True, gate4_pass=False, ready_for_gate5=False, scenario_switching=False,
    formal_scientific_results=False,
    package_scope='Audit delivery and changed project files/config snapshots; not a standalone runnable model checkout')
dump(out / 'CLOSEOUT.json', close)
(out / 'push.log').write_bytes((E / 'push.log').read_bytes())
(out / 'package_builder.py').write_bytes(Path(__file__).read_bytes())
hashes = {p.relative_to(out).as_posix(): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
dump(out / 'SHA256SUMS.json', hashes)
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for path in sorted(out.rglob('*')):
        if path.is_file():
            z.write(path, path.relative_to(out).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert set(z.namelist()) == set(hashes) | {'SHA256SUMS.json'}
    for name, digest in json.loads(z.read('SHA256SUMS.json')).items():
        assert hashlib.sha256(z.read(name)).hexdigest() == digest, name
    files = len(z.namelist())
receipt = dict(zip=str(archive), sha256=sha(archive), bytes=archive.stat().st_size,
    files=files, all_hashes_pass=True, zip_crc_pass=True, final_head=head,
    remote_main=post['refs/heads/main'], research_clean=not git('status', '--porcelain'),
    gate4_pass=False, network_exported=False, solver_runs=0)
dump(E / 'PACKAGE_RECEIPT.json', receipt)
archive.with_suffix('.zip.sha256').write_text(receipt['sha256'] + '  ' + archive.name + '\n')
print(json.dumps(receipt, indent=2))
