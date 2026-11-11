"""X20 A 段：S1 存活表中"退役年 = 2050"（现行 < 规则下退出、改为 <= 后保留）的机组，以及地热 30 -> 40 年的影响（只读）。"""
import json
from collections import defaultdict
from pathlib import Path

P = Path(r"\\wsl.localhost\Ubuntu\home\jin\research\SGP_ESE5004_Stage2\phase2\research_model\results_project\s1\S1_SELECTED_ASSET_SURVIVAL_2050.json")
S = json.loads(P.read_text(encoding="utf-8"))
print("top keys:", list(S.keys())[:20])
recs = S["unit_evidence"]["records"]
print("records:", len(recs), "example keys:", sorted(recs[0].keys()))
status = defaultdict(float)
boundary = defaultdict(lambda: [0, 0.0])
geo = defaultdict(lambda: [0.0, 0.0, 0.0])  # surv30, surv40(<=), no year
for r in recs:
    cap = float(r.get("OriginalCapacity") or 0)
    status[r.get("SurvivalStatus")] += cap
    ry = r.get("RetirementYear")
    try:
        ry = float(ry)
    except (TypeError, ValueError):
        ry = None
    if ry is not None and abs(ry - 2050.0) < 1e-9:
        k = (r.get("Country"), r.get("Technology"), r.get("SurvivalStatus"))
        boundary[k][0] += 1
        boundary[k][1] += cap
    if r.get("Technology") == "Geothermal":
        cy = r.get("CommissioningYear")
        try:
            cy = float(cy)
        except (TypeError, ValueError):
            cy = None
        c = r.get("Country")
        if cy is None:
            geo[c][2] += cap
        else:
            if cy + 30 > 2050:
                geo[c][0] += cap
            if cy + 40 >= 2050:
                geo[c][1] += cap
print("\ncapacity by SurvivalStatus (MW):")
for k, v in sorted(status.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v:,.1f}")
print("\nunits with RetirementYear == 2050 (country, technology, status): count, MW")
tot = 0.0
for k, (cnt, mw) in sorted(boundary.items(), key=lambda x: -x[1][1]):
    print(f"  {k}: {cnt}, {mw:,.1f}")
    tot += mw
print(f"  total MW at the boundary: {tot:,.1f}")
print("\ngeothermal by country: survives 30 a (> 2050), survives 40 a (>= 2050), no commissioning year (MW)")
for c, v in sorted(geo.items()):
    print(f"  {c}: {v[0]:,.1f} / {v[1]:,.1f} / {v[2]:,.1f}")
