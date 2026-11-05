"""V4 W07 G0: page text of Wei et al. 2020 (Energies 13(21) 5664) from downloads/17_nickel_literature/, for the nickel unit-energy check (B-G0 item 2).

    %USERPROFILE%/miniconda3/python.exe -I scripts/v4g0_wei_text.py

Windows miniconda interpreter (it has pypdf; the WSL pypsa-earth environment has none). Read-only on the PDF; the text is a third-party
publication and stays in G0/extracted/ (not committed); only the values used, with page numbers, go into the deliverables.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from pypdf import PdfReader

G0 = Path(__file__).resolve().parents[1]
PDF = G0.parents[1] / "p1_v4_data_20261105/downloads/17_nickel_literature/energies-13-05664 (1).pdf"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    b = PDF.read_bytes()
    out = G0 / "extracted/wei2020"; out.mkdir(parents=True, exist_ok=True)
    r = PdfReader(str(PDF))
    print("sha256", hashlib.sha256(b).hexdigest(), "bytes", len(b), "pages", len(r.pages))
    print("metadata", dict(r.metadata or {}))
    for i, pg in enumerate(r.pages, 1):
        (out / f"p{i:02d}.txt").write_text(pg.extract_text(extraction_mode="layout") or "", encoding="utf-8")
        (out / f"p{i:02d}_plain.txt").write_text(pg.extract_text() or "", encoding="utf-8")
    (out / "SOURCE.txt").write_text(f"{PDF.name}\t{len(b)}\t{hashlib.sha256(b).hexdigest()}\t{len(r.pages)} pages\n", encoding="utf-8")


if __name__ == "__main__":
    main()
