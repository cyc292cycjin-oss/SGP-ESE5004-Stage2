#!/bin/bash
# S4N-3: download the light probe outputs (single scp, no parallel stream) and scan them for licence strings. Host / port from the calling environment.
set -u
source /home/jin/s4n_ssh.sh
P=/root/autodl-tmp/s4m_cloud/probe/20261019T071010Z_3872
E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019/evidence/s4n_3
mkdir -p $E
s4n_scp -q "root@$S4N_HOST:$P/SPEED_PROBE.json" "root@$S4N_HOST:$P/STATUS.txt" "root@$S4N_HOST:$P/GUROBI_LOG_SCRUBBED.txt" "root@$S4N_HOST:$P/solve_log_scrubbed.txt" "root@$S4N_HOST:$P/solve/SOLVE_RECEIPT.json" "root@$S4N_HOST:$P/solve/V5_GATES.json" $E/ || echo "SCP_FAILED"
s4n_ssh "grep -v '^AUTH' /root/autodl-tmp/s4n_probe_launch.txt; grep -A 25 'Command being timed' $P/solve.err | grep -viE 'licen[cs]e|registered|wls|academic'" > $E/PROBE_LAUNCH_AND_TIME.txt
H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $E)
[ -z "$H" ] && echo "LICENCE_SCAN_PROBE_EVIDENCE: no hit ($(ls $E | wc -l) files)" || { echo "LICENCE STRING FOUND:"; echo "$H"; }
/home/jin/miniforge3/envs/pypsa-earth/bin/python - $E <<'P'
import json, sys
e = sys.argv[1]
g = json.load(open(e + "/V5_GATES.json")); r = json.load(open(e + "/SOLVE_RECEIPT.json"))
print("gates all_passed_solver_tolerances", g.get("all_passed_solver_tolerances"), "failed", sorted(k for k, v in g.items() if isinstance(v, dict) and "passed" in v and not v["passed"]))
print("peak_rss_GiB", round((r.get("peak_rss_bytes") or 0) / 2**30, 2), "solve_seconds", round(r.get("solve_seconds") or 0, 1), "lp", [r["lp"].get(k) for k in ("num_row", "num_col", "nnz")], "build_seconds", round(r["lp"].get("build_seconds") or 0, 1))
P
grep -E "Elapsed|Maximum resident" $E/PROBE_LAUNCH_AND_TIME.txt
