#!/bin/bash
# S4Q-2 (decision 123; user authorisation 2026-10-20: SIX local 56x3h runs = candidate BarConvTol 1e-6 x two thread paths x three scenarios, stop-loss
# 30 min each, no retry, no cloud). S4O run pipeline (run_365x24h.sh with automatic C1) in the package-like folder /home/jin/s4q_local/pkg:
# TRUNCATE=56 (label SMOKE_TEST_ONLY), TimeLimit 1,750 s / wall cap 1,800 s, FIXED_RUNS=on (exactly the three named runs: no stop rule, no diagnostic),
# serial with RUN_GAP_S 330 s; invocation 1 = formal_barrier_1e6 (Threads 8), invocation 2 = formal_barrier_1e6_t16 (Threads 16); >= 330 s between the
# last solve of invocation 1 and the first solve of invocation 2. The licence is only referenced through GRB_LICENSE_FILE.
set -u
P=/home/jin/s4q_local/pkg; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; DS=/home/jin/s4q_local/DRIVER_STATUS.txt
GAP=330
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $DS; }
busy() { ps -eo cmd | grep -cE '[s]2_solve.py|[g]urobi_cl'; }
cd $P
log DRIVER_START "commit=$(cat COMMIT | cut -c1-8)"
prev=""
for prof in formal_barrier_1e6 formal_barrier_1e6_t16; do
  ( PREFLIGHT_ONLY=profile,c1,versions,tools PY=$PY bash preflight.sh serial $prof ) > $P/preflight_$prof.txt 2>&1
  log PREFLIGHT_$prof "$(grep -cE '^PREFLIGHT OK' $P/preflight_$prof.txt)ok"
  if [ -n "$prev" ]; then
    last=$(cat $prev/.last_solve_end 2>/dev/null || date +%s)
    while [ $(( $(date +%s) - last )) -lt $GAP ]; do sleep 5; done
    log GAP_BEFORE_$prof "$(( $(date +%s) - last ))s"
  fi
  n=$(busy); [ "$n" = 0 ] || { log SOLVER_BUSY_BEFORE_$prof "$n processes - waiting"; while [ "$(busy)" != 0 ]; do sleep 10; done; log SOLVER_FREE_$prof; }
  log INVOKE_$prof
  TRUNCATE=56 GUROBI_TIME_LIMIT_S=1750 WALL_CAP_S=1800 MONITOR_S=10 RUN_GAP_S=$GAP FIXED_RUNS=on GRB_LICENSE_FILE=/home/jin/gurobi.lic PY=$PY \
    bash run_365x24h.sh --mode serial --solver-profile $prof --runs integrated,disconnected,integrated_nze \
      --auth "S4Q-2 (decision 123; user authorisation 2026-10-20): local 56x3h level-1 calibration, candidate profile $prof, six runs in total, stop-loss 30 min, no retry" \
      > $P/run_stdout_$prof.txt 2>&1
  rc=$?
  prev=$(ls -td $P/runs/*/ | head -1); prev=${prev%/}
  log END_$prof "exit=$rc:run=$(basename $prev):$(grep -E '^RUN_' $prev/STATUS.txt | tr '\n' ' ')"
done
log DRIVER_DONE
