"""V4 W20 review package (after scripts/d2c_review_zip.py): REVIEW_<commit8>.zip of the delivery folder (zip files, commit-message files and __pycache__
excluded) plus the repository diff ac75354c (W14 head = W20 start)..<commit> of scripts_project / configs / tests (patch), diff stat and log; manifest with
SHA256 and CRC32 per member. The zip is not committed.

    /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w20_review_zip.py <commit>
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

W = Path(__file__).resolve().parents[1]
R = Path("/home/jin/wt_v4_w20")
BASE = "ac75354c"
PATHS = ["scripts_project", "configs", "tests", "research_inputs"]


def main():
    commit = sys.argv[1]
    diff = subprocess.run(["git", "-C", str(R), "diff", BASE, commit, "--", *PATHS], capture_output=True, text=True, check=True).stdout
    stat = subprocess.run(["git", "-C", str(R), "diff", "--stat", BASE, commit], capture_output=True, text=True, check=True).stdout
    log = subprocess.run(["git", "-C", str(R), "log", "--format=%H %s", f"{BASE}..{commit}"], capture_output=True, text=True, check=True).stdout
    extra = {f"repo/CODE_DIFF_{BASE}.patch": diff.encode(), f"repo/DIFF_STAT_{BASE}.txt": stat.encode(), "repo/GIT_LOG.txt": log.encode()}
    members = [p for p in sorted(W.rglob("*")) if p.is_file() and p.suffix != ".zip" and not p.name.startswith("msg_") and "__pycache__" not in p.parts]
    out = W / f"REVIEW_{commit[:8]}.zip"
    man = []
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
    (W / "evidence").mkdir(exist_ok=True)
    (W / f"evidence/REVIEW_ZIP_MANIFEST_{commit[:8]}.txt").write_text(txt)
    print(out.name, out.stat().st_size, hashlib.sha256(out.read_bytes()).hexdigest(), "members", len(man) + 1, "testzip", bad)


if __name__ == "__main__":
    main()
