"""将 C10（原样）与 D 阶段轻量证据暂存进研究仓库（不 commit/push）。由 c09_stage_git.py 改写。

python d_stage_git.py c10 | d
公开仓库：许可证注册行脱敏（数值行不变），原始/公开 SHA 记录；数组、NetCDF、归档不入库；>4 MB 文件不入库并记录路径/大小/SHA；
每个文件扫描凭据与邮箱。
"""
from pathlib import Path
import sys, json, hashlib, re, subprocess

REPO = Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model'); EVO = REPO / 'research/05_baseline_evolution/20261011'
WORK = Path('/mnt/d/ResearchWorkspaces/ASEAN/work'); W = WORK / 'd_stage_2920_20261013'; W10 = WORK / 'c10_rigorous_bound_20261013'
OUTS = Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/d_2920_diagnostic')
BRANCH = 'codex/d-stage-2920-20261013'
LEDGERS = ['research/05_baseline_evolution/20261011/BASELINE_EVOLUTION_LEDGER.md', 'research/STAGE2_PROJECT_LEDGER.md',
           'research/05_baseline_evolution/20261011/b03_c00/C00_GO_NO_GO_CHECKLIST.md']
REDACTED = '[REDACTED: license registration metadata; numerical lines unchanged]'
SENS = re.compile(rb'Academic\x20license|registered\x20to|u\.nus\.edu|PRIVATE\x20KEY-----|gh[p]_|github_pa[t]_|gh[o]_|(?:WLSSECRE[T]|WLSACCESSI[D]|LICENSEI[D])"?\s*[:=]\s*"?[0-9A-Za-z-]{6,}', re.I)  # name followed by a real value; bare parameter names are not secrets
LIC = re.compile(r'Academic\x20license|registered\x20to')
BULK = ('.npy', '.npz', '.nc', '.lic', '.zip', '.gz', '.tar', '.so', '.pyc', '.partial')
LIMIT = 4_000_000
sha = lambda b: hashlib.sha256(b).hexdigest()
excluded, prov = [], []


def git(*a): return subprocess.check_output(['git', '-C', str(REPO), *a]).decode().strip()


def put(dest, data, src=''):
    assert not dest.exists(), dest
    if dest.suffix.lower() in BULK or len(data) >= LIMIT:
        excluded.append({'would_be': str(dest.relative_to(REPO)), 'source': src, 'bytes': len(data), 'sha256': sha(data)}); return
    assert not SENS.search(data), 'SENSITIVE ' + str(dest)
    dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)


def redact_text(data):
    lines = data.decode('utf-8', errors='strict').split('\n'); hit = [i + 1 for i, s in enumerate(lines) if LIC.search(s)]
    for i in hit: lines[i - 1] = REDACTED
    return '\n'.join(lines).encode('utf-8'), hit


def redact_json(data):
    s = data.decode('utf-8'); hit = len(LIC.findall(s))
    if not hit: return data, 0
    v = json.loads(s)
    def walk(o):
        if isinstance(o, dict): return {k: walk(x) for k, x in o.items()}
        if isinstance(o, list): return [walk(x) for x in o]
        if isinstance(o, str) and LIC.search(o): return REDACTED
        return o
    return (json.dumps(walk(v), indent=2) + '\n').encode('utf-8'), hit


def copy_tree(src, dst, skip=()):
    for p in sorted(src.rglob('*')):
        if not p.is_file() or any(s in p.parts for s in skip) or '__pycache__' in p.parts: continue
        data = p.read_bytes(); rel = p.relative_to(src).as_posix(); target = dst / rel
        if SENS.search(data):
            if p.suffix == '.json': pub, hit = redact_json(data)
            elif p.suffix in ('.log', '.txt', '.md', '.jsonl'): pub, hit = redact_text(data)
            else: raise AssertionError('SENSITIVE_UNHANDLED ' + str(p))
            if p.suffix == '.log': target = target.with_name(target.stem + '.redacted.log')
            prov.append({'public': str(target.relative_to(REPO)), 'original': str(p), 'original_sha256': sha(data), 'public_sha256': sha(pub), 'redacted': hit}); data = pub
        elif p.suffix == '.log': target = target.with_name(target.stem + '.redacted.log')
        put(target, data, str(p))


def append_ledgers(entry, marker):
    for rel in LEDGERS:
        p = REPO / rel; s = p.read_text(encoding='utf-8'); assert marker not in s, rel
        p.write_text(s + '\n\n' + entry.strip('\n') + '\n', encoding='utf-8')


def stage_c10():
    assert git('branch', '--show-current') == BRANCH and not git('status', '--porcelain')
    O = EVO / 'c10'; assert not O.exists(); man = json.loads((W10 / 'PACKAGE_MANIFEST.json').read_text()); omitted = []
    for m in man['members']:
        data = (W10 / m['path']).read_bytes(); assert len(data) == m['bytes'] and sha(data) == m['sha256'], m['path']
        if Path(m['path']).suffix in BULK: omitted.append(m); continue
        put(O / m['path'], data)
    for p in sorted((W10 / 'methods').glob('*.py')):
        if not (O / 'methods' / p.name).exists(): put(O / 'methods' / p.name, p.read_bytes())
    put(O / 'PACKAGE_MANIFEST.json', (W10 / 'PACKAGE_MANIFEST.json').read_bytes())
    put(O / 'C10_GIT_OMITTED_BULK.json', (json.dumps({'omitted_members': omitted, 'reason': 'array files are not committed; bytes/SHA from PACKAGE_MANIFEST'}, indent=1) + '\n').encode())
    put(O / '.gitattributes', b'# Preserve exact evidence bytes; SHA identities are contractual.\n** -text\n')
    entry = (W10 / 'C10_LEDGER_ENTRY.md').read_text(encoding='utf-8').rstrip('\n') + (
        '\n- 补记（2026-10-13）：C10 报告、证据与方法随分支 `' + BRANCH + '` 入库于 `research/05_baseline_evolution/20261011/c10/`；成员字节与 PACKAGE_MANIFEST 一致（界数组 npz 不入库）；以上条目原文未改。\n')
    append_ledgers(entry, '## C10 日基线严格下界证书'); print('C10 staged')


def stage_d():
    assert git('branch', '--show-current') == BRANCH and not git('status', '--porcelain')
    O = EVO / 'd_stage'; assert not O.exists()
    for p in sorted(W.iterdir()):
        if p.is_file() and p.suffix in ('.md', '.json', '.py', '.txt') and p.name != 'D_STATUS_LOOP_STOP':
            data = p.read_bytes()
            if SENS.search(data):
                pub, hit = (redact_json(data) if p.suffix == '.json' else redact_text(data))
                prov.append({'public': str((O / p.name).relative_to(REPO)), 'original': str(p), 'original_sha256': sha(data), 'public_sha256': sha(pub), 'redacted': hit}); data = pub
            put(O / p.name, data, str(p))
    for sub, skip in [('methods', ()), ('tools', ()), ('release_d1', ('_c02r_original',)), ('release_d2', ()), ('release_d5', ()), ('release_d5b', ()), ('release_d6', ()),
                      ('evidence', ()), ('d1_light', ()), ('monitor_snapshots', ()), ('claude_review', ())]:
        if (W / sub).exists(): copy_tree(W / sub, O / sub, skip)
    rid = json.loads((W / 'D5_LAUNCH_RECEIPT.json').read_text())['run_id']; RUN = OUTS / rid / 'cloud_run'
    for p in sorted(RUN.rglob('*')):
        if not p.is_file() or p.suffix.lower() in BULK: continue
        rel = p.relative_to(RUN).as_posix(); data = p.read_bytes(); dest = O / 'evidence/d5_run' / rel
        if p.suffix == '.log':
            pub, hit = redact_text(data); dest = dest.with_name(dest.stem + '.redacted.log')
            prov.append({'public': str(dest.relative_to(REPO)), 'original': str(p), 'original_sha256': sha(data), 'public_sha256': sha(pub), 'redacted': hit}); data = pub
        put(dest, data, str(p))
    put(O / 'D_PUBLIC_EVIDENCE_PROVENANCE.json', (json.dumps({'rule': 'Only license registration metadata lines/strings are replaced; numerical lines unchanged.', 'redactions': prov}, indent=1) + '\n').encode())
    put(O / 'D_EXCLUDED_LARGE_FILES.json', (json.dumps({'rule': 'arrays/NetCDF/archives and files >= 4,000,000 bytes are not committed; originals in LOCAL_BACKUP_SHA_VERIFIED outputs or the local work directory', 'files': excluded}, indent=1) + '\n').encode())
    put(O / '.gitattributes', b'# Preserve exact evidence and production source bytes; SHA identities are contractual.\n** -text\n')
    files = [dict(relative=p.relative_to(O).as_posix(), bytes=p.stat().st_size, sha256=sha(p.read_bytes())) for p in sorted(O.rglob('*')) if p.is_file()]
    put(O / 'D_EVIDENCE_INDEX.json', (json.dumps({'run_id': rid, 'files': files, 'decision': 'DR1_GATE6_2920_BASELINE_ACCEPTED', 'builds': 1, 'optimization_calls': 1,
                                                  'large_arrays_included': False, 'formal_V4_changed': False}, indent=1) + '\n').encode())
    append_ledgers((W / 'D_STAGE_LEDGER_ENTRY.md').read_text(encoding='utf-8'), '## D 阶段：2920×3h 方案 A 模型的精确分解求解')
    print('D staged', len(files) + 1, 'files; excluded', len(excluded), '; redactions', len(prov))


if __name__ == '__main__':
    {'c10': stage_c10, 'd': stage_d}[sys.argv[1]]()
