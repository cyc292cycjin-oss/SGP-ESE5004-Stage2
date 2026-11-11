"""X20 ②1：NGCP TDP 2025-2050 中 PH 岛间直流的原文核对（只读 PDF）。按关键词找页，打印命中行（短）。"""
import re
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("pypdf missing")
P = Path(r"D:\ResearchWorkspaces\ASEAN\work\p1_v5_x20_20261111\downloads\ngcp\NGCP_TDP_2025_2050_REPORT.pdf")
r = PdfReader(str(P))
print("pages", len(r.pages))
pats = [r"Leyte[\s-]*Luzon", r"Mindanao[\s-]*Visayas|MVIP", r"Mindoro", r"440\s*MW", r"450\s*MW", r"HVDC", r"Batangas[\s-]*Mindoro"]
hits = {}
for i, pg in enumerate(r.pages):
    t = pg.extract_text() or ""
    for pat in pats:
        for m in re.finditer(pat, t, flags=re.I):
            s = max(0, m.start() - 90); e = min(len(t), m.end() + 90)
            hits.setdefault(i + 1, []).append((pat, " ".join(t[s:e].split())))
for pno in sorted(hits):
    kinds = sorted({h[0] for h in hits[pno]})
    if any(k in kinds for k in (r"440\s*MW", r"450\s*MW", r"HVDC")) and any(k.startswith(("Leyte", "Mindanao", "Mindoro", "Batangas")) for k in kinds):
        print(f"\n== PDF page {pno}: {kinds}")
        seen = set()
        for pat, snip in hits[pno]:
            if snip in seen:
                continue
            seen.add(snip)
            print("  -", snip[:230])
