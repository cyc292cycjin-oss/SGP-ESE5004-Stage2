"""G3: merge the section evidence files into EVIDENCE.json (A4) and check the A6 deliverables exist.

    python scripts/g3_summary.py          (WSL pypsa-earth python)

Every number carries key, value, unit, source, status (EXACT / VERIFIED / INFERENCE / PROPOSED) and data grade (A-E). Keys must be unique.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g3_common as cm   # noqa: E402

SECTIONS = ["_ncv_evidence.json", "_captive_evidence.json", "_products_evidence.json", "_biomass_evidence.json", "_chain_evidence.json"]
A6 = ["OTHER_SHARE_STEPS.csv", "SUBSECTORS_V4.csv", "CAPTIVE.csv", "BIOMASS_CHECK.csv", "NCV.csv", "NODE_SHARES.csv", "MISSING_DATA.csv", "DECISIONS.md"]


def main():
    nums, extra = [], {}
    for f in SECTIONS:
        d = json.loads((cm.G3 / "tables" / f).read_text(encoding="utf-8"))
        nums += d["numbers"]; extra[d["section"]] = {k: v for k, v in d.get("extra", {}).items() if k in ("reproduction", "plan", "timing_s", "schemes")}
    keys = Counter(n["key"] for n in nums)
    dup = [k for k, c in keys.items() if c > 1]
    if dup:
        raise SystemExit(f"duplicated keys: {dup[:5]}")
    bad = [n["key"] for n in nums if not n.get("status") or n.get("grade") in (None, "")]
    if bad:
        raise SystemExit(f"numbers without status / grade: {bad[:5]}")
    sdmx = {}
    for cc in cm.CC3:
        r = json.loads((cm.G3 / "sdmx" / f"{cc}_2015_2022.xml.receipt.json").read_text())
        sdmx[cc] = {k: r[k] for k in ("url", "utc", "http_status", "bytes", "sha256")}
    missing = [f"{cc}_{a}" for cc in cm.CC3 for a in A6 if not (cm.G3 / f"{cc}_{a}").exists()]
    st = Counter(n["status"].split(" ")[0] for n in nums)
    out = dict(session="G3 (v4 W07, B-G3: TH, PH, SG)", instruction_sha256="20d03b692f1d32733f34b04d85c01fb3df1345f95f366a6bf25de36ac7ec7baf",
               n_numbers=len(nums), by_status=dict(st), sdmx_downloads=sdmx, a6_missing=missing, extra=extra, numbers=nums)
    (cm.G3 / "EVIDENCE.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(len(nums), dict(st), "missing A6:", missing)


if __name__ == "__main__":
    main()
