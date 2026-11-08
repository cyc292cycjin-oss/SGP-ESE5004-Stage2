"""V4 W14 review package: REVIEW_<commit8>.zip of the delivery folder (zip files, commit-message files, __pycache__ and the package folders hpc_package_v4*/
excluded) plus the TEXT files of the delivered package under hpc_package_v4_text/ (everything but the two networks and the code archive, which are listed with
their SHA256 only), the repository diff stat and log 4e83d71e (D2c head = W14 start)..<commit> (research/ only; no code change); manifest with SHA256 and CRC32
per member.

    /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w14_review_zip.py <commit>
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

W = Path(__file__).resolve().parents[1]
R = Path("/home/jin/wt_v4_w14")
BASE = "4e83d71e"
PKG = W / "hpc_package_v4"


def main():
    commit = sys.argv[1]
    stat = subprocess.run(["git", "-C", str(R), "diff", "--stat", BASE, commit], capture_output=True, text=True, check=True).stdout
    outside = subprocess.run(["git", "-C", str(R), "diff", "--name-only", BASE, commit, "--", ".", ":!research/"], capture_output=True, text=True, check=True).stdout
    log = subprocess.run(["git", "-C", str(R), "log", "--format=%H %s", f"{BASE}..{commit}"], capture_output=True, text=True, check=True).stdout
    extra = {f"repo/DIFF_STAT_{BASE}.txt": stat.encode(), "repo/GIT_LOG.txt": log.encode(),
             f"repo/CHANGED_OUTSIDE_RESEARCH_{BASE}.txt": (outside or "(none: research/ only)\n").encode()}
    skip = lambda p: (p.suffix == ".zip" or p.name.startswith("msg_") or "__pycache__" in p.parts or any(x.startswith("hpc_package_v4") for x in p.relative_to(W).parts))   # noqa: E731
    members = [p for p in sorted(W.rglob("*")) if p.is_file() and not skip(p)]
    big = [p for p in sorted(PKG.rglob("*")) if p.is_file() and (p.suffix == ".nc" or p.name.startswith("code_"))]
    pkg_text = [p for p in sorted(PKG.rglob("*")) if p.is_file() and p not in big]
    listing = "".join(f"{p.relative_to(PKG).as_posix()}\t{p.stat().st_size}\t{hashlib.sha256(p.read_bytes()).hexdigest()}\n" for p in big)
    extra["hpc_package_v4_text/BINARY_FILES_NOT_IN_ZIP.tsv"] = ("path\tbytes\tsha256\n" + listing).encode()
    out = W / f"REVIEW_{commit[:8]}.zip"
    man = []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in members:
            b = p.read_bytes(); n = p.relative_to(W).as_posix()
            z.writestr(n, b); man.append((n, len(b), hashlib.sha256(b).hexdigest(), f"{zlib.crc32(b) & 0xffffffff:08x}"))
        for p in pkg_text:
            b = p.read_bytes(); n = "hpc_package_v4_text/" + p.relative_to(PKG).as_posix()
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
