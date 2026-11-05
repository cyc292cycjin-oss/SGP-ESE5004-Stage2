"""W12: build the review package REVIEW_<commit8>.zip of the delivery folder and its member manifest (SHA256 and CRC32 per member).

    python scripts/w12_review_zip.py <commit8>

Members: REPORT.md, EVIDENCE.json, PROGRESS.md, MISSING_DATA.csv, LEDGER_ENTRY_DRAFT.md, DATA_REGISTRY_W12_SDMX.csv, tables/, evidence/
(json and logs), scripts/ (without probes), sdmx/ (raw responses and receipts). The zip itself is not committed; the manifest
evidence/REVIEW_ZIP_MANIFEST_<commit8>.txt is.
"""
from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

W12 = Path(__file__).resolve().parents[1]


def members():
    for name in ("REPORT.md", "EVIDENCE.json", "PROGRESS.md", "MISSING_DATA.csv", "LEDGER_ENTRY_DRAFT.md", "DATA_REGISTRY_W12_SDMX.csv"):
        if (W12 / name).exists():
            yield W12 / name
    for sub in ("tables", "evidence", "scripts", "sdmx"):
        for p in sorted((W12 / sub).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and not p.name.startswith(("_probe", "_agg")) and not p.name.startswith("REVIEW_ZIP_MANIFEST"):
                yield p


def main(tag: str):
    z = W12 / f"REVIEW_{tag}.zip"
    rows = []
    with zipfile.ZipFile(z, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in members():
            arc = f"W12/{p.relative_to(W12).as_posix()}"
            zf.write(p, arc)
            rows.append((arc, p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest()))
    with zipfile.ZipFile(z) as zf:
        bad = zf.testzip()
        crc = {i.filename: f"{i.CRC:08x}" for i in zf.infolist()}
    zsha = hashlib.sha256(z.read_bytes()).hexdigest()
    lines = [f"# REVIEW_{tag}.zip  bytes {z.stat().st_size}  sha256 {zsha}  members {len(rows)}  testzip {'OK' if bad is None else bad}",
             "# member  bytes  sha256  crc32"]
    lines += [f"{a}  {b}  {s}  {crc[a]}" for a, b, s in rows]
    m = W12 / "evidence" / f"REVIEW_ZIP_MANIFEST_{tag}.txt"
    m.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(z.name, z.stat().st_size, zsha, len(rows), "members; testzip", bad)


if __name__ == "__main__":
    main(sys.argv[1])
