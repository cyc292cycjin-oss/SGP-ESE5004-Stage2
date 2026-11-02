import re, sys
sys.path.insert(0, "/home/jin/v3/pylib")
from pypdf import PdfReader
B = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_s4r_downloads_20261020/F1_renewable_potential/"
r = PdfReader(B + "mmc1.pdf")
t = r.pages[10].extract_text(); i = t.find("Table S8 below"); print(t[i:]); print("|PAGE12|"); t2 = r.pages[11].extract_text(); print(t2[:330]); print("...tail:", t2[-700:])
r = PdfReader(B + "pgaf389_supplementary_data.pdf"); print("===== SI pages", len(r.pages))
for i, p in enumerate(r.pages):
    t = p.extract_text() or ""
    for m in re.finditer(r"Table S4\b", t):
        print("--- p", i + 1, "at", m.start())
    if re.search(r"Lao PDR\s*[-–]|Thailand\s*[-–]\s*Lao|Thailand\s*[-–]\s*Myanmar", t):
        print("--- line table p", i + 1); print(t[:2300])
