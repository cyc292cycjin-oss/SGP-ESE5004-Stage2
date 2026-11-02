"""X1b: ACE 2024 APG project profiles: the pages about Thailand - Lao PDR and Lao PDR - Vietnam. Read-only."""
import re, sys
sys.path.insert(0, "/home/jin/v3/pylib")
import pypdf
f = "/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/raw8/ACE2024_APG_Interconnections_Project_Profiles.pdf"
r = pypdf.PdfReader(f); print("pages", len(r.pages))
T = [(p.extract_text() or "") for p in r.pages]
print("TABLE PAGE 2"); print(T[1][:2400])
for i, t in enumerate(T):
    if re.search(r"Lao", t):
        h = [m.start() for m in re.finditer(r"Lao", t)]
        print("--- page", i + 1, "chars", len(t), "images", len(r.pages[i].images), "Lao hits", len(h), "first:", t[:90].replace("\n", " | "))
