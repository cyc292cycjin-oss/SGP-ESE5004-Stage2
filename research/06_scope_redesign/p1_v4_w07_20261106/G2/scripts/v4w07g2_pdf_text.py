"""G2: page text of the local PDFs used for Viet Nam (read only), written to extracted/<stem>/p<NNN>.txt plus extracted/PDF_TEXT_INDEX.csv.

    <Windows miniconda python with pypdf> -I scripts\\v4w07g2_pdf_text.py

The page texts are third-party publications and stay out of git (only the index with path, pages and SHA256 is committed).
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from pypdf import PdfReader

HERE = Path(__file__).resolve().parent.parent
W = HERE.parent.parent
PDFS = {
    "usgs_myb_2022_vietnam": W / "p2_data_intake/v3_20261102/01_industry/myb3-2022-vietnam.pdf",
    "apec_ebt_2022_table": W / "p2_data_intake/v3_20261102/01_industry/EBT 2022 Table.pdf",
    "apec_energy_statistics_2022": W / "p2_data_intake/v3_20261102/01_industry/225_ewg_apec-energy-statistics-2022.pdf",
    "usgs_myb_2017_18_asia_pacific": W / "p2_data_intake/v3_20261102/01_industry/myb3-2017-18-asia-pacific.pdf",
    "iea_worldbal_documentation_2026": W / "p1_v4_data_20261105/downloads/14_iea_worldbal/WORLDBAL_Documentation_July2026.pdf",
}


def sha(p: Path) -> str:
    h = hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()


def main():
    out = HERE / "extracted"; out.mkdir(exist_ok=True)
    rows = []
    for stem, p in PDFS.items():
        r = PdfReader(str(p)); d = out / stem; d.mkdir(exist_ok=True)
        n_text = 0
        for i, pg in enumerate(r.pages, start=1):
            t = pg.extract_text() or ""
            n_text += bool(t.strip())
            (d / f"p{i:03d}.txt").write_text(t, encoding="utf-8")
        rows.append(dict(stem=stem, path=str(p.relative_to(W)).replace("\\", "/"), pages=len(r.pages), pages_with_text=n_text,
                         bytes=p.stat().st_size, sha256=sha(p)))
        print(stem, len(r.pages), n_text)
    with open(out / "PDF_TEXT_INDEX.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
