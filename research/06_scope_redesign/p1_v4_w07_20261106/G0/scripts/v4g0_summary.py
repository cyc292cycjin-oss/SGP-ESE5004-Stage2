"""V4 W07 G0: merge the evidence fragments (evidence/_*.json except the chain detail dump) into EVIDENCE.json, with counts by status and grade.

    python scripts/v4g0_summary.py          (WSL pypsa-earth python; reads the G0 work folder only)

Every number of REPORT.md is in EVIDENCE.json (key, value, unit, source, status, grade) or in one of the ID_*.csv tables.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4g0_common as cm   # noqa: E402

FRAG = ["_chain_evidence.json", "_nickel_evidence.json", "_tables_evidence.json", "_biomass_potential_evidence.json"]


def main():
    nums, extra = [], {}
    for f in FRAG:
        d = json.loads((cm.WORK / "evidence" / f).read_text(encoding="utf-8"))
        nums += d["numbers"]; extra[f] = sorted(d.get("extra", {}).keys())
    add = [dict(key="g0.instruction_sha256", value=cm.sha256(cm.INSTR), unit="sha256", source="V4_W07_INSTRUCTION.md vs V4_W07_SHA256.txt (20d03b69...7baf)", status="VERIFIED", grade="-"),
           dict(key="g0.branch_base", value="07e08f387bcb5894384c008debc97d9e9c30ae4b", unit="commit", source="codex/v4-data-20261105 head when G0 branched", status="VERIFIED", grade="-"),
           dict(key="g0.mode2_coupling", value="RAS over ASEAN10 x sectors (m08b_demand.py ras_split: rows = country TFEC anchors, columns = sector totals)", unit="-",
                source="scripts_project/m08b_demand.py lines 132, 240-246; G0 reading-II runs change ID only, W11 changed 10 countries at once (ID (b) -10.99 here vs -10.16 in W11)",
                status="VERIFIED (code) / EXACT (runs)", grade="-"),
           dict(key="g0.s2_table_unit_note", value="s2/ID_BIOMASS_UNSD_2019.csv column 'twh' holds PWh (value / 1000); the S2 report text uses TWh correctly", unit="-",
                source="fuelwood n.e.s. industry 65,253 thousand m3 x 0.00254 TWh = 165.74 TWh vs 0.165743 in the column", status="VERIFIED", grade="-")]
    nums = add + nums
    keys = [n["key"] for n in nums]
    dup = [k for k, c in Counter(keys).items() if c > 1]
    if dup:
        raise SystemExit(f"duplicated keys {dup[:5]}")
    st = Counter(str(n["status"]).split(" (")[0] for n in nums); gr = Counter(str(n["grade"]) for n in nums)
    out = dict(session="V4 W07 G0 (Indonesia final)", instruction="work/p1_v4_w07_20261106/V4_W07_INSTRUCTION.md v1 section B-G0",
               status_legend="EXACT chain run or exact recomputation; VERIFIED read from a table / array / text; INFERENCE mechanism or estimate; PROPOSED quantified option, not implemented",
               grade_legend="A actual statistics; B official capacity / national statistics; C derived / proxy; D model estimate; E missing; '-' not a data value",
               counts=dict(numbers=len(nums), by_status=dict(st), by_grade=dict(gr)), fragments=extra, numbers=nums)
    cm.jdump(out, cm.WORK / "EVIDENCE.json")
    print(len(nums), dict(st))


if __name__ == "__main__":
    main()
