"""X1b: ACE 2024 profile no. 10 Lao PDR - Vietnam, overview part. Read-only."""
import re, sys
sys.path.insert(0, "/home/jin/v3/pylib")
import pypdf
f = "/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/raw8/ACE2024_APG_Interconnections_Project_Profiles.pdf"
r = pypdf.PdfReader(f)
for i in (27, 28):
    t = r.pages[i - 1].extract_text() or ""; k = t.find("APG Interconnection Project Profile |")
    print(f"======== file page {i}"); print(re.sub(r"\n\s*\n+", "\n", t[k:])[:2600])
