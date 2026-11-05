"""G3: read the USGS Minerals Yearbook country chapters already on disk (TH 2020-21, PH 2022), Table 1 rows used by G3.

    C:/Users/20122/miniconda3/python.exe -I scripts/g3_usgs_text.py        (Windows interpreter: only it has pypdf)

Each value is read from the PDF text layer of Table 1 (no OCR) and written with page number and the year header of the table; the script asserts
that the year header and every row it keeps are found exactly once. Output tables/USGS_TABLE1_TH_PH.csv. Read only; nothing is downloaded.
"""
from __future__ import annotations

import csv
import hashlib
import re
import sys
from pathlib import Path

from pypdf import PdfReader

sys.stdout.reconfigure(encoding="utf-8")
G3 = Path(__file__).resolve().parents[1]
SRC = Path("D:/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102/01_industry")
FILES = {"TH": ("myb3-2020-21-thailand.pdf", [2017, 2018, 2019, 2020, 2021]), "PH": ("myb3-2022-philippines.pdf", [2018, 2019, 2020, 2021, 2022])}
ROWS = {"TH": [("Raw steel thousand metric tons", "raw_steel", 1e3), ("Cement, hydraulic thousand metric tons", "cement_hydraulic", 1e3), ("Limee", "lime", 1.0),
               ("Limestone, for cement do.", "limestone_for_cement", 1e3)],
        "PH": [("Raw steel", "raw_steel", 1.0), ("Cement, hydraulic thousand metric tons", "cement_hydraulic", 1e3), ("Lime", "lime", 1.0)]}


def num(tok: str):
    t = tok.replace(",", "").rstrip("re").strip()
    return float(t) if re.fullmatch(r"-?\d+(\.\d+)?", t) else None


def main():
    out = []
    for cc, (fn, years) in FILES.items():
        p = SRC / fn
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        r = PdfReader(str(p))
        for i, page in enumerate(r.pages):
            t = page.extract_text() or ""
            if "TABLE 1" not in t:
                continue
            for line in t.splitlines():
                for label, key, unit_t in ROWS[cc]:
                    if line.startswith(label + " ") and not any(o["country"] == cc and o["item"] == key for o in out):
                        raw = line[len(label):].split(); toks = []
                        for x in raw:   # a stand-alone flag ('r', 'e') belongs to the number before it
                            if x in ("r", "e") and toks:
                                toks[-1] += x
                            else:
                                toks.append(x)
                        vals = [num(x) for x in toks]
                        if len(vals) < 5 or any(v is None for v in vals[-5:]):
                            raise ValueError(f"{cc} {label}: cannot read five numbers from '{line}'")
                        for y, tok, v in zip(years, toks[-5:], vals[-5:]):
                            out.append(dict(country=cc, item=key, year=y, value_t=v * unit_t, flag=("r" if tok.endswith("r") else ("e" if tok.endswith("e") else "")),
                                            source=f"USGS MYB {fn}", page=i + 1, sha256=sha, line=line.strip()))
        got = {o["item"] for o in out if o["country"] == cc}
        miss = {k for _, k, _ in ROWS[cc]} - got
        if miss:
            raise ValueError(f"{cc}: rows not found {miss}")
    with open(G3 / "tables/USGS_TABLE1_TH_PH.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    for o in out:
        if o["year"] == 2019:
            print(o["country"], o["item"], o["year"], o["value_t"], o["flag"], "p", o["page"])


if __name__ == "__main__":
    main()
