"""Build the G5 review zip REVIEW_<commit8>.zip from the G5 delivery folder and write a member manifest (SHA256, CRC32, bytes).

    python g5_review_zip.py --g5 <G5 dir> --commit <commit sha>

Skips earlier zips and __pycache__. Writes <G5>/REVIEW_<commit8>.zip and <G5>/evidence/REVIEW_ZIP_MANIFEST_<commit8>.txt.
"""
from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--g5", type=Path, required=True); ap.add_argument("--commit", required=True); a = ap.parse_args()
    c8 = a.commit[:8]
    zp = a.g5 / f"REVIEW_{c8}.zip"; man = a.g5 / "evidence" / f"REVIEW_ZIP_MANIFEST_{c8}.txt"
    files = sorted(p for p in a.g5.rglob("*") if p.is_file() and p.suffix != ".zip" and "__pycache__" not in p.parts and p != man)
    with zipfile.ZipFile(zp, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, f"G5/{p.relative_to(a.g5).as_posix()}")
    lines = [f"# REVIEW_{c8}.zip  members={len(files)}  source commit {a.commit}", "# sha256  crc32  bytes  member"]
    with zipfile.ZipFile(zp) as z:
        if z.testzip() is not None:
            raise SystemExit("zip test failed")
        for i in z.infolist():
            data = z.read(i.filename)
            lines.append(f"{hashlib.sha256(data).hexdigest()}  {i.CRC:08x}  {i.file_size}  {i.filename}")
    zs = hashlib.sha256(zp.read_bytes()).hexdigest()
    lines.append(f"# zip sha256 {zs}  bytes {zp.stat().st_size}")
    man.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:3] + lines[-1:]))


if __name__ == "__main__":
    main()
