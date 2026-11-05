"""V4 S1: page-by-page text of the PDFs used in S1 (BPS IBS 2019, CREA/GEM captive coal 2025, IEA WORLDBAL documentation July 2026,
HEESI 2025, USGS MYB 2023 Indonesia), written to extracted/<subdir>/<pdf stem>/pNNN.txt (layout mode) and pNNN_plain.txt (plain mode).

    %USERPROFILE%/miniconda3/python.exe -I scripts/v4s1_pdf_text.py --work <work dir>

Runs with the Windows miniconda interpreter because only it has pypdf (the WSL pypsa-earth environment has none); everything else of S1
runs in WSL. The text dumps stay in extracted/ (not in git: the PDFs and their text are third-party publications; the IEA document is
cited by page number only). Writes extracted/PDF_TEXT_INDEX.csv (file, pages, SHA256 of the PDF, characters per page).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

from pypdf import PdfReader

PDFS = {
    "12_bps_indonesia": "downloads/12_bps_indonesia/BPS0000-statistik_industri_manufaktur_indonesia_2019.pdf",
    "13_crea_captive_coal": "downloads/13_crea_captive_coal/EN-CREA_GEM_Indonesia-captive-coal-in-2025_REV.pdf",
    "14_iea_worldbal": "downloads/14_iea_worldbal/WORLDBAL_Documentation_July2026.pdf",
    "heesi_2025": "../p2_data_intake/v3_20261102/01_industry/content-handbook-of-energy-and-economic-statistics-of-indonesia-2025.pdf",
    "usgs_myb3_2023_id": "../p2_data_intake/v3_20261102/01_industry/myb3-2023-indonesia.pdf",
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); ap.add_argument("--only", default="")
    a = ap.parse_args()
    rows = []
    for key, rel in PDFS.items():
        if a.only and key not in a.only.split(","):
            continue
        p = (a.work / rel).resolve()
        out = a.work / "extracted" / key / p.stem
        out.mkdir(parents=True, exist_ok=True)
        r = PdfReader(str(p))
        for i, page in enumerate(r.pages, start=1):
            try:
                lay = page.extract_text(extraction_mode="layout")
            except Exception as e:   # noqa: BLE001 - record and fall back to plain mode
                lay = f"[layout extraction failed: {e!r}]"
            plain = page.extract_text() or ""
            (out / f"p{i:03d}.txt").write_text(lay, encoding="utf-8")
            (out / f"p{i:03d}_plain.txt").write_text(plain, encoding="utf-8")
            rows.append(dict(key=key, pdf=rel, page=i, chars_layout=len(lay), chars_plain=len(plain)))
        print(key, len(r.pages), "pages", sha256(p)[:16])
        rows.append(dict(key=key, pdf=rel, page=0, chars_layout=len(r.pages), chars_plain=sha256(p)))
    idx = a.work / "extracted" / "PDF_TEXT_INDEX.csv"
    old = []
    if a.only and idx.exists():
        old = [x for x in csv.DictReader(idx.open(encoding="utf-8")) if x["key"] not in a.only.split(",")]
    with idx.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["key", "pdf", "page", "chars_layout", "chars_plain"]); w.writeheader(); w.writerows(old + rows)


if __name__ == "__main__":
    main()
