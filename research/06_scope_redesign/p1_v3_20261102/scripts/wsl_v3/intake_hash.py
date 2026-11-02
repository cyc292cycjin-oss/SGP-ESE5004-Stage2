"""V3 1.2: SHA256 / size of every uploaded file, member lists of the zip files (no extraction next to the originals)."""
import csv, hashlib, zipfile, gzip, json
from pathlib import Path
SRC = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102")
OUT = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/phase1"); OUT.mkdir(parents=True, exist_ok=True)
rows = []
for p in sorted(SRC.rglob("*")):
    if p.is_file():
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        rows.append(dict(path=str(p.relative_to(SRC)).replace("\\", "/"), bytes=p.stat().st_size, sha256=h.hexdigest()))
with open(OUT / "INTAKE_FILES_SHA256.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, ["path", "bytes", "sha256"]); w.writeheader(); w.writerows(rows)
print(len(rows), sum(r["bytes"] for r in rows))
for r in rows:
    print(r["sha256"][:12], r["bytes"], r["path"])
for z in sorted(SRC.rglob("*.zip")):
    with zipfile.ZipFile(z) as x:
        names = x.infolist()
        print("==", z.name, len(names))
        for i in names[:60]:
            print("   ", i.file_size, i.filename)
for g in sorted(SRC.rglob("*.gz")):
    with gzip.open(g, "rt", encoding="utf-8", errors="replace") as f:
        print("==", g.name)
        for k in range(4):
            print("   ", f.readline()[:300].rstrip())
