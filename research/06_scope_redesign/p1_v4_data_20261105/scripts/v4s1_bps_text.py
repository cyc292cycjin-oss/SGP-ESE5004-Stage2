"""V4 S1 section 4.1 (step 1): text of the BPS IBS 2019 publication with positions and fonts.

    %USERPROFILE%/miniconda3/python.exe -I scripts/v4s1_bps_text.py --work <work dir>

Every page of BPS0000-statistik_industri_manufaktur_indonesia_2019.pdf draws one Form XObject (/TPLn) that holds the printed page
(vector text with ToUnicode maps; a few pages are scanned images); the page itself only adds the watermark URL, which is why
pypdf's page.extract_text() returns nothing else. This script reads the form of each page:
  * extracted/12_bps_indonesia/bps_text/pNNN.txt   - pypdf extract_xform_text (reading order)
  * extracted/12_bps_indonesia/bps_text/pNNN.csv   - one row per text run: x, y (form user space after cm x Tm), font BaseFont,
                                                   font size, text (for the table parser v4s1_bps_parse.py)
  * extracted/12_bps_indonesia/bps_text/PAGES.csv  - page, form name, BBox, number of runs, fonts, image XObjects in the form
Runs with the Windows miniconda interpreter (pypdf; the WSL environment has none). Output stays out of git (third-party content);
the parsed tables and the check table go to s1/.
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from pypdf import PdfReader

PDF = "downloads/12_bps_indonesia/BPS0000-statistik_industri_manufaktur_indonesia_2019.pdf"


def mult(a, b):
    """3x3 affine product of PDF matrices [a b c d e f]."""
    return [a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3], a[2] * b[0] + a[3] * b[2], a[2] * b[1] + a[3] * b[3],
            a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5]]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True)
    a = ap.parse_args()
    r = PdfReader(str(a.work / PDF))
    out = a.work / "extracted/12_bps_indonesia/bps_text"; out.mkdir(parents=True, exist_ok=True)
    pages = []
    for i, page in enumerate(r.pages, start=1):
        data = page.get_contents().get_data()
        used = [u.decode() for u in re.findall(rb"/(TPL\d+) Do", data)]
        runs, txt, fonts, n_img, bbox = [], [], set(), 0, None
        for u in used:
            form = page["/Resources"]["/XObject"]["/" + u].get_object()
            bbox = [float(x) for x in form.get("/BBox", [])]
            res = form.get("/Resources", {})
            xo = res.get("/XObject", {}) if res else {}
            n_img += sum(1 for v in xo.values() if v.get_object().get("/Subtype") == "/Image")

            def vis(text, cm, tm, font, size, _runs=runs, _fonts=fonts):
                if not text or not text.strip():
                    return
                m = mult(tm, cm)
                fn = str(font.get("/BaseFont", "")) if font else ""
                _fonts.add(fn)
                eff = size * (m[3] if m[3] else 1.0)
                _runs.append(dict(x=round(m[4], 2), y=round(m[5], 2), font=fn, size=round(eff, 2), text=text.replace("\n", " ")))
            try:
                txt.append(page.extract_xform_text(form, visitor_text=vis))
            except Exception as e:   # noqa: BLE001 - record and continue
                txt.append(f"[extract_xform_text failed: {e!r}]")
        (out / f"p{i:03d}.txt").write_text("\n".join(txt), encoding="utf-8")
        with (out / f"p{i:03d}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["x", "y", "font", "size", "text"]); w.writeheader(); w.writerows(runs)
        pages.append(dict(page=i, forms=";".join(used), bbox=" ".join(f"{v:g}" for v in (bbox or [])), runs=len(runs), images=n_img,
                          fonts=";".join(sorted(fonts)), first_text=(txt[0][:80].replace("\n", " | ") if txt else "")))
    with (out / "PAGES.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pages[0].keys())); w.writeheader(); w.writerows(pages)
    print(len(pages), "pages;", sum(p["runs"] for p in pages), "runs;", sum(1 for p in pages if p["images"]), "pages with images")


if __name__ == "__main__":
    main()
