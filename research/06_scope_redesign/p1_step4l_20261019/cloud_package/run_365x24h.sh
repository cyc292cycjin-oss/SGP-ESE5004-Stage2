#!/bin/bash
# S4L cloud package run script (S4L-3, decision 112 c; successor of the S4K script of package code 56d28358 - NOT yet packaged: the next package
# is built after the user decides the second-batch plan). Same configuration as the S4K package (see the S4K header: S4C .. S4K main settings,
# AC lines with the linear loss proxy) plus whatever the user decides for the second batch (e.g. research.numerics.dust_cleanup, S4L-1).
# Changes against the S4K script (L23 findings 1-3; S4L-3 points 1-2):
#   * each solve runs in its own session / process group (setsid): the wall-clock cap terminates the WHOLE group (time -> python -> any child), not
#     only the direct child (L23: the 3 h kill ended the /usr/bin/time layer, s2_solve.py kept running for 2 min 40 s and wrote its post-solve files
#     after the export and the DONE mark);
#   * after a kill the script waits until the group has exited (TERM, grace, KILL) and only then exports and packs;
#   * before the export the receipt is checked: a receipt without termination_condition / finished_epoch is a PRE-SOLVE receipt (solve not finished
#     or killed) -> STATUS gets RECEIPT_<run>:pre_solve and the run is marked killed_pre_solve / none;
#   * the monitor sums the RSS of the solve process group (pgrep -g) and reads the container cgroup memory limit and usage (v2 memory.max /
#     memory.current, v1 memory.limit_in_bytes / memory.usage_in_bytes) instead of the host /proc/meminfo (L23 finding 2); the host value is
#     kept as a separate column;
#   * --solver-profile accepts formal_barrier_crossover (S4L-2; registry s4l2_profile_formal_barrier_crossover) besides the three S4K profiles.
# PREPARED ONLY - run on the cloud instance after the user has authorised the run (CLAUDE.md: every optimisation needs a separate explicit
# authorisation).
#
#   GRB_LICENSE_FILE=/path/to/gurobi.lic bash run_365x24h.sh --solver-profile formal_barrier --mode serial|lanes2 [--runs ...] [--auth "text"] [--dry-run]
#
# Environment overrides (tests only; the defaults are the production values): WALL_CAP_S (3 h = 10800), GRACE_S (30 s between TERM and KILL),
# GUROBI_TIME_LIMIT_S (10500), MONITOR_S (60), CGROUP_ROOT (/sys/fs/cgroup).
#
# Licence (S4I K2, decision 106 a): the academic WLS licence allows at most 2 concurrent sessions and keeps every token for at least 5 minutes after
# the Gurobi environment is closed. Each s2_solve.py opens one environment; the preflight licence check opens one too. Hence: serial (recommended)
# never needs more than 2 tokens; lanes2 waits LICENCE_GAP_S (330 s) before starting (the preflight token) and again inside a lane before its next
# run (the token of the run just finished); lanes3 is withdrawn (it always needs 3 sessions) and is refused.
#
# --solver-profile is REQUIRED and has no default; the cloud profile confirmed by the user for the first batch was A: formal_barrier (with Kirchhoff
#   row normalisation). Allowed values = research.solver.profiles in configs/research/baseline.yaml:
#   formal_barrier | crossover_diagnostic | barrier_numericfocus2 | formal_barrier_crossover. Without it the script refuses to start.
#
# Runs (default integrated,disconnected,integrated_nze):
#   integrated        integrated main, WEO 2025 STEPS fuel prices;
#   disconnected      disconnected main (STEPS, extra-ASEAN CO2 storage on) - expected feasible;
#   integrated_nze    integrated sensitivity with WEO 2025 NZE fuel prices (research.fuels.price_scenario = nze);
#   disconnected_gap  disconnected gap diagnostic (packaged; runs ONLY when the disconnected main ends non-optimal, or when named in --runs).
# Modes: serial = integrated -> disconnected (-> disconnected_gap) -> integrated_nze (recommended);
#        lanes2 = two lanes at the same time after a 330 s start gap: [integrated -> 330 s -> integrated_nze] and [disconnected (-> 330 s ->
#                 disconnected_gap)];
#        lanes3 = withdrawn (licence: at most 2 concurrent sessions) - refused with the reason.
#
# * one solve per run, no retry, no parameter change, no warm start (stop-loss of the project);
# * wall-clock cap WALL_CAP_S per run (Gurobi TimeLimit GUROBI_TIME_LIMIT_S, hard kill of the process group at the cap);
# * every MONITOR_S seconds: RSS of the solve process group, cgroup memory used / limit, host MemAvailable, free disk and the last Gurobi progress
#   line -> MONITOR_<run>.csv;
# * after each solve: SOLVE_RECEIPT.json, V5_GATES.json (incl. B1_BUNKERS and the decision-71 solver-tolerance gates), INTERIOR_CHECKS.json,
#   BUNKER_ACCOUNT.json, CO2_FLOWS.json (incl. extra_asean_by_country with the Lao transit, intra_asean_shipping), GAP_TABLE.json,
#   COUNTRY_COST_LEDGER.csv (country x subject), COUNTRY_COST_LEDGER_DETAIL.csv, LEDGER_IDENTITY.json, NODAL_PRICES.csv (per bus: mean / min / max
#   and one column per day), GUROBI_LOG_SCRUBBED.txt (licence lines removed), RESOURCE.jsonl, the solved network and the monitor file are
#   copied to export/<run>/; the raw Gurobi log and the CSC LP arrays are NOT exported;
# * the licence file is only referenced through GRB_LICENSE_FILE (never copied, printed or packaged).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
MODE=serial; DRY=0; AUTH=""; RUNS="integrated,disconnected,integrated_nze"; PROFILE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --mode) MODE="$2"; shift 2;;
    --runs) RUNS="$2"; shift 2;;
    --auth) AUTH="$2"; shift 2;;
    --solver-profile) PROFILE="$2"; shift 2;;
    --dry-run) DRY=1; shift;;
    *) echo "unknown argument $1"; exit 2;;
  esac
done
[ -n "$PROFILE" ] || { echo "REFUSED: --solver-profile is required (no default). First-batch profile confirmed by the user: --solver-profile formal_barrier (profile A)."; exit 2; }
case "$PROFILE" in formal_barrier|crossover_diagnostic|barrier_numericfocus2|formal_barrier_crossover) ;; *) echo "REFUSED: unknown solver profile $PROFILE"; exit 2;; esac
case "$MODE" in
  serial|lanes2) ;;
  lanes3) echo "REFUSED: --mode lanes3 is withdrawn (S4I K2, decision 106 a): it needs 3 Gurobi sessions at the same time, the academic WLS licence allows at most 2 and keeps each token >= 5 min. Use --mode serial (recommended) or --mode lanes2."; exit 2;;
  *) echo "--mode serial|lanes2"; exit 2;;
esac
LICENCE_GAP_S=330   # >= 5 min: a closed environment keeps its WLS token for at least 5 minutes
WALL_CAP_S="${WALL_CAP_S:-10800}"; GRACE_S="${GRACE_S:-30}"; GUROBI_TIME_LIMIT_S="${GUROBI_TIME_LIMIT_S:-10500}"; MONITOR_S="${MONITOR_S:-60}"; CGROUP_ROOT="${CGROUP_ROOT:-/sys/fs/cgroup}"
for r in ${RUNS//,/ }; do case "$r" in integrated|disconnected|integrated_nze|disconnected_gap) ;; *) echo "unknown run $r"; exit 2;; esac; done
want() { case ",$RUNS," in *",$1,"*) return 0;; *) return 1;; esac; }
: "${GRB_LICENSE_FILE:?set GRB_LICENSE_FILE to the licence path provided by the user}"
[ -r "$GRB_LICENSE_FILE" ] || { echo "GRB_LICENSE_FILE is not readable"; exit 2; }
command -v setsid >/dev/null 2>&1 || { echo "REFUSED: setsid (util-linux) missing - the wall-clock cap needs a process group per solve"; exit 2; }
[ -n "$AUTH" ] || AUTH="S4L cloud runs 365x24h (authorisation text to be supplied with --auth)"
REPO="$HERE/repo"                 # unpacked code snapshot (make_package.sh -> code_<commit>.tar.gz)
NETS="$HERE/networks"             # integrated_365_24h_unsolved.nc, disconnected_365_24h_unsolved.nc, integrated_nze_365_24h_unsolved.nc, disconnected_gap_diagnostic_365_24h_unsolved.nc
PY="${PY:-python}"                # python of the pypsa-earth environment (environment_pypsa-earth.yml)
RUN="$HERE/runs/$(date -u +%Y%m%dT%H%M%SZ)_$$"; EXP="$RUN/export"
mkdir -p "$(dirname "$RUN")" && mkdir "$RUN" && mkdir "$EXP" || { echo "run folder $RUN exists or cannot be created"; exit 2; }
ST="$RUN/STATUS.txt"
export PYTHONHASHSEED=0
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) mode:$MODE runs:$RUNS solver_profile:$PROFILE commit:$(cat "$HERE/COMMIT" 2>/dev/null) wall_cap_s:$WALL_CAP_S time_limit_s:$GUROBI_TIME_LIMIT_S" >> "$ST"
SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic'   # licence-line filter (written so that the file itself holds no licence keyword)

# ---- container cgroup memory (v2: memory.max / memory.current; v1: memory/memory.limit_in_bytes / memory.usage_in_bytes); "" when unlimited or absent
cg_mem_limit_b() {
  local v=""
  if [ -r "$CGROUP_ROOT/memory.max" ]; then v=$(cat "$CGROUP_ROOT/memory.max")
  elif [ -r "$CGROUP_ROOT/memory/memory.limit_in_bytes" ]; then v=$(cat "$CGROUP_ROOT/memory/memory.limit_in_bytes"); fi
  case "$v" in ""|max) echo "";; *) [ "${#v}" -ge 19 ] && echo "" || echo "$v";; esac   # v1 "unlimited" is 9223372036854771712 (19 digits)
}
cg_mem_used_b() {
  if [ -r "$CGROUP_ROOT/memory.current" ]; then cat "$CGROUP_ROOT/memory.current"
  elif [ -r "$CGROUP_ROOT/memory/memory.usage_in_bytes" ]; then cat "$CGROUP_ROOT/memory/memory.usage_in_bytes"
  else echo ""; fi
}
echo "CGROUP_MEMORY_LIMIT_GIB:$(l=$(cg_mem_limit_b); [ -n "$l" ] && awk -v b="$l" 'BEGIN {printf "%.2f", b/1073741824}' || echo unlimited_or_absent)" >> "$ST"

net_of() { case "$1" in integrated) echo "$NETS/integrated_365_24h_unsolved.nc";; disconnected) echo "$NETS/disconnected_365_24h_unsolved.nc";;
                         integrated_nze) echo "$NETS/integrated_nze_365_24h_unsolved.nc";; disconnected_gap) echo "$NETS/disconnected_gap_diagnostic_365_24h_unsolved.nc";; esac; }
scen_of() { case "$1" in integrated|integrated_nze) echo integrated;; *) echo disconnected;; esac; }
label_of() { case "$1" in disconnected_gap) echo GAP_DIAGNOSTIC;; *) echo FORMAL_TRIAL_365X24H;; esac; }

group_pids() { pgrep -g "$1" 2>/dev/null; }   # every process of the solve's process group (time, python, children)
group_alive() { [ -n "$(group_pids "$1")" ]; }

monitor() {   # $1 pgid $2 run $3 solve dir
  local pg=$1 tag=$2 dir=$3 f="$RUN/MONITOR_$2.csv"
  echo "utc,elapsed_s,rss_gib_group,cgroup_mem_used_gib,cgroup_mem_limit_gib,host_mem_available_gib,disk_free_gib,gurobi_last_line" > "$f"
  local t0=$(date +%s) lim; lim=$(cg_mem_limit_b)
  while group_alive "$pg"; do
    local rss=0
    for p in $(group_pids "$pg"); do
      r=$(ps -o rss= -p "$p" 2>/dev/null | tr -d ' '); [ -n "$r" ] && rss=$((rss + r))
    done
    local used; used=$(cg_mem_used_b)
    local avail=$(awk '/MemAvailable/ {printf "%.2f", $2/1048576}' /proc/meminfo 2>/dev/null)
    local disk=$(df -Pk "$RUN" | awk 'NR==2 {printf "%.1f", $4/1048576}')
    local last=$(tail -n 1 "$dir/gurobi.linopy.log" 2>/dev/null | grep -viE "$SCRUB" | tr ',' ';' | cut -c1-160)
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ),$(( $(date +%s) - t0 )),$(awk -v k=$rss 'BEGIN {printf "%.2f", k/1048576}'),$([ -n "$used" ] && awk -v b="$used" 'BEGIN {printf "%.2f", b/1073741824}' || echo ""),$([ -n "$lim" ] && awk -v b="$lim" 'BEGIN {printf "%.2f", b/1073741824}' || echo ""),$avail,$disk,$last" >> "$f"
    sleep "$MONITOR_S"
  done
}

receipt_state() {   # $1 receipt path -> post_solve | pre_solve | missing
  [ -f "$1" ] || { echo missing; return; }
  "$PY" - "$1" <<'P' 2>/dev/null || echo unreadable
import json, sys
r = json.load(open(sys.argv[1]))
print("post_solve" if ("termination_condition" in r and "finished_epoch" in r) else "pre_solve")
P
}

solve() {   # $1 run tag; prints the termination condition as the last line
  local tag=$1 dir="$RUN/$1" net sc label; net=$(net_of "$1"); sc=$(scen_of "$1"); label=$(label_of "$1")
  mkdir -p "$dir"
  local cmd=("$PY" "$REPO/scripts_project/s2_solve.py" --repo "$REPO" --network "$net" --scenario "$sc" --output "$dir"
             --label "$label" --authorization "$AUTH; run $tag" --solver gurobi --solver-profile "$PROFILE" --scaling on --time-limit "$GUROBI_TIME_LIMIT_S")
  if [ $DRY = 1 ]; then echo "DRY-RUN: ${cmd[*]}" | tee -a "$ST" >/dev/null; echo dry; return 0; fi
  # own session + process group for the solve: the group id equals the pid of /usr/bin/time (setsid does not fork when the caller is not a group leader)
  ( cd "$REPO" && exec setsid /usr/bin/time -v "${cmd[@]}" > "$dir/solve.log" 2> "$dir/solve.err" ) &
  local pid=$! start=$(date +%s) killed=0
  sleep 1
  local pg; pg=$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' '); [ -n "$pg" ] || pg=$pid
  echo "SOLVE_$tag:pid=$pid:pgid=$pg:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$ST"
  monitor "$pg" "$tag" "$dir" &
  local mon=$!
  while kill -0 $pid 2>/dev/null; do
    sleep 5
    if [ $(( $(date +%s) - start )) -ge "$WALL_CAP_S" ]; then
      echo "KILLED_${WALL_CAP_S}S_$tag:$(date -u +%Y-%m-%dT%H:%M:%SZ):group=$pg:members=$(group_pids "$pg" | tr '\n' ' ')" >> "$ST"
      kill -TERM -- "-$pg" 2>/dev/null; killed=1
      local g=0
      while group_alive "$pg" && [ $g -lt "$GRACE_S" ]; do sleep 1; g=$((g + 1)); done
      if group_alive "$pg"; then kill -KILL -- "-$pg" 2>/dev/null; echo "KILL9_$tag:$(date -u +%Y-%m-%dT%H:%M:%SZ):after_grace_${GRACE_S}s" >> "$ST"; fi
      break
    fi
  done
  wait $pid 2>/dev/null
  local w=0   # export only when the whole group has exited (a surviving grandchild would otherwise write after the export, L23 finding 3)
  while group_alive "$pg" && [ $w -lt 120 ]; do sleep 1; w=$((w + 1)); done
  if group_alive "$pg"; then kill -KILL -- "-$pg" 2>/dev/null; sleep 1; echo "GROUP_SURVIVED_$tag:killed_after_120s:$(group_pids "$pg" | tr '\n' ' ')" >> "$ST"; fi
  kill $mon 2>/dev/null; wait $mon 2>/dev/null
  local rs; rs=$(receipt_state "$dir/SOLVE_RECEIPT.json")
  echo "RECEIPT_$tag:$rs" >> "$ST"
  local cond
  if [ "$rs" = post_solve ]; then
    cond=$("$PY" -c "import json,sys; print(json.load(open(sys.argv[1])).get('termination_condition','none'))" "$dir/SOLVE_RECEIPT.json" 2>/dev/null || echo none)
  elif [ $killed = 1 ]; then cond=killed_pre_solve
  else cond=none; fi
  echo "RUN_$tag:$cond:$(( $(date +%s) - start ))s" >> "$ST"
  local e="$EXP/$tag"; mkdir -p "$e"
  for f in SOLVE_RECEIPT.json V5_GATES.json INTERIOR_CHECKS.json BUNKER_ACCOUNT.json GUROBI_LOG_SCRUBBED.txt RESOURCE.jsonl CO2_FLOWS.json GAP_TABLE.json EMISSIONS_BY_COUNTRY.json CAPACITY_BY_TECH_COUNTRY.json cross_border_flows.csv COUNTRY_COST_LEDGER.csv COUNTRY_COST_LEDGER_DETAIL.csv LEDGER_IDENTITY.json NODAL_PRICES.csv; do [ -f "$dir/$f" ] && cp "$dir/$f" "$e/"; done
  [ -f "$dir/solve.log" ] && grep -viE "$SCRUB" "$dir/solve.log" > "$e/solve_log_scrubbed.txt"   # stdout carries the Gurobi licence banner: lines removed
  [ -f "$dir/lp/MATH_PROBLEM.json" ] && cp "$dir/lp/MATH_PROBLEM.json" "$e/"
  [ -f "$dir/v5/kkt_summary.json" ] && cp "$dir/v5/kkt_summary.json" "$e/"
  ls "$dir"/*_solved.nc >/dev/null 2>&1 && cp "$dir"/*_solved.nc "$e/"
  cp "$RUN/MONITOR_$tag.csv" "$e/" 2>/dev/null
  grep -A 30 "Command being timed" "$dir/solve.err" > "$e/solve_time.txt" 2>/dev/null
  if [ "$cond" != "optimal" ]; then tail -60 "$dir/gurobi.linopy.log" 2>/dev/null | grep -viE "$SCRUB" > "$e/LOG_TAIL_NONOPTIMAL.txt"; tail -60 "$dir/solve.err" | grep -viE "$SCRUB" > "$e/STDERR_TAIL_NONOPTIMAL.txt"; fi
  echo "$cond"
}

licence_gap() {   # $1 reason; lanes2 only (serial never holds more than 2 tokens)
  [ "$MODE" = lanes2 ] || return 0
  if [ $DRY = 1 ]; then echo "DRY-RUN: would wait ${LICENCE_GAP_S} s ($1)" >> "$ST"; return 0; fi
  echo "LICENCE_GAP:${LICENCE_GAP_S}s:$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$ST"; sleep "$LICENCE_GAP_S"
}
lane_integrated() { want integrated && solve integrated > /dev/null; }
lane_nze() { want integrated_nze && solve integrated_nze > /dev/null; }
lane_disconnected() {   # the diagnostic runs only when the disconnected main ends non-optimal (or when named explicitly)
  local c="skipped"
  want disconnected && c=$(solve disconnected | tail -1)
  if want disconnected_gap; then licence_gap "before disconnected_gap in the lane"; solve disconnected_gap > /dev/null
  elif [ "$c" != "optimal" ] && [ "$c" != "skipped" ] && [ "$c" != "dry" ]; then echo "DISCONNECTED_MAIN_NON_OPTIMAL:$c -> running disconnected_gap diagnostic" >> "$ST"; licence_gap "before disconnected_gap in the lane"; solve disconnected_gap > /dev/null
  elif [ "$c" = "dry" ]; then echo "DRY-RUN: disconnected_gap would run only if the disconnected main ends non-optimal" >> "$ST"; fi
}
case "$MODE" in
  serial) lane_integrated; lane_disconnected; lane_nze;;
  lanes2) licence_gap "start (token of the preflight licence check)"
          ( lane_integrated; want integrated && want integrated_nze && licence_gap "before integrated_nze in the lane"; lane_nze ) & p1=$!; lane_disconnected & p2=$!; wait $p1 $p2;;
esac
if [ $DRY = 1 ]; then echo "DRY-RUN done (no solve, no export)" >> "$ST"; cat "$ST"; exit 0; fi
if grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" "$EXP" >/dev/null 2>&1; then
  echo "LICENCE STRING FOUND IN EXPORT - not packed" >> "$ST"; exit 1
fi
cp "$ST" "$EXP/"
( cd "$RUN" && tar czf "results_$(basename "$RUN").tar.gz" export && sha256sum "results_$(basename "$RUN").tar.gz" > "results_$(basename "$RUN").tar.gz.sha256" )
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ) export:$RUN/results_$(basename "$RUN").tar.gz" >> "$ST"
cat "$ST"
