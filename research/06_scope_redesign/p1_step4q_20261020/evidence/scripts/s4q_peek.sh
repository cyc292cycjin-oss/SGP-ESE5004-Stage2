#!/bin/bash
# light peek at finished runs: objective vs S4M-2, iterations / barrier s / WU, KKT relative gap
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
$PY - <<'P'
import json, re, glob, os
S = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4m/s4m2/solves"
for r in sorted(glob.glob("/home/jin/s4q_local/pkg/runs/*/")):
    prof = re.search(r"solver_profile:(\S+)", open(r + "STATUS.txt").read()).group(1)
    for sc in ("integrated", "disconnected", "integrated_nze"):
        d = r + sc
        if not os.path.exists(d + "/SOLVE_RECEIPT.json"): continue
        rec = json.load(open(d + "/SOLVE_RECEIPT.json"))
        if "termination_condition" not in rec: continue
        ref = json.load(open(f"{S}/s4m_A_{sc}/SOLVE_RECEIPT.json"))["objective"]
        it = sec = wu = None
        for ln in open(d + "/GUROBI_LOG_SCRUBBED.txt", errors="ignore"):
            m = re.match(r"Barrier solved model in (\d+) iterations and ([\d.]+) seconds(?: \(([\d.]+) work units\))?", ln)
            if m: it, sec, wu = m.groups()
        k = json.load(open(d + "/v5/kkt_summary.json")) if os.path.exists(d + "/v5/kkt_summary.json") else {}
        g = json.load(open(d + "/V5_GATES.json")) if os.path.exists(d + "/V5_GATES.json") else {}
        print(f"{prof} {sc}: {rec['termination_condition']} obj {rec['objective']:.4f} rel_vs_A {rec['objective']/ref-1:+.2e} it {it} barrier_s {sec} WU {wu} kkt_rel_gap {k.get('relative_gap')} B16 {(g.get('B16_LEDGER') or {}).get('relative_error')}")
P
