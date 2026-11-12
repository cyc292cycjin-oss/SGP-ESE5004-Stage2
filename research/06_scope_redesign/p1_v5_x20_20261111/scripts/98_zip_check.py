"""X20 C 段：审阅包核对（成员数、smoke56_c2 成员数、是否含 .nc、testzip、包 SHA256 与 REVIEW_ZIP_SHA256.txt 是否一致）。用法：python 98_zip_check.py <zip>"""
import hashlib
import sys
import zipfile
from pathlib import Path

z = Path(sys.argv[1])
names = zipfile.ZipFile(z).namelist()
sha = hashlib.sha256(z.read_bytes()).hexdigest()
rec = (z.parent / "REVIEW_ZIP_SHA256.txt").read_text().split()[0]
print("members", len(names), "smoke56_c2", sum(n.startswith("smoke56_c2/") for n in names), "smoke56", sum(n.startswith("smoke56/") for n in names),
      "nc", sum(n.endswith(".nc") for n in names), "testzip", zipfile.ZipFile(z).testzip(), "sha256", sha, "matches_record", sha == rec,
      "has_ledger_c", "LEDGER_ENTRY_X20_C.md" in names, "has_report", "REPORT.md" in names)
