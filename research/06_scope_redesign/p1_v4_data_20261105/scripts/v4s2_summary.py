"""V4 S2: V4_S2_EVIDENCE.json - every number the report V4_S2_ID_REPORT.md quotes, with source, status (EXACT / VERIFIED / INFERENCE / PROPOSED) and
data grade (A-E), read back from the section evidence fragments s2/_*.json (written by the section scripts) and the registry rows of section 7.
No number is typed in here. Also lists the S2 tables with their SHA256.

    python scripts/v4s2_summary.py --work <work dir>      (WSL pypsa-earth python or any Python 3 with pandas)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); a = ap.parse_args()
    s2 = a.work / "s2"
    order = ["_chain_evidence.json", "_steel_evidence.json", "_products_evidence.json", "_biomass_evidence.json", "_stepwise_evidence.json", "_captive_screen_evidence.json"]
    numbers, extra = [], {}
    for name in order:
        J = json.loads((s2 / name).read_text(encoding="utf-8"))
        numbers += J["numbers"]; extra[name] = sorted(J.get("extra", {}).keys())
    with open(a.work / "DATA_REGISTRY_V4_DOWNLOADS.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["relative_path"].startswith("downloads/15_faostat/"):
                numbers.append(dict(key=f"7.registry.{Path(r['relative_path']).name}.bytes", value=int(r["bytes"]), unit="bytes", source="DATA_REGISTRY_V4_DOWNLOADS.csv", status="EXACT", grade="-"))
                numbers.append(dict(key=f"7.registry.{Path(r['relative_path']).name}.sha256", value=r["sha256"], unit="-", source="DATA_REGISTRY_V4_DOWNLOADS.csv (= V4_S2_INSTRUCTION.md)", status="EXACT", grade="-"))
                numbers.append(dict(key=f"7.registry.{Path(r['relative_path']).name}.licence", value=r["licence"], unit="-", source="DATA_REGISTRY_V4_DOWNLOADS.csv", status="待核", grade="-"))
    keys = [n["key"] for n in numbers]
    dup = sorted({k for k in keys if keys.count(k) > 1})
    if dup:
        raise SystemExit(f"duplicated evidence keys: {dup[:10]}")
    tables = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(s2.iterdir()) if p.is_file() and not p.name.startswith("_")}
    by_status = {}
    for n in numbers:
        s = str(n["status"]).split(" ")[0]; by_status[s] = by_status.get(s, 0) + 1
    out = dict(instruction="V4_S2_INSTRUCTION.md v1 (SHA256 95dcd3d846c34bbb631c8d8fb3f90c70e3bc28fd7187dd8cd9b29432816e6b01)", branch="codex/v4-data-20261105",
               count=len(numbers), count_by_status=by_status, fragments=order, fragment_extra_keys=extra, tables_sha256=tables, numbers=numbers)
    (a.work / "V4_S2_EVIDENCE.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("numbers", len(numbers), by_status, "tables", len(tables))


if __name__ == "__main__":
    main()
