import json
R = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/smoke_v2"
for sc in ("integrated", "disconnected"):
    d = f"{R}/{sc}"
    v5 = json.load(open(f"{d}/V5_GATES.json")); p = json.load(open(f"{d}/PRECISION.json")); v6 = json.load(open(f"{d}/V6_ACCEPTANCE.json")); r = json.load(open(f"{d}/SOLVE_RECEIPT.json"))
    print(sc, "objective", r.get("objective"), "tc", r.get("termination_condition"), "s", r.get("solve_seconds"), "rss", (r.get("peak_rss_bytes") or 0) / 2**30)
    print(" v5 keys", list(v5)[:60])
    print(" B16", {k: (v if not isinstance(v, (dict, list)) else "...") for k, v in (v5.get("B16_LEDGER") or {}).items()})
    print(" prec keys", list(p)[:30]); print(" acceptance", json.dumps(p.get("acceptance"))[:500]); print(" grade", json.dumps(p.get("grade"))[:300])
    print(" v6", v6.get("label"), list(v6)[:20])
print(open(f"{R}/STATUS.txt").read()[-900:])
