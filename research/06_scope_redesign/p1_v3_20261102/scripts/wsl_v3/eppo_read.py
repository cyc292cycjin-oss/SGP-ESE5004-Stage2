"""Read the EPPO snapshot with pypdf (read-only): page count, text, images."""
import sys
sys.path.insert(0, "/home/jin/v3/pylib")
import pypdf
f = "/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102/01_industry/EPPO_power_purchased_from_Lao_PDR.pdf"
r = pypdf.PdfReader(f); print("pages", len(r.pages), r.metadata)
for i, p in enumerate(r.pages):
    t = p.extract_text() or ""; print("--- page", i + 1, "chars", len(t), "images", len(p.images)); print(t[:3500])
