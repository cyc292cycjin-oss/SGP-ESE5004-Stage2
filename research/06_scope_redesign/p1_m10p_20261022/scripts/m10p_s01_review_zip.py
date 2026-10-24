"""M10P supplement 01: review ZIP of the work folder (without the deployment packages and earlier review ZIPs) + the repository files changed by
supplement 01 (code/), with a per-member SHA256 / CRC32 manifest (same layout as M10P_REVIEW.zip).

    python m10p_s01_review_zip.py --work <work/p1_m10p_20261022> --repo /home/jin/wt_m10p_20261022 --head <sha>
"""
import argparse
import csv
import hashlib
import zipfile
import zlib
from pathlib import Path

CODE = ("scripts_project/m10_batch3_summary.py", "tests/research/test_m10p_batch3.py", "tests/research/fixtures/m10p_fake_pipeline.py")
PKG = "research/06_scope_redesign/p1_m10p_20261022/cloud_package"
SKIP = {"M10P_REVIEW.zip", "M10P_REVIEW_MANIFEST.csv", "M10P_REVIEW_ZIP_SHA256.txt", "M10P_S01_REVIEW.zip", "M10P_S01_REVIEW_MANIFEST.csv", "M10P_S01_REVIEW_ZIP_SHA256.txt"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--head", required=True)
    a = ap.parse_args()
    members = [(p, p.relative_to(a.work).as_posix()) for p in sorted(a.work.rglob("*"))
               if p.is_file() and p.name not in SKIP and "__pycache__" not in p.parts and not p.relative_to(a.work).parts[0].startswith("cloud_package_dist")]
    members += [(a.repo / c, "code/" + c) for c in CODE]
    members += [(p, "code/" + p.relative_to(a.repo).as_posix()) for p in sorted((a.repo / PKG).rglob("*")) if p.is_file()]
    rows = []
    zp = a.work / "M10P_S01_REVIEW.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in members:
            b = src.read_bytes()
            z.writestr(arc, b)
            rows.append(dict(member=arc, bytes=len(b), sha256=hashlib.sha256(b).hexdigest(), crc32=f"{zlib.crc32(b) & 0xFFFFFFFF:08x}"))
    with zipfile.ZipFile(zp) as z:   # read back: every member's CRC as recorded
        info = {i.filename: f"{i.CRC:08x}" for i in z.infolist()}
        assert all(info[r["member"]] == r["crc32"] for r in rows) and z.testzip() is None
    with open(a.work / "M10P_S01_REVIEW_MANIFEST.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["member", "bytes", "sha256", "crc32"]); w.writeheader(); w.writerows(rows)
    h = hashlib.sha256(zp.read_bytes()).hexdigest()
    (a.work / "M10P_S01_REVIEW_ZIP_SHA256.txt").write_text(f"{h}  M10P_S01_REVIEW.zip\n# branch codex/m10-batch3-20261022 built from {a.head}; {len(rows)} members; manifest M10P_S01_REVIEW_MANIFEST.csv\n")
    print(h, len(rows), zp.stat().st_size)


if __name__ == "__main__":
    main()
