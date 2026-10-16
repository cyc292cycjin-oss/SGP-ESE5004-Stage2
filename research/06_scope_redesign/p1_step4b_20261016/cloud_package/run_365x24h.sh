#!/bin/bash
# S4B cloud package: first formal day-resolution trial, 365x24h, with the S4B main configuration (research.s3.fuel_carbon_mode = origin_neutral,
# research.renewable.profile_variant = calibrated_modern, resource_classes 3, decisions 70-79, typhoon_premium off; solver profile formal_barrier,
# scaling on). PREPARED ONLY - run on the cloud instance after the user has authorised the run (CLAUDE.md: every optimisation needs a separate
# explicit authorisation).
#
#   GRB_LICENSE_FILE=/path/to/gurobi.lic bash run_365x24h.sh --mode serial|parallel [--runs integrated,disconnected,disconnected_gap] [--auth "text"] [--dry-run]
#
# Runs (default all three):
#   integrated        integrated main (must be OPTIMAL to be used);
#   disconnected      disconnected main - expected to end non-optimal (INFEASIBLE / INF_OR_UNBD / NUMERIC) because of the structural CO2 gap
#                     (decisions 49, 53, 73); the status is recorded, it is not a failure of the package;
#   disconnected_gap  disconnected gap diagnostic (penalised electricity / CO2 / biomass / gas slacks, decision 73; must be OPTIMAL).
# Modes: serial = integrated -> disconnected -> disconnected_gap; parallel = two lanes at the same time: [integrated] and [disconnected -> disconnected_gap].
#
# * one solve per run, no retry, no parameter change, no warm start (stop-loss of the project);
# * wall-clock cap 3 h per run (Gurobi TimeLimit 10,500 s, hard kill at 10,800 s);
# * every 60 s: RSS of the solve process tree, free memory, free disk and the last Gurobi progress line -> MONITOR_<run>.csv;
# * after each solve: SOLVE_RECEIPT.json, V5_GATES.json (incl. the decision-71 solver-tolerance gates), INTERIOR_CHECKS.json, GAP_TABLE.json,
#   GUROBI_LOG_SCRUBBED.txt (licence lines removed), RESOURCE.jsonl, the solved network and the monitor file are copied to export/<run>/;
#   the raw Gurobi log and the CSC LP arrays are NOT exported;
# * the licence file is only referenced through GRB_LICENSE_FILE (never copied, printed or packaged).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
MODE=serial; DRY=0; AUTH=""; RUNS="integrated,disconnected,disconnected_gap"
while [ $# -gt 0 ]; do
  case "$1" in
    --mode) MODE="$2"; shift 2;;
    --runs) RUNS="$2"; shift 2;;
    --auth) AUTH="$2"; shift 2;;
    --dry-run) DRY=1; shift;;
    *) echo "unknown argument $1"; exit 2;;
  esac
done
[ "$MODE" = serial ] || [ "$MODE" = parallel ] || { echo "--mode serial|parallel"; exit 2; }
for r in ${RUNS//,/ }; do case "$r" in integrated|disconnected|disconnected_gap) ;; *) echo "unknown run $r"; exit 2;; esac; done
want() { case ",$RUNS," in *",$1,"*) return 0;; *) return 1;; esac; }
: "${GRB_LICENSE_FILE:?set GRB_LICENSE_FILE to the licence path provided by the user}"
[ -r "$GRB_LICENSE_FILE" ] || { echo "GRB_LICENSE_FILE is not readable"; exit 2; }
[ -n "$AUTH" ] || AUTH="S4B cloud trial 365x24h (authorisation text to be supplied with --auth)"
REPO="$HERE/repo"                 # unpacked code snapshot (make_package.sh -> code_<commit>.tar.gz)
NETS="$HERE/networks"             # integrated_365_24h_unsolved.nc, disconnected_365_24h_unsolved.nc, disconnected_gap_diagnostic_365_24h_unsolved.nc
PY="${PY:-python}"                # python of the pypsa-earth environment (environment_pypsa-earth.yml)
RUN="$HERE/runs/$(date -u +%Y%m%dT%H%M%SZ)"; EXP="$RUN/export"
mkdir -p "$RUN" "$EXP"
ST="$RUN/STATUS.txt"
export PYTHONHASHSEED=0
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) mode:$MODE runs:$RUNS commit:$(cat "$HERE/COMMIT" 2>/dev/null)" >> "$ST"
SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic'   # licence-line filter (written so that the file itself holds no licence keyword)

net_of() { case "$1" in integrated) echo "$NETS/integrated_365_24h_unsolved.nc";; disconnected) echo "$NETS/disconnected_365_24h_unsolved.nc";; disconnected_gap) echo "$NETS/disconnected_gap_diagnostic_365_24h_unsolved.nc";; esac; }
scen_of() { case "$1" in integrated) echo integrated;; *) echo disconnected;; esac; }
label_of() { case "$1" in disconnected_gap) echo GAP_DIAGNOSTIC;; *) echo FORMAL_TRIAL_365X24H;; esac; }

monitor() {   # $1 pid $2 run $3 solve dir
  local pid=$1 tag=$2 dir=$3 f="$RUN/MONITOR_$2.csv" net; net=$(net_of "$2")
  echo "utc,elapsed_s,rss_gib_tree,mem_available_gib,disk_free_gib,gurobi_last_line" > "$f"
  local t0=$(date +%s)
  while kill -0 "$pid" 2>/dev/null; do
    local rss=0
    for p in $pid $(pgrep -P "$pid" 2>/dev/null) $(pgrep -f "s2_solve.py --repo $REPO --network $net" 2>/dev/null); do
      r=$(ps -o rss= -p "$p" 2>/dev/null | tr -d ' '); [ -n "$r" ] && rss=$((rss + r))
    done
    local avail=$(awk '/MemAvailable/ {printf "%.2f", $2/1048576}' /proc/meminfo)
    local disk=$(df -Pk "$RUN" | awk 'NR==2 {printf "%.1f", $4/1048576}')
    local last=$(tail -n 1 "$dir/gurobi.linopy.log" 2>/dev/null | grep -viE "$SCRUB" | tr ',' ';' | cut -c1-160)
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ),$(( $(date +%s) - t0 )),$(awk -v k=$rss 'BEGIN {printf "%.2f", k/1048576}'),$avail,$disk,$last" >> "$f"
    sleep 60
  done
}

solve() {   # $1 run tag
  local tag=$1 dir="$RUN/$1" net sc label; net=$(net_of "$1"); sc=$(scen_of "$1"); label=$(label_of "$1")
  mkdir -p "$dir"
  local cmd=("$PY" "$REPO/scripts_project/s2_solve.py" --repo "$REPO" --network "$net" --scenario "$sc" --output "$dir"
             --label "$label" --authorization "$AUTH; run $tag" --solver gurobi --solver-profile formal_barrier --scaling on --time-limit 10500)
  if [ $DRY = 1 ]; then echo "DRY-RUN: ${cmd[*]}" | tee -a "$ST"; return 0; fi
  ( cd "$REPO" && /usr/bin/time -v "${cmd[@]}" > "$dir/solve.log" 2> "$dir/solve.err" ) &
  local pid=$! start=$(date +%s)
  monitor $pid "$tag" "$dir" &
  local mon=$!
  while kill -0 $pid 2>/dev/null; do
    sleep 15
    if [ $(( $(date +%s) - start )) -ge 10800 ]; then
      pkill -TERM -P $pid 2>/dev/null; kill -TERM $pid 2>/dev/null; sleep 10; pkill -KILL -P $pid 2>/dev/null; kill -KILL $pid 2>/dev/null
      echo "KILLED_3H_$tag:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$ST"
    fi
  done
  wait $pid 2>/dev/null; kill $mon 2>/dev/null
  local cond=$("$PY" -c "import json,sys; print(json.load(open(sys.argv[1])).get('termination_condition','none'))" "$dir/SOLVE_RECEIPT.json" 2>/dev/null || echo none)
  echo "RUN_$tag:$cond:$(( $(date +%s) - start ))s" >> "$ST"
  [ "$tag" = disconnected ] && echo "DISCONNECTED_MAIN_EXPECTED_NON_OPTIMAL:$cond" >> "$ST"
  # export (raw Gurobi log and the CSC LP arrays stay on the instance)
  local e="$EXP/$tag"; mkdir -p "$e"
  for f in SOLVE_RECEIPT.json V5_GATES.json INTERIOR_CHECKS.json GUROBI_LOG_SCRUBBED.txt RESOURCE.jsonl CO2_FLOWS.json GAP_TABLE.json EMISSIONS_BY_COUNTRY.json CAPACITY_BY_TECH_COUNTRY.json cross_border_flows.csv; do [ -f "$dir/$f" ] && cp "$dir/$f" "$e/"; done
  [ -f "$dir/solve.log" ] && grep -viE "$SCRUB" "$dir/solve.log" > "$e/solve_log_scrubbed.txt"   # stdout carries the Gurobi licence banner: lines removed
  [ -f "$dir/lp/MATH_PROBLEM.json" ] && cp "$dir/lp/MATH_PROBLEM.json" "$e/"
  [ -f "$dir/v5/kkt_summary.json" ] && cp "$dir/v5/kkt_summary.json" "$e/"
  ls "$dir"/*_solved.nc >/dev/null 2>&1 && cp "$dir"/*_solved.nc "$e/"
  cp "$RUN/MONITOR_$tag.csv" "$e/" 2>/dev/null
  grep -A 30 "Command being timed" "$dir/solve.err" > "$e/solve_time.txt" 2>/dev/null
  if [ "$cond" != "optimal" ]; then tail -60 "$dir/gurobi.linopy.log" 2>/dev/null | grep -viE "$SCRUB" > "$e/LOG_TAIL_NONOPTIMAL.txt"; tail -60 "$dir/solve.err" | grep -viE "$SCRUB" > "$e/STDERR_TAIL_NONOPTIMAL.txt"; fi
}

lane_disconnected() { want disconnected && solve disconnected; want disconnected_gap && solve disconnected_gap; }
if [ "$MODE" = serial ]; then
  want integrated && solve integrated; lane_disconnected
else
  ( want integrated && solve integrated ) & p1=$!; lane_disconnected & p2=$!; wait $p1 $p2
fi
if [ $DRY = 1 ]; then echo "DRY-RUN done (no solve, no export)" >> "$ST"; cat "$ST"; exit 0; fi
if grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" "$EXP" >/dev/null 2>&1; then
  echo "LICENCE STRING FOUND IN EXPORT - not packed" >> "$ST"; exit 1
fi
cp "$ST" "$EXP/"
( cd "$RUN" && tar czf "results_$(basename "$RUN").tar.gz" export && sha256sum "results_$(basename "$RUN").tar.gz" > "results_$(basename "$RUN").tar.gz.sha256" )
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ) export:$RUN/results_$(basename "$RUN").tar.gz" >> "$ST"
cat "$ST"
