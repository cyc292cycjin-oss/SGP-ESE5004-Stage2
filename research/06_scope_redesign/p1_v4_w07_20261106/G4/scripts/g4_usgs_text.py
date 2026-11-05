"""G4: USGS Minerals Yearbook 2017-18, Asia and the Pacific (regional overview, July 2023; local copy in work/p2_data_intake), table 3
'production of selected mineral commodities, 2018', rows of Brunei, Burma, Cambodia and Laos on PDF pages 6, 9 and 10 (column headers read
from the same pages and written below). Page text stays in G4/extracted/ (third-party publication, not committed); the parsed values with
page, column and flag go to evidence/USGS_AP_2018_T3_G4.csv.

    C:/Users/20122/miniconda3/python.exe -I scripts/g4_usgs_text.py      (Windows python with pypdf)
"""
import csv
import hashlib
import re
import sys
from pathlib import Path

import pypdf

G4 = Path(__file__).resolve().parents[1]
PDF = G4.parents[1] / "p2_data_intake/v3_20261102/01_industry/myb3-2017-18-asia-pacific.pdf"
# column headers as printed on the pages (thousand metric tons unless the header says otherwise)
COLS = {6: ["alumina", "bauxite", "aluminum_metal", "antimony_mine_Sb_t", "chromite_mine_gross", "cobalt_mine_Co", "cobalt_refined",
            "copper_mine_Cu", "copper_refined_primary"],
        9: ["rutile_TiO2_t", "tungsten_mine_W_t", "zinc_mine_Zn", "zinc_metal", "barite", "cement_hydraulic", "fluorspar_t", "graphite_t", "lithium_t"],
        10: ["magnesite", "nitrogen_N_content_of_ammonia", "phosphate_rock_P2O5", "potash_K2O", "salt", "anthracite", "bituminous", "lignite",
             "natural_gas_Mm3"]}
ROWS = {"Brunei": "BN", "Burma": "MM", "Cambodia": "KH", "Laos": "LA"}
TOK = re.compile(r"--|\d[\d,]*(?:\.\d+)?(?: e)?(?:, \d)?")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sha = hashlib.sha256(PDF.read_bytes()).hexdigest()
    r = pypdf.PdfReader(str(PDF))
    out = G4 / "extracted/usgs_ap_2017_18"; out.mkdir(parents=True, exist_ok=True)
    rows = []
    for pg, cols in COLS.items():
        t = r.pages[pg - 1].extract_text() or ""
        (out / f"p{pg:03d}.txt").write_text(t, encoding="utf-8")
        assert "2017–2018" in t or "2017-2018" in t or "ASIA AND THE PACIFIC" in t.upper(), pg
        for line in t.splitlines():
            m = re.match(r"^(Brunei|Burma|Cambodia|Laos) (.*)$", line.strip())
            if not m:
                continue
            toks = TOK.findall(m.group(2))
            if len(toks) != len(cols):
                raise ValueError(f"page {pg} {m.group(1)}: {len(toks)} tokens {toks}")
            for c, tk in zip(cols, toks):
                if tk == "--":
                    continue
                flag = "e" if " e" in tk else ""
                foot = tk.split(",")[-1].strip() if ", " in tk else ""
                v = float(tk.split(" ")[0].replace(",", ""))
                rows.append(dict(iso=ROWS[m.group(1)], country_label=m.group(1), pdf_page=pg, printed_page=f"1.{pg - 2}", column=c, year=2018, value=v,
                                 unit=("t" if c.endswith("_t") else ("million m3" if c.endswith("Mm3") else "thousand t")), usgs_flag=flag, footnote=foot,
                                 source=f"USGS MYB 2017-18 Asia and the Pacific, table 3 ({PDF.name}, sha256 {sha[:16]})"))
    with open(G4 / "evidence/USGS_AP_2018_T3_G4.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (out / "INDEX.csv").write_text(f"pdf,{PDF.name}\nsha256,{sha}\npages,{len(r.pages)}\nused_pages,6;9;10\n", encoding="utf-8")
    for x in rows:
        print(x["iso"], x["pdf_page"], x["column"], x["value"], x["usgs_flag"], x["footnote"])


if __name__ == "__main__":
    sys.exit(main())
