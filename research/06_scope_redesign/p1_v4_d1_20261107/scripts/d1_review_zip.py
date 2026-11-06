"""V4 D1 review package (copy of W08 w08_review_zip.py): REVIEW_<commit8>.zip of the delivery folder (zip files, logs and commit-message files excluded) plus the repository diff
7aa356e4..<commit> of scripts_project / configs / tests (patch), diff stat and log; manifest with SHA256 and CRC32 per member.

    /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/d1_review_zip.py <commit>
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

W = Path(__file__).resolve().parents[1]
R = Path("/home/jin/wt_v4_d1")


def main():
    commit = sys.argv[1]
    diff = subprocess.run(["git", "-C", str(R), "diff", "7aa356e4", commit, "--", "scripts_project", "configs", "tests"], capture_output=True, text=True, check=True).stdout
    stat = subprocess.run(["git", "-C", str(R), "diff", "--stat", "7aa356e4", commit], capture_output=True, text=True, check=True).stdout
    log = subprocess.run(["git", "-C", str(R), "log", "--format=%H %s", f"7aa356e4..{commit}"], capture_output=True, text=True, check=True).stdout
    extra = {"repo/CODE_DIFF_7aa356e4.patch": diff.encode(), "repo/DIFF_STAT_7aa356e4.txt": stat.encode(), "repo/GIT_LOG.txt": log.encode()}
    members = [p for p in sorted(W.rglob("*")) if p.is_file() and p.suffix != ".zip" and "logs" not in p.parts and not p.name.startswith("msg_") and "__pycache__" not in p.parts]
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
