"""V3 D160-2 + fleet: read candidate sources (read only)."""
import sys, re, zipfile, io
sys.path.insert(0, "/home/jin/v3/pylib")
import pandas as pd, pypdf
from pathlib import Path
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 120); pd.set_option("display.max_colwidth", 60)
W = Path("/home/jin/wt_v3_20261102"); S = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_s4r_downloads_20261020/F1_renewable_potential")
OUT = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/phase1")
t = pd.read_csv("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data/temp_hard_coded/transport_data.csv")
print(t.shape, t.columns.tolist()); key = t.columns[0]
print(t[t[key].astype(str).isin(["BN", "ID", "KH", "LA", "MY", "MM", "PH", "SG", "TH", "TL", "VN", "DE", "FR"])].to_string())
for f in ("APG_STOCK_CHECK_S4E1.csv", "CORRIDOR_APG_CROSSCHECK_2024.csv"):
    x = pd.read_csv(W / "research_inputs/corridors" / f); print(f, x.shape, x.columns.tolist()); print(x.head(30).to_string()[:3600])
with zipfile.ZipFile(S / "ESI_APG_Model_v2.3.zip") as z:
    print([(i.filename, i.file_size) for i in z.infolist()][:40])
for name in ("main.pdf", "mmc1.pdf", "pgaf389.pdf", "pgaf389_supplementary_data.pdf"):
    r = pypdf.PdfReader(str(S / name)); txt = ""
    for i, p in enumerate(r.pages, 1):
        txt += f"\n=====PAGE {i}=====\n" + (p.extract_text() or "")
    (OUT / (name + ".txt")).write_text(txt)
    print("==", name, len(r.pages), len(txt))
    hits = 0
    for m in re.finditer(r"(existing|current|in operation|operational)[^.\n]{0,70}(interconnect|transmission|cross-border|capacity)|interconnect[^.\n]{0,70}(existing|current)|Table S?\d+[^\n]{0,90}(interconnect|transmission|cross-border|APG)", txt, flags=re.I):
        pg = txt.count("=====PAGE", 0, m.start()); print(f" p{pg}:", txt[max(0, m.start() - 70):m.end() + 90].replace("\n", " ")[:230]); hits += 1
        if hits >= 10: break
