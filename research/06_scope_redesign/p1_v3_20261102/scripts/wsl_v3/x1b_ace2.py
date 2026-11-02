"""X1b: ACE 2024 profile no. 9 Thailand - Lao PDR and no. 10 Lao PDR - Vietnam, text after the contents block. Read-only."""
import re, sys
sys.path.insert(0, "/home/jin/v3/pylib")
import pypdf
f = "/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/raw8/ACE2024_APG_Interconnections_Project_Profiles.pdf"
r = pypdf.PdfReader(f)
for i in (22, 23, 24, 25, 26, 27, 28):
    t = r.pages[i - 1].extract_text() or ""
    k = t.rfind("Internal Indonesia"); k = t.find("\n", k) if k >= 0 else 0
    print(f"======== file page {i}, images {len(r.pages[i - 1].images)}"); print(re.sub(r"\n\s*\n+", "\n", t[k:])[:4200])
