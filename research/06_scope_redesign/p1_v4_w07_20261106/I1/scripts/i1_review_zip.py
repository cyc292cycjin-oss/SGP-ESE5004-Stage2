"""I1: build the review package REVIEW_<commit8>.zip of the delivery folder and its member manifest (SHA256 and CRC32 per member).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i1_review_zip.py <commit8>

Members: the top-level deliverables, EVIDENCE.json, BASE2019_SDMX/, tables/, evidence/ (json), scripts/. The zip is not committed; the
manifest evidence/REVIEW_ZIP_MANIFEST_<commit8>.txt is.
"""
from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

I1 = Path(__file__).resolve().parents[1]
TOP = ("REPORT.md", "RAS_MECHANISM.md", "EVIDENCE.json", "PROGRESS.md", "MISSING_DATA.csv", "LEDGER_ENTRY_DRAFT.md", "BASE2019_DIFF.csv",
       "EXPORT_TRUNCATION_SCAN.csv", "CORRECTION_CLASSIFICATION.csv", "HVC_VECTOR_CHECK.csv", "ID_GASOLINE_CHECK.csv")


def members():
    for name in TOP:
        if (I1 / name).exists():
            yield I1 / name
    for sub in ("BASE2019_SDMX", "tables", "evidence", "scripts"):
        for p in sorted((I1 / sub).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc" and not p.name.startswith("REVIEW_ZIP_MANIFEST"):
                yield p


def main(tag: str):
    z = I1 / f"REVIEW_{tag}.zip"
    rows = []
    with zipfile.ZipFile(z, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in members():
            arc = f"I1/{p.relative_to(I1).as_posix()}"
            zf.write(p, arc)
            rows.append((arc, p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest()))
    with zipfile.ZipFile(z) as zf:
        bad = zf.testzip()
        crc = {i.filename: f"{i.CRC:08x}" for i in zf.infolist()}
    zsha = hashlib.sha256(z.read_bytes()).hexdigest()
    lines = [f"# REVIEW_{tag}.zip  bytes {z.stat().st_size}  sha256 {zsha}  members {len(rows)}  testzip {'OK' if bad is None else bad}",
             "# member  bytes  sha256  crc32"]
    lines += [f"{a}  {b}  {s}  {crc[a]}" for a, b, s in rows]
    m = I1 / "evidence" / f"REVIEW_ZIP_MANIFEST_{tag}.txt"
    m.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(z.name, z.stat().st_size, zsha, len(rows), "members; testzip", bad)


if __name__ == "__main__":
    main(sys.argv[1])
