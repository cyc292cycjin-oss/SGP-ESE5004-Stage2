"""I2: build the review package REVIEW_<commit8>.zip of the delivery folder and its member manifest (SHA256 and CRC32 per member).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i2_review_zip.py <commit8>

Members: the top-level deliverables, EVIDENCE.json, tables/, evidence/ (json), figures/, scripts/. The zip is not committed; the manifest
evidence/REVIEW_ZIP_MANIFEST_<commit8>.txt is.
"""
from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

I2 = Path(__file__).resolve().parents[1]


def members():
    for p in sorted(I2.glob("*")):
        if p.is_file() and p.suffix != ".zip":
            yield p
    for sub in ("tables", "evidence", "figures", "scripts"):
        for p in sorted((I2 / sub).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc" and not p.name.startswith("REVIEW_ZIP_MANIFEST"):
                yield p


def main(tag: str):
    z = I2 / f"REVIEW_{tag}.zip"
    rows = []
    with zipfile.ZipFile(z, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in members():
            arc = f"I2/{p.relative_to(I2).as_posix()}"
            zf.write(p, arc)
            rows.append((arc, p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest()))
    with zipfile.ZipFile(z) as zf:
        bad = zf.testzip()
        crc = {i.filename: f"{i.CRC:08x}" for i in zf.infolist()}
    zsha = hashlib.sha256(z.read_bytes()).hexdigest()
    lines = [f"# REVIEW_{tag}.zip  bytes {z.stat().st_size}  sha256 {zsha}  members {len(rows)}  testzip {'OK' if bad is None else bad}",
             "# member  bytes  sha256  crc32"]
    lines += [f"{a}  {b}  {s}  {crc[a]}" for a, b, s in rows]
    m = I2 / "evidence" / f"REVIEW_ZIP_MANIFEST_{tag}.txt"
    m.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(z.name, z.stat().st_size, zsha, len(rows), "members; testzip", bad)


if __name__ == "__main__":
    main(sys.argv[1])
