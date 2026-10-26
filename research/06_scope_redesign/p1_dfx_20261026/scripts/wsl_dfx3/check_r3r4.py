"""Check the third-batch R3 / R4 export: Owen allocation, ledgers, labels (read-only)."""
import json
from pathlib import Path
L = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10_20261022/cloud_results/20261023T174135Z_halted/light_unpacked/export")
s = json.load(open(L / "batch/BATCH3_SUMMARY.json"))
for rid in ("R1", "R2", "R3", "R4"):
    d = L / rid; o = d / "m12_owen" / "OWEN.json"; led = d / "COUNTRY_COST_LEDGER.csv"
    r = s["runs"][rid]
    print(rid, r["profile"], r["termination"], r["v6"], "obj", r["objective"], "| OWEN", o.exists(), "usable", (json.load(open(o)).get("usable_for_allocation") if o.exists() else None), "| ledger", led.exists(), "| owen_usable(summary)", r.get("owen_usable"))
print("B6 R2-R1", (s["runs"]["R2"]["objective"] - s["runs"]["R1"]["objective"]) / 1e9, "B6 R4-R3", (s["runs"]["R4"]["objective"] - s["runs"]["R3"]["objective"]) / 1e9)
print("level2 / profile choice:", json.dumps(s.get("profile_choice"))[:400])
