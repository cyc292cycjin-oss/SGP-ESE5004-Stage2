#!/bin/bash
# DFX v3: read-only inspection for F6 (test structure, first-order JSON, third-batch OWEN / ledger structure)
WT=/home/jin/wt_dfx_v3_20261026; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $WT || exit 1
echo "=== test_m10p_batch3.py $(wc -l < tests/research/test_m10p_batch3.py) lines ==="
grep -n -E "^def |^@pytest|^class |fixture|FAKE_|SOLVE_CMD|ALLOW_UNREGISTERED|def _run|subprocess.run|def fake|RUNNER|run_batch3" tests/research/test_m10p_batch3.py | head -70
echo "=== test_b4p_batch4.py $(wc -l < tests/research/test_b4p_batch4.py) lines ==="
grep -n -E "^def |^@pytest|^class |fixture|FAKE_|SOLVE_CMD|ALLOW_UNREGISTERED|def _run|subprocess.run|def fake|RUNNER|run_batch4" tests/research/test_b4p_batch4.py | head -70
echo "=== first-order json ==="
$PY - <<'P'
import json
f = json.load(open("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/evidence/DFX_FIRST_ORDER.json"))
print("pairs keys:", list(f["pairs"].keys()))
p = f["pairs"][list(f["pairs"].keys())[0]]
print({k: (v if not isinstance(v, (dict, list)) else type(v).__name__ + str(len(v))) for k, v in p.items()})
for k, v in p.items():
    if isinstance(v, dict) and len(v) < 30:
        print(k, json.dumps(v)[:600])
L = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10_20261022/cloud_results/20261023T174135Z_halted/light_unpacked/export/"
o = json.load(open(L + "R1/m12_owen/OWEN.json"))
print("OWEN keys:", list(o.keys())[:40]); print("alpha_main", o.get("alpha_main"), "alloc keys", list((o.get("allocation_eur") or {}).keys()))
print("R1 alloc 0.5:", o["allocation_eur"].get(str(o.get("alpha_main", 0.5))))
s = json.load(open(L + "batch/BATCH3_SUMMARY.json"))
print("B6:", s.get("B6")); print("R1 state:", {k: s["runs"]["R1"][k] for k in ("objective", "v6", "termination", "solve_seconds", "peak_rss_gib")}); print("R2 state:", {k: s["runs"]["R2"][k] for k in ("objective", "v6", "termination", "solve_seconds", "peak_rss_gib")})
import csv
r = list(csv.DictReader(open(L + "R1/COUNTRY_COST_LEDGER.csv"))); print("ledger cols:", list(r[0].keys())[:12]); print([ (x[list(x.keys())[0]], x.get("total")) for x in r[:13]])
o2 = json.load(open("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10s1_20261024/cloud_results/regress/R1/export/R1/m12_owen/OWEN.json"))
print("regress R1 alloc equal:", o2["allocation_eur"].get("0.5") == o["allocation_eur"].get("0.5"))
P
