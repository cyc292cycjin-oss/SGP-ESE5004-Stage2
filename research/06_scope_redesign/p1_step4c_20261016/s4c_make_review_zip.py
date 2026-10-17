"""Build S4C_REVIEW.zip and S4C_REVIEW_ZIP_MANIFEST.csv (member, bytes, sha256, crc32) from the S4C work folder (run with any Python 3).
Members: report, evidence JSON, progress, download list, stop reports, cloud estimate and deploy steps, cloud_package scripts, the collector and
this script, evidence/ (tables, receipts, licence-scrubbed logs, source table extracts). Excluded: third-party source PDFs / HTML (sources_s4c/,
SHA256 logged in the progress file and evidence/s4c_4/DOWNLOAD_LOG_S4C4.tsv), cloud_package_dist/ (networks, code archive), drafts.
"""
import csv, hashlib, sys, zipfile, zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOP = ["S4C_REPORT.md", "S4C_EVIDENCE.json", "S4C_PROGRESS.md", "DOWNLOAD_LIST.csv", "CLOUD_RESOURCE_ESTIMATE.md", "CLOUD_DEPLOY_STEPS.md",
       "S4C_STOP_01_SUBSEA_SHARE.md", "S4C_STOP_02_HYDRO_DIAGNOSIS.md", "S4C_CLAUDE_CODE_INSTRUCTION.md", "S4C_INSTRUCTION_SHA256.txt",
       "S4C_SUPPLEMENT_01.md", "S4C_SUPPLEMENT_01_SHA256.txt", "s4c_collect_evidence.py", "s4c_make_review_zip.py"]


def main():
    members = [p for p in (HERE / t for t in TOP) if p.exists()]
    members += sorted(p for p in (HERE / "cloud_package").rglob("*") if p.is_file())
    members += sorted(p for p in (HERE / "evidence").rglob("*") if p.is_file())
    missing = [t for t in TOP[:6] if not (HERE / t).exists()]
    if missing:
        sys.exit("missing deliverables: " + ", ".join(missing))
    rows = []
    with zipfile.ZipFile(HERE / "S4C_REVIEW.zip", "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in members:
            data = p.read_bytes(); arc = str(p.relative_to(HERE)).replace("\\", "/")
            z.writestr(arc, data)
            rows.append(dict(member=arc, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), crc32=format(zlib.crc32(data) & 0xFFFFFFFF, "08x")))
    with open(HERE / "S4C_REVIEW_ZIP_MANIFEST.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["member", "bytes", "sha256", "crc32"]); w.writeheader(); w.writerows(rows)
    with zipfile.ZipFile(HERE / "S4C_REVIEW.zip") as z:
        bad = z.testzip()
        assert bad is None, bad
        for r in rows:
            info = z.getinfo(r["member"])
            assert format(info.CRC, "08x") == r["crc32"] and info.file_size == r["bytes"], r["member"]
    print(len(rows), "members;", (HERE / "S4C_REVIEW.zip").stat().st_size, "bytes; zip sha256", hashlib.sha256((HERE / "S4C_REVIEW.zip").read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
