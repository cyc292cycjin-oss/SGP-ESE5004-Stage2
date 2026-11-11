"""X20 §3 第 8 步：审阅包 REVIEW_<REPORT.md SHA256 前 8 位>.zip —— 规格、报告、桥表、CSV、脚本、EVIDENCE、evidence/，56 时段回归的不含许可证内容的小文件
（回执、验收、停止分类、Owen / M12 结果、剔除后的求解日志），以及仓库差异 26c2e47d..<提交>（scripts_project / configs / tests / 注册表片段，patch）、
差异统计与提交日志；不含网络文件、原始求解日志与 logs/。清单逐成员给出字节数、SHA256 与 CRC32。
打包后对每个成员做泄露扫描：模式只在运行时由环境变量 X20_LEAK_PATTERNS（正则，| 分隔）提供，脚本中不写任何模式；只打印成员名与命中数，不打印命中内容。
用法：X20_LEAK_PATTERNS='...' python x20_review_zip.py <提交>"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

W = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
R = Path("/home/jin/wt_v5_x20")
BASE = "26c2e47d025fdd4e46cb278718d93aeddabbe984"
PATHS = ["scripts_project", "configs", "tests", "research_inputs/registry_v5/fragments"]
SMOKE_FILES = ("SOLVE_RECEIPT.json", "V6_ACCEPTANCE.json", "STOP_CLASS.json", "V5_GATES.json", "PRECISION.json", "ALLOCATION.json", "ALLOCATION.csv",
               "COUNTRY_COST_LEDGER.csv", "HYDRO_SPILL.json", "RUN_STATUS.json", "BUNKER_CARBON_ATTRIBUTION.json", "BUNKER_CARBON_ATTRIBUTION.csv",
               "solve_log_scrubbed.txt", "solve_err_scrubbed.txt")


def main():
    commit = sys.argv[1]
    pat = os.environ.get("X20_LEAK_PATTERNS")
    if not pat:
        print("X20_LEAK_PATTERNS not set: refusing to pack without the leak scan"); sys.exit(2)
    rx = re.compile(pat, re.I)
    rep = (W / "REPORT.md").read_bytes(); rsha = hashlib.sha256(rep).hexdigest()
    diff = subprocess.run(["git", "-C", str(R), "diff", BASE, commit, "--", *PATHS], capture_output=True, text=True, check=True).stdout
    stat = subprocess.run(["git", "-C", str(R), "diff", "--stat", BASE, commit], capture_output=True, text=True, check=True).stdout
    log = subprocess.run(["git", "-C", str(R), "log", "--format=%H %s", f"{BASE}..{commit}"], capture_output=True, text=True, check=True).stdout
    extra = {f"repo/CODE_DIFF_{BASE[:8]}_{commit[:8]}.patch": diff.encode(), f"repo/DIFF_STAT_{BASE[:8]}_{commit[:8]}.txt": stat.encode(), "repo/GIT_LOG.txt": log.encode()}
    members = [p for p in sorted(W.glob("*")) if p.is_file() and p.suffix in (".md", ".csv", ".json", ".txt") and not p.name.startswith("REVIEW_")]
    members += [p for p in sorted((W / "evidence").glob("*")) if p.is_file() and not p.name.startswith("REVIEW_ZIP_MANIFEST")]
    members += [p for p in sorted((W / "scripts").glob("*")) if p.is_file() and not p.name.startswith("msg_")]
    members += [p for p in sorted((W / "smoke56").glob("*")) if p.is_file() and p.suffix in (".txt", ".json")]
    for rid in ("F1", "F2"):
        members += [W / "smoke56" / rid / f for f in SMOKE_FILES if (W / "smoke56" / rid / f).exists()]
        members += [p for p in sorted((W / "smoke56" / rid / "m12_owen").glob("*")) if p.is_file() and p.suffix in (".json", ".csv", ".md")]
    out = W / f"REVIEW_{rsha[:8]}.zip"
    man, hits = [], []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in members:
            b = p.read_bytes(); n = p.relative_to(W).as_posix()
            z.writestr(n, b); man.append((n, len(b), hashlib.sha256(b).hexdigest(), f"{zlib.crc32(b) & 0xffffffff:08x}"))
        for n, b in extra.items():
            z.writestr(n, b); man.append((n, len(b), hashlib.sha256(b).hexdigest(), f"{zlib.crc32(b) & 0xffffffff:08x}"))
        txt = "member\tbytes\tsha256\tcrc32\n" + "".join(f"{a}\t{b}\t{c}\t{d}\n" for a, b, c, d in man)
        z.writestr("MANIFEST.tsv", txt)
    with zipfile.ZipFile(out) as z:
        bad = z.testzip()
        for n in z.namelist():
            k = len(rx.findall(z.read(n).decode("utf-8", "replace")))
            if k:
                hits.append((n, k))
    (W / f"evidence/REVIEW_ZIP_MANIFEST_{rsha[:8]}.txt").write_text(txt)
    zsha = hashlib.sha256(out.read_bytes()).hexdigest()
    (W / "REVIEW_ZIP_SHA256.txt").write_text(f"{zsha}  {out.name}\nREPORT.md sha256 {rsha}\n")
    print(out.name, out.stat().st_size, zsha, "members", len(man) + 1, "testzip", bad, "report_sha256", rsha)
    print("LEAK_SCAN", "PASS" if not hits else "HITS", hits)
    if hits:
        sys.exit(3)


if __name__ == "__main__":
    main()
