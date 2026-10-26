import json
from pathlib import Path
L = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10_20261022/cloud_results/20261023T174135Z_halted/light_unpacked/export")
b = json.load(open(L / "batch/M12_BENEFIT/BENEFIT.json"))
def show(o, pre="", depth=0):
    if depth > 2: return
    for k, v in o.items():
        if isinstance(v, dict):
            print(pre + k, "{", ", ".join(list(v.keys())[:14]), "}"); show(v, pre + "  ", depth + 1)
        elif isinstance(v, list):
            print(pre + k, "list", len(v), str(v[:2])[:160])
        else:
            print(pre + k, "=", str(v)[:120])
show(b)
print(sorted(p.name for p in (L / "batch/M12_BENEFIT").iterdir()))
o = json.load(open(L / "R3/m12_owen/OWEN.json")); print("OWEN interval keys", list((o.get("interval_eur") or {}).keys())[:5], "market_form keys", list((o.get("market_form") or {}).keys())[:8])
print("bunker_standalone", str(o.get("bunker_standalone"))[:300])
