"""V4 W07 G1: review package REVIEW_<report commit[:8]>.zip of the G1 folder (every file except earlier review packages and __pycache__),
with a member manifest (path, bytes, SHA256, CRC32) written next to it.

    python scripts/v4g1_review_zip.py <report commit, 8+ hex characters>
"""
import hashlib
import sys
import zipfile
import zlib
from pathlib import Path

G1 = Path(__file__).resolve().parents[1]


def main():
    cid = sys.argv[1][:8]
    if len(cid) != 8 or any(c not in "0123456789abcdef" for c in cid):
        sys.exit("commit id must be 8 hex characters")
    zp = G1 / f"REVIEW_{cid}.zip"; mp = G1 / f"REVIEW_ZIP_MANIFEST_{cid}.txt"
    files = [p for p in sorted(G1.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and not p.name.startswith("REVIEW_")]
    lines = [f"V4 W07 G1 review package {zp.name}: {len(files)} members (path, bytes, sha256, crc32)"]
    with zipfile.ZipFile(zp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files:
            b = p.read_bytes(); rel = p.relative_to(G1).as_posix()
            z.writestr(zipfile.ZipInfo(rel, date_time=(2026, 11, 6, 0, 0, 0)), b, compress_type=zipfile.ZIP_DEFLATED)
            lines.append(f"{rel}\t{len(b)}\t{hashlib.sha256(b).hexdigest()}\t{zlib.crc32(b) & 0xFFFFFFFF:08x}")
    with zipfile.ZipFile(zp) as z:
        bad = z.testzip()
        if bad:
            sys.exit(f"zip test failed at {bad}")
        if len(z.namelist()) != len(files):
            sys.exit("member count differs")
    zb = zp.read_bytes()
    lines.append(f"package\t{len(zb)}\t{hashlib.sha256(zb).hexdigest()}")
    mp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(zp.name, len(files), len(zb), hashlib.sha256(zb).hexdigest())


if __name__ == "__main__":
    main()
