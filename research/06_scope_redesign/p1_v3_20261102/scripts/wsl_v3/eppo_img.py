"""Extract the images of the EPPO snapshot to a scratch folder (read-only on the source)."""
import sys
sys.path.insert(0, "/home/jin/v3/pylib")
from pathlib import Path
import pypdf
from PIL import Image
f = "/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102/01_industry/EPPO_power_purchased_from_Lao_PDR.pdf"
out = Path("/mnt/c/Users/20122/AppData/Local/Temp/claude/D--ResearchWorkspaces/3b84a8d8-c3d9-4930-9986-da94fd4c6e0e/scratchpad/eppo"); out.mkdir(parents=True, exist_ok=True)
r = pypdf.PdfReader(f)
for i, p in enumerate(r.pages):
    for j, im in enumerate(p.images):
        n = out / f"p{i+1}_{j}_{im.name}"; n.write_bytes(im.data)
        try:
            I = Image.open(n); print(n.name, I.size, I.mode, len(im.data))
        except Exception as e:
            print(n.name, "ERR", e, len(im.data))
