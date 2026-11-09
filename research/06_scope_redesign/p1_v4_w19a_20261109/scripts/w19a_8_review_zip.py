"""W19a: review ZIP from the delivery commit (git archive) and per-member SHA256 / CRC32 manifest."""
import csv, hashlib, subprocess, sys, zipfile
from pathlib import Path
c = sys.argv[1]
D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w19a_20261109")
z = D / f"REVIEW_{c[:8]}.zip"
subprocess.run(["git", "-C", "/home/jin/wt_v4_w19a", "archive", "--format=zip", "-o", str(z), c, "research/06_scope_redesign/p1_v4_w19a_20261109"], check=True)
rows = []
with zipfile.ZipFile(z) as f:
    for i in f.infolist():
        if i.is_dir():
            continue
        b = f.read(i.filename)
        rows.append(dict(member=i.filename, bytes=i.file_size, sha256=hashlib.sha256(b).hexdigest(), crc32=f"{i.CRC:08x}"))
with open(D / "evidence" / "REVIEW_MANIFEST.csv", "w", newline="", encoding="utf-8") as g:
    w = csv.DictWriter(g, fieldnames=["member", "bytes", "sha256", "crc32"]); w.writeheader(); w.writerows(rows)
zs = hashlib.sha256(z.read_bytes()).hexdigest()
(D / "evidence" / f"REVIEW_ZIP_SHA256_{c[:8]}.txt").write_text(f"{zs}  {z.name}\nsource commit {c}\nmembers {len(rows)}\n", encoding="utf-8")
print(z.name, zs, len(rows), z.stat().st_size)
