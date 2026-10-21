"""M08b supplement 01 review ZIP: delivery folder of the branch head + the supplement-01 data tables / registry fragments + code diffs against the
M08b first-round head 58b8efdc (supplement only) and the M08a head 820c2cae (whole M08b); manifest member, bytes, sha256, crc32 (as the first round).
The first-round M08B_REVIEW.zip is left unchanged."""
import csv
import hashlib
import subprocess
import zipfile
import zlib
from pathlib import Path

WT = Path("/home/jin/wt_m08b_20261021")
OUT = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m08b_20261021")
D = WT / "research/06_scope_redesign/p1_m08b_20261021"
FIRST, BASE = "58b8efdc", "820c2cae"
head = subprocess.check_output(["git", "-C", str(WT), "rev-parse", "--short", "HEAD"], text=True).strip()
diff = lambda base: subprocess.check_output(["git", "-C", str(WT), "diff", base, "HEAD", "--", "scripts_project", "tests", "configs"])
members = []
for p in sorted(D.rglob("*")):
    if p.is_file() and "__pycache__" not in p.parts:
        members.append((str(p.relative_to(D)), p.read_bytes()))
dem = WT / "research_inputs/demand_v5"
extra = {f"data/{n}": dem / n for n in ["DEMAND_ANCHOR_AEO8_ATS.csv", "DEMAND_ANCHOR_M08B_EVIDENCE.json", "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv",
                                         "INDUSTRY_OUTPUT_2050_M08B.csv", "INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.csv", "INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.json",
                                         "INDUSTRY_HEAT_BAND_TECHNOLOGY_MAP.csv", "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"]}
extra.update({f"registry/{n}": WT / "research_inputs/registry_v5/fragments" / n for n in ["m08b.csv", "m08b_corrections.csv"]})
for name, p in extra.items():
    members.append((name, p.read_bytes()))
members.append(("M08B_S01_CODE_DIFF_vs_first_round.patch", diff(FIRST)))
members.append(("M08B_CODE_DIFF_vs_M08a.patch", diff(BASE)))
zp = OUT / "M08B_S01_REVIEW.zip"
rows = []
with zipfile.ZipFile(zp, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for name, data in members:
        zi = zipfile.ZipInfo(name, date_time=(2026, 10, 21, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(zi, data)
        rows.append(dict(member=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), crc32=f"{zlib.crc32(data) & 0xffffffff:08x}"))
with zipfile.ZipFile(zp) as z:   # verify: every member reads back with the listed CRC
    bad = [r["member"] for r in rows if f"{z.getinfo(r['member']).CRC:08x}" != r["crc32"]]
    assert not bad and z.testzip() is None, bad
with open(OUT / "M08B_S01_REVIEW_MANIFEST.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["member", "bytes", "sha256", "crc32"]); w.writeheader(); w.writerows(rows)
zs = hashlib.sha256(zp.read_bytes()).hexdigest()
(OUT / "M08B_S01_REVIEW_ZIP_SHA256.txt").write_text(f"{zs}  M08B_S01_REVIEW.zip\n# branch codex/m08b-demand-20261021 head {head}; {len(rows)} members; manifest M08B_S01_REVIEW_MANIFEST.csv\n")
print(head, len(rows), zp.stat().st_size, zs)
