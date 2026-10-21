"""M12: review ZIP of the work folder + the four repository files (code/), with a per-member SHA256 / CRC32 manifest.

    python m12_review_zip.py --work <work/p1_m12_20261021> --repo /home/jin/wt_m12_20261021 --head <sha>
"""
import argparse
import csv
import hashlib
import zipfile
import zlib
from pathlib import Path

CODE = ("scripts_project/m12_allocation.py", "scripts_project/m12_rhs_audit.py", "scripts_project/m08a_run_batch.sh", "tests/research/test_m12_allocation.py")
SKIP = {"M12_REVIEW.zip", "M12_REVIEW_MANIFEST.csv", "M12_REVIEW_ZIP_SHA256.txt"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--head", required=True)
    a = ap.parse_args()
    members = [(p, p.relative_to(a.work).as_posix()) for p in sorted(a.work.rglob("*")) if p.is_file() and p.name not in SKIP]
    members += [(a.repo / c, "code/" + c) for c in CODE]
    rows = []
    zp = a.work / "M12_REVIEW.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in members:
            b = src.read_bytes()
            z.writestr(arc, b)
            rows.append(dict(member=arc, bytes=len(b), sha256=hashlib.sha256(b).hexdigest(), crc32=f"{zlib.crc32(b) & 0xFFFFFFFF:08x}"))
    with zipfile.ZipFile(zp) as z:   # read back: every member's CRC as recorded
        info = {i.filename: f"{i.CRC:08x}" for i in z.infolist()}
        assert all(info[r["member"]] == r["crc32"] for r in rows) and z.testzip() is None
    with open(a.work / "M12_REVIEW_MANIFEST.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["member", "bytes", "sha256", "crc32"]); w.writeheader(); w.writerows(rows)
    h = hashlib.sha256(zp.read_bytes()).hexdigest()
    (a.work / "M12_REVIEW_ZIP_SHA256.txt").write_text(f"{h}  M12_REVIEW.zip\n# branch codex/m12-allocation-20261021 head {a.head}; {len(rows)} members; manifest M12_REVIEW_MANIFEST.csv\n")
    print(h, len(rows), zp.stat().st_size)


if __name__ == "__main__":
    main()
