"""Fable W08 review: review package REVIEW_<commit8>.zip with a per-member SHA256 + CRC32 manifest (evidence/REVIEW_ZIP_MANIFEST_<commit8>.txt).
usage: make_review_zip.py <delivery dir> <commit sha>"""
import hashlib
import sys
import zipfile
import zlib
from pathlib import Path

D = Path(sys.argv[1]); C8 = sys.argv[2][:8]
members = [p for p in sorted(D.rglob("*")) if p.is_file() and p.suffix != ".zip" and "__pycache__" not in p.parts and not p.name.startswith("REVIEW_ZIP_MANIFEST")]
man = D / "evidence" / f"REVIEW_ZIP_MANIFEST_{C8}.txt"
lines = []
for p in members:
    b = p.read_bytes(); lines.append(f"{hashlib.sha256(b).hexdigest()}  {zlib.crc32(b):08x}  {len(b):>10d}  {p.relative_to(D).as_posix()}")
man.write_text("\n".join(lines) + "\n", encoding="utf-8")
z = D / f"REVIEW_{C8}.zip"
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
    for p in members + [man]:
        zf.write(p, p.relative_to(D).as_posix())
print(z, len(members) + 1, "members;", "zip sha256", hashlib.sha256(z.read_bytes()).hexdigest())
