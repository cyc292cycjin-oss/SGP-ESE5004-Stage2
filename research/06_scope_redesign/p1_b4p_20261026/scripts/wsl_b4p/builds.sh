#!/bin/bash
# B4P A1.2: --stop-before-solve builds of the 2920x3h networks truncated to N snapshots (no solver call; GRB_LICENSE_FILE removed).
# Measures: build seconds, peak RSS (GNU time + Sampler), LP size, lp/ array bytes. Sequence 56, 112, 182, then 273 only when the 182 peak
# x 1.55 stays below 8.5 GiB (WSL 10.95 GiB; the instruction stops a measurement above 90 % of memory, so 365 is not attempted locally).
set -u
WT=/home/jin/wt_b4p_20261026; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; export PYTHONHASHSEED=0
NETS=$MAIN/results_project/m08b/builds_s01; R=$MAIN/results_project/b4p; B=$R/builds; ST=$R/BUILDS_STATUS.txt
export TMPDIR=$R/tmp; mkdir -p "$B" "$TMPDIR"
cd "$WT" || exit 1
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> "$ST"; }
log START "head=$(git rev-parse HEAD)"
one() {   # $1 scenario $2 N
  local sc=$1 N=$2 d=$B/${1}_$2
  [ -f "$d/SOLVE_RECEIPT.json" ] && { log SKIP_${sc}_$N exists; return 0; }
  mkdir -p "$d"; local t0=$(date +%s)
  ( env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" scripts_project/s2_solve.py --repo . --network "$NETS/$sc/${sc}_2920_3h_unsolved.nc" --scenario "$sc" --output "$d" \
      --label SMOKE_TEST_ONLY --authorization "B4P A1.2 build-only measurement (user authorisation 2026-10-26 03:15: --stop-before-solve builds of the truncated 2920x3h networks; no solver call)" \
      --solver gurobi --solver-profile formal_barrier_1e6_t16 --scaling on --time-limit 259200 --costs-table "$NETS/$sc/costs_active_research.csv" --truncate "$N" --stop-before-solve \
      > "$d/build.log" 2> "$d/build.err" ); local ex=$?
  local peak; peak=$(grep -h "Maximum resident" "$d/build.err" | awk '{print $NF}')
  local lpb; lpb=$(du -sb "$d/lp" 2>/dev/null | cut -f1)
  log BUILD_${sc}_$N "exit=$ex:$(( $(date +%s) - t0 ))s:peak_kb=${peak:-none}:lp_bytes=${lpb:-none}:$(tail -1 "$d/build.log" | cut -c1-300)"
  echo "${peak:-0}"
}
for N in 56 112 182; do for sc in integrated disconnected; do one $sc $N > /dev/null; done; done
p182=$(grep -h "Maximum resident" "$B/integrated_182/build.err" | awk '{print $NF}')
if [ -n "$p182" ] && [ "$p182" -gt 0 ] && [ $(( p182 * 155 / 100 )) -lt $(( 8500 * 1024 )) ]; then
  log DECIDE_273 "integrated_182 peak ${p182} kB x 1.55 < 8.5 GiB -> 273 attempted"
  for sc in integrated disconnected; do one $sc 273 > /dev/null; done
else
  log DECIDE_273 "integrated_182 peak ${p182:-none} kB -> 273 not attempted (90 % rule)"
fi
log DONE
echo DONE >> "$ST"
