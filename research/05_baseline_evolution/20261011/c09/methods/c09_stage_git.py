"""Stage C08 (unchanged, SHA-checked) and C09 light evidence into the research repo. No git commit/push here.

Run in WSL:  python c09_stage_git.py c08|c09
Public repo: license registration lines are redacted (numerical lines unchanged); original and public SHA recorded.
Excludes arrays, NetCDF, archives; every staged file < 4 MB and scanned for credentials/e-mail.
"""
from pathlib import Path
import sys, json, hashlib, shutil, re, subprocess

REPO = Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
EVO = REPO / 'research/05_baseline_evolution/20261011'
WORK = Path('/mnt/d/ResearchWorkspaces/ASEAN/work'); W8 = WORK / 'c08_block_decomposition_20261013'; W9 = WORK / 'c09_exact_decomposition_20261013'
OUTS = Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/c09_daily_diagnostic')
BRANCH = 'codex/c09-exact-decomposition-20261013'
LEDGERS = ['research/05_baseline_evolution/20261011/BASELINE_EVOLUTION_LEDGER.md', 'research/STAGE2_PROJECT_LEDGER.md',
           'research/05_baseline_evolution/20261011/b03_c00/C00_GO_NO_GO_CHECKLIST.md']
REDACTED = '[REDACTED: license registration metadata; numerical lines unchanged]'
SENSITIVE = re.compile(rb'Academic\x20license|registered\x20to|u\.nus\.edu|PRIVATE\x20KEY-----|gh[p]_|github_pa[t]_|gh[o]_|WLSSECRE[T]|WLSACCESSI[D]|LICENSEI[D]', re.I)
BULK = ('.npy', '.npz', '.nc', '.lic', '.zip', '.gz', '.tar', '.so', '.pyc', '.partial')
sha = lambda b: hashlib.sha256(b).hexdigest()


def git(*a): return subprocess.check_output(['git', '-C', str(REPO), *a]).decode().strip()


def put(dest, data):
    assert not dest.exists(), dest
    assert dest.suffix.lower() not in BULK and len(data) < 4_000_000, dest
    assert not SENSITIVE.search(data), 'SENSITIVE ' + str(dest)
    dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)


def redact_text(data):
    lines = data.decode('utf-8').split('\n'); hit = []
    for i, s in enumerate(lines):
        if re.search(r'Academic\x20license|registered\x20to', s): lines[i] = REDACTED; hit.append(i + 1)
    return '\n'.join(lines).encode('utf-8'), hit


def redact_snapshot(data):
    v = json.loads(data); hit = []
    tail = (v.get('log') or {}).get('tail') or []
    for i, s in enumerate(tail):
        if re.search(r'Academic\x20license|registered\x20to', s): tail[i] = REDACTED; hit.append(i)
    return (json.dumps(v, indent=2) + '\n').encode('utf-8'), hit


def append_ledgers(entry, marker):
    for rel in LEDGERS:
        p = REPO / rel; s = p.read_text(encoding='utf-8'); assert marker not in s, rel
        p.write_text(s + '\n\n' + entry.strip('\n') + '\n', encoding='utf-8')


def stage_c08():
    assert git('branch', '--show-current') == BRANCH and not git('status', '--porcelain')
    O = EVO / 'c08'; assert not O.exists()
    man = json.loads((W8 / 'PACKAGE_MANIFEST.json').read_text())
    for m in man['members']:
        data = (W8 / m['path']).read_bytes(); assert len(data) == m['bytes'] and sha(data) == m['sha256'], m['path']
        put(O / m['path'], data)
    put(O / 'PACKAGE_MANIFEST.json', (W8 / 'PACKAGE_MANIFEST.json').read_bytes())
    put(O / '.gitattributes', b'# Preserve exact evidence bytes; SHA identities are contractual.\n** -text\n')
    entry = (W8 / 'C08_LEDGER_ENTRY.md').read_text(encoding='utf-8').rstrip('\n') + (
        '\n- 补记（2026-10-13）：C08 报告、证据和方法随分支 `' + BRANCH + '` 入库于 `research/05_baseline_evolution/20261011/c08/`，'
        '成员字节与 PACKAGE_MANIFEST 中的 SHA 逐个一致；以上条目原文未改。\n')
    append_ledgers(entry, '## C08 日模型根因核实')
    print('C08 staged', len(man['members']) + 2, 'files')


def stage_c09():
    assert git('branch', '--show-current') == BRANCH and not git('status', '--porcelain')
    O = EVO / 'c09'; assert not O.exists()
    rid = json.loads((W9 / 'LAUNCH_RECEIPT.json').read_text())['run_id']; RUN = OUTS / rid / 'cloud_run'
    prov = []
    top = ['C09_RESULT.md', 'C09_LEDGER_ENTRY.md', 'C09_EXECUTION_GUIDE.md', 'C09_CLAUDE_CODE_TASK.md', 'C09_APPROVAL_RECORD.json',
           'C09_BLOCK_PRIMAL_RECEIPT.json', 'C09_DRYRUN_V4_ALGEBRA.json', 'C09_LOCAL_TESTS.json', 'C09_RELEASE_MANIFEST.json',
           'RELEASE_DELIVERY.json', 'c09_control.py', 'DEPLOYMENT_RECEIPT.json', 'START_ATTEMPT.json', 'START_STDOUT.txt',
           'START_STDERR.txt', 'LAUNCH_RECEIPT.json', 'FETCH_WINDOW.json', 'FETCH_RECEIPT.json', 'C09_LOCAL_BACKUP_RECEIPT.json',
           'C09_LOCAL_V4_RECHECK.json', 'C09_COMPARISON.json']
    for n in top: put(O / n, (W9 / n).read_bytes())
    for p in sorted((W9 / 'methods').glob('*.py')): put(O / 'methods' / p.name, p.read_bytes())
    for p in sorted((W9 / 'monitor_snapshots').glob('*.json')):
        data = p.read_bytes(); pub, hit = redact_snapshot(data) if SENSITIVE.search(data) else (data, [])
        put(O / 'monitor_snapshots' / p.name, pub)
        if hit: prov.append(dict(public='monitor_snapshots/' + p.name, original=str(p), original_sha256=sha(data), public_sha256=sha(pub), redacted_log_tail_indices=hit))
    for p in sorted(RUN.rglob('*')):
        if not p.is_file() or p.suffix.lower() in BULK: continue
        rel = p.relative_to(RUN).as_posix(); data = p.read_bytes()
        if p.suffix == '.log':
            pub, hit = redact_text(data); dest = 'evidence/run/' + rel[:-4] + '.redacted.log'
            prov.append(dict(public=dest, original='outputs/c09_daily_diagnostic/' + rid + '/cloud_run/' + rel, original_sha256=sha(data), public_sha256=sha(pub), redacted_lines=hit))
        else:
            pub, dest = data, 'evidence/run/' + rel
        put(O / dest, pub)
    put(O / 'C09_PUBLIC_EVIDENCE_PROVENANCE.json', (json.dumps(dict(
        rule='Only license registration metadata lines are replaced; numerical lines and all other bytes unchanged. Excluded from Git: .npy/.nc arrays and archives (in LOCAL_BACKUP_SHA_VERIFIED outputs).',
        redactions=prov, run_id=rid), indent=2) + '\n').encode())
    put(O / '.gitattributes', b'# Preserve exact evidence and production source bytes; SHA identities are contractual.\n** -text\n')
    files = [dict(relative=p.relative_to(O).as_posix(), bytes=p.stat().st_size, sha256=sha(p.read_bytes())) for p in sorted(O.rglob('*')) if p.is_file()]
    put(O / 'C09_EVIDENCE_INDEX.json', (json.dumps(dict(run_id=rid, files=files, large_arrays_included=False, formal_V4_changed=False,
                                                        optimization_calls=1, decision='R1_C09_DAILY_BASELINE_ACCEPTED_DAILY_DIAGNOSTIC_ONLY',
                                                        local_backup='LOCAL_BACKUP_SHA_VERIFIED'), indent=2) + '\n').encode())
    append_ledgers((W9 / 'C09_LEDGER_ENTRY.md').read_text(encoding='utf-8'), '## C09 精确分解后主 LP 单次求解')
    print('C09 staged', len(files) + 1, 'files;', 'redactions', len([r for r in prov if r.get('redacted_lines') or r.get('redacted_log_tail_indices')]))


if __name__ == '__main__':
    {'c08': stage_c08, 'c09': stage_c09}[sys.argv[1]]()
