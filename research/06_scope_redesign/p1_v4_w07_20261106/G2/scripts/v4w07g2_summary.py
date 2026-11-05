"""G2: merge the evidence fragments (evidence/_*.json) into EVIDENCE.json with counts by status and grade (standard library only).

    python scripts/v4w07g2_summary.py
"""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parent.parent
INSTR_SHA = "20d03b692f1d32733f34b04d85c01fb3df1345f95f366a6bf25de36ac7ec7baf"


def main():
    nums, frags = [], {}
    for p in sorted((W / "evidence").glob("_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if "numbers" not in d:
            continue
        frags[p.name] = dict(section=d.get("section"), n=len(d["numbers"]), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        nums.extend(d["numbers"])
    keys = [n["key"] for n in nums]
    dup = sorted(k for k, c in collections.Counter(keys).items() if c > 1)
    if dup:
        raise SystemExit(f"duplicated keys: {dup[:10]}")
    out = dict(session="W07 G2 (Viet Nam)", instruction_sha256=INSTR_SHA, count=len(nums),
               count_by_status=dict(collections.Counter(n["status"] for n in nums)), count_by_grade=dict(collections.Counter(str(n["grade"]) for n in nums)),
               fragments=frags, numbers=nums)
    (W / "EVIDENCE.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(out["count"], out["count_by_status"])


if __name__ == "__main__":
    main()
