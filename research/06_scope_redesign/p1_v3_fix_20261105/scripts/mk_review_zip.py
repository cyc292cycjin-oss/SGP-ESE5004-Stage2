"""V3.1 review ZIP: work/p1_v3_fix_20261105_REVIEW.zip with the work folder (without draft/) and the v3.1 plan / guide / definition / packaging scripts and the
package's small control files; a member list with SHA256 and CRC32 (REVIEW_MANIFEST.csv inside the zip and next to it). Never the networks or the code archive.
    python -I mk_review_zip.py"""
import csv
import hashlib
import io
import zipfile
import zlib
from pathlib import Path

W = Path(r"D:\ResearchWorkspaces\ASEAN\work")
FIX = W / "p1_v3_fix_20261105"; V3 = W / "p1_v3_20261102"; PKG = V3 / "hpc_package_v3_1"
OUT = W / "p1_v3_fix_20261105_REVIEW.zip"; MAN = W / "p1_v3_fix_20261105_REVIEW_MANIFEST.csv"
members = []
for p in sorted(FIX.rglob("*")):
    if p.is_file() and "draft" not in p.relative_to(FIX).parts and "__pycache__" not in p.parts:
        members.append((p, "p1_v3_fix_20261105/" + p.relative_to(FIX).as_posix()))
for rel in ["RUN_PLAN_HPC_V3.md", "HPC_OPERATOR_GUIDE_V3.md", "V3_REPORT_FIX.md", "batch_def/BATCH_DEF_2920x3h_v31hpc.json", "hpc_v31/make_hpc_package_v31.sh", "hpc_v31/fullsize_presolve.sh"]:
    members.append((V3 / rel, "p1_v3_20261102/" + rel))
for rel in ["COMMIT", "SHA256SUMS", "HPC_PACKAGE_MANIFEST.json", "ZERO_SLACK_CHECK.json", "HPC_CONSISTENCY.txt", "HPC_CONSISTENCY.json", "BATCH_DEF.json", "pbs/HPC_PLAN.txt"]:
    members.append((PKG / rel, "hpc_package_v3_1/" + rel))
rows = []
if OUT.exists():
    raise SystemExit(f"{OUT} exists - never overwritten")
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for src, arc in members:
        b = src.read_bytes()
        z.writestr(arc, b)
        rows.append(dict(member=arc, bytes=len(b), sha256=hashlib.sha256(b).hexdigest(), crc32=f"{zlib.crc32(b) & 0xFFFFFFFF:08x}"))
    s = io.StringIO(); w = csv.DictWriter(s, fieldnames=["member", "bytes", "sha256", "crc32"]); w.writeheader(); w.writerows(rows)
    z.writestr("REVIEW_MANIFEST.csv", s.getvalue())
MAN.write_text(s.getvalue(), encoding="utf-8")
with zipfile.ZipFile(OUT) as z:
    bad = z.testzip()
    crc_ok = all(f"{z.getinfo(r['member']).CRC:08x}" == r["crc32"] for r in rows)
print(f"members {len(rows)} + manifest; zip {OUT.stat().st_size} bytes; testzip {'OK' if bad is None else bad}; crc match {crc_ok}; zip sha256 {hashlib.sha256(OUT.read_bytes()).hexdigest()}")
