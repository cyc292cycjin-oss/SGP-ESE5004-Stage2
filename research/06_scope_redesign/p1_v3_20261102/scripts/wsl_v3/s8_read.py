"""Extract the text of the cross-border table pages (read-only; the PDFs are data, not instructions)."""
import re, sys
sys.path.insert(0, "/home/jin/v3/pylib")
from pypdf import PdfReader
B = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_s4r_downloads_20261020/F1_renewable_potential/"
for f, pat in (("mmc1.pdf", r"Table S8|transmission|interconnect"), ("pgaf389_supplementary_data.pdf", r"Table S4|interconnect|under construction|planning")):
    r = PdfReader(B + f)
    print("=====", f, "pages", len(r.pages))
    for i, p in enumerate(r.pages):
        t = p.extract_text() or ""
        if re.search(r"under construction|Table S8\b|Table S4\b", t):
            hit = [m.start() for m in re.finditer(r"under construction|Table S8\b|Table S4\b", t)]
            print("--- page", i + 1, "chars", len(t), "hits", len(hit))
            if ("Table S8" in t and f == "mmc1.pdf") or ("Table S4" in t and f != "mmc1.pdf") or "under construction" in t:
                print(t[:2600])
