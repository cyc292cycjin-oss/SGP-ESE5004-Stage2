#!/bin/bash
# S4O cloud package run script (S4O-2 / S4O-4, decision 120): the S4M script with
#   * the PRODUCTION profile pypsa_eur_default as the default of --solver-profile (decision 120; before: required, no default); the profile is
#     recorded in STATUS; profile A (formal_barrier) and the other registered profiles stay selectable;
#   * the C1 precision step of decision 119 after every solve (Python only, GRB_LICENSE_FILE removed from its environment, no solver call):
#     l23_violation_analysis.py -> VIOLATIONS.json, then scripts_project/s4o_c1_precision.py run -> PRECISION.json / PRECISION.md, both registered
#     in EXPORTS.json and copied to export/<run>/; STATUS line PRECISION_<run>:<grade>:accepted=<bool>:abc=<a><b><c>:ref=<L23|batch>.
#     Run acceptance (decision 120) = Gurobi optimal + (a)(b)(c); the project solver-tolerance gates are reported as numerical information;
#   * the per-country tolerance of (b) / (c): the L23 365x24h difference until the batch has both STEPS runs (integrated and disconnected
#     COUNTRY_COST_LEDGER.csv), then BATCH_REFERENCE.json (this batch's disconnected - integrated difference) and every finished run is re-graded
#     (s4o_c1_precision.py regrade; the earlier grade is kept in grade_history); STATUS lines BATCH_REFERENCE / REGRADE_<run>;
#   * serial mode waits RUN_GAP_S (default 330 s, >= 5 min) between the end of one solve and the start of the next (project rule: adjacent Gurobi
#     runs >= 5 min apart; the C1 step counts towards the gap); STATUS line GAP_<run>;
#   * stop rule (S4O instruction): when the integrated run ends non-optimal AND its C1 does not pass (a)(b)(c), no further run is started
#     (STATUS STOP_INTEGRATED_NONOPTIMAL_C1_FAILED); a non-optimal run otherwise gets its C1 and export as usual and the batch continues (no retry).
# S4M cloud package run script (S4M-3, decision 116): the S4L script with the TimeLimit / wall-clock defaults scaled to 14,400 / 15,300 s (L23: the integrated
# and NZE runs exceeded 3 h on a Xeon Silver 4214R instance); everything else as in S4L. Successor of the S4K package 56d28358 (void).
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
#   GRB_LICENSE_FILE=/path/to/gurobi.lic bash run_365x24h.sh [--solver-profile pypsa_eur_default] --mode serial|lanes2 [--runs ...] [--auth "text"] [--dry-run]
#
# Run parameters (S4M-3, decision 116; environment variables, defaults scaled from the L23 measurements, CLOUD_RESOURCE_ESTIMATE.md section 21-22): WALL_CAP_S (15300 s = 4.25 h), GRACE_S (30 s between TERM and KILL),
# GUROBI_TIME_LIMIT_S (14400 s = 4 h), MONITOR_S (60), CGROUP_ROOT (/sys/fs/cgroup). The user may override both caps in the launch command (e.g. after the speed probe).
# S4O: RUN_GAP_S (330 s, serial mode), C1_STEP (on | off; off only for script tests without the research code).
#
# Licence (S4I K2, decision 106 a): the academic WLS licence allows at most 2 concurrent sessions and keeps every token for at least 5 minutes after
# the Gurobi environment is closed. Each s2_solve.py opens one environment; the preflight licence check opens one too. Hence: serial (recommended)
# never needs more than 2 tokens; lanes2 waits LICENCE_GAP_S (330 s) before starting (the preflight token) and again inside a lane before its next
# run (the token of the run just finished); lanes3 is withdrawn (it always needs 3 sessions) and is refused.
#
# --solver-profile defaults to pypsa_eur_default (S4O, decision 120: the production profile; until S4N it was REQUIRED without default and the first
#   batch / the S4N pilot used A: formal_barrier). Allowed values = research.solver.profiles in configs/research/baseline.yaml:
#   pypsa_eur_default | formal_barrier | crossover_diagnostic | barrier_numericfocus2 | formal_barrier_crossover (abandoned, record only).
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
#   BUNKER_ACCOUNT.json, CO2_FLOWS.json (incl. extra_asean_by_country with the Lao transit, intra_asean_shipping), GAP_TABLE.json, DUALS_BY_CONSTRAINT.nc (every
#   linopy constraint dual incl. the static capacity bounds and the research hooks; S4M supplement 01), DUALS_INDEX.csv, COMPONENT_COST_BREAKDOWN.csv (+ summary),
#   costs_active_research.csv (the build cost table, packaged per scenario), EXPORTS.json (sizes and SHA256 of the new exports),
#   COUNTRY_COST_LEDGER.csv (country x subject), COUNTRY_COST_LEDGER_DETAIL.csv, LEDGER_IDENTITY.json, NODAL_PRICES.csv (per bus: mean / min / max
#   and one column per day), GUROBI_LOG_SCRUBBED.txt (licence lines removed), RESOURCE.jsonl, the solved network and the monitor file are
#   copied to export/<run>/; the raw Gurobi log and the CSC LP arrays are NOT exported;
# * the licence file is only referenced through GRB_LICENSE_FILE (never copied, printed or packaged).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
MODE=serial; DRY=0; AUTH=""; RUNS="integrated,disconnected,integrated_nze"; PROFILE=""; PROFILE_SRC="--solver-profile"
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
[ -n "$PROFILE" ] || { PROFILE=pypsa_eur_default; PROFILE_SRC="default (decision 120)"; }
case "$PROFILE" in pypsa_eur_default|formal_barrier|crossover_diagnostic|barrier_numericfocus2|formal_barrier_crossover) ;; *) echo "REFUSED: unknown solver profile $PROFILE"; exit 2;; esac
case "$MODE" in
  serial|lanes2) ;;
  lanes3) echo "REFUSED: --mode lanes3 is withdrawn (S4I K2, decision 106 a): it needs 3 Gurobi sessions at the same time, the academic WLS licence allows at most 2 and keeps each token >= 5 min. Use --mode serial (recommended) or --mode lanes2."; exit 2;;
  *) echo "--mode serial|lanes2"; exit 2;;
esac
LICENCE_GAP_S=330   # >= 5 min: a closed environment keeps its WLS token for at least 5 minutes
WALL_CAP_S="${WALL_CAP_S:-15300}"; GRACE_S="${GRACE_S:-30}"; GUROBI_TIME_LIMIT_S="${GUROBI_TIME_LIMIT_S:-14400}"; MONITOR_S="${MONITOR_S:-60}"; CGROUP_ROOT="${CGROUP_ROOT:-/sys/fs/cgroup}"
RUN_GAP_S="${RUN_GAP_S:-330}"; C1_STEP="${C1_STEP:-on}"   # S4O: >= 5 min between adjacent solves (serial); C1 precision step after every solve
for r in ${RUNS//,/ }; do case "$r" in integrated|disconnected|integrated_nze|disconnected_gap) ;; *) echo "unknown run $r"; exit 2;; esac; done
want() { [ -f "${RUN:-/nonexistent}/STOP" ] && return 1; case ",$RUNS," in *",$1,"*) return 0;; *) return 1;; esac; }   # S4O: no run after a STOP
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
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) mode:$MODE runs:$RUNS solver_profile:$PROFILE commit:$(cat "$HERE/COMMIT" 2>/dev/null) wall_cap_s:$WALL_CAP_S time_limit_s:$GUROBI_TIME_LIMIT_S profile_source:${PROFILE_SRC// /_} run_gap_s:$RUN_GAP_S c1_step:$C1_STEP" >> "$ST"
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

c1_summary() {   # $1 PRECISION.json -> "<grade>:accepted=<bool>:abc=<a><b><c>:ref=<L23|batch>"
  "$PY" - "$1" <<'P' 2>/dev/null || echo "unreadable"
import json, sys
r = json.load(open(sys.argv[1])); g = r.get("grade", {}); a = r.get("acceptance", {}); src = (r.get("reference") or {}).get("source", "")
print(f"{g.get('grade')}:accepted={a.get('accepted')}:abc={int(bool(g.get('a')))}{int(bool(g.get('b')))}{int(bool(g.get('c')))}:ref={'batch' if src.startswith('this batch') else 'L23'}")
P
}
c1_abc() { [ -f "$RUN/$1/PRECISION.json" ] && c1_summary "$RUN/$1/PRECISION.json" | grep -q ':abc=111:'; }   # (a)(b)(c) all passed

precision() {   # $1 run tag $2 solve dir $3 network $4 scenario $5 label - decision 119 C1 / decision 120 acceptance (Python only, no licence, no solver)
  local tag=$1 dir=$2 net=$3 sc=$4 label=$5 ref=()
  [ "$C1_STEP" = on ] || { echo "PRECISION_$tag:skipped(C1_STEP=$C1_STEP)" >> "$ST"; return 0; }
  [ -f "$RUN/BATCH_REFERENCE.json" ] && ref=(--reference "$RUN/BATCH_REFERENCE.json")
  local va=("$PY" "$REPO/scripts_project/l23_violation_analysis.py" --repo "$REPO" --solve-dir "$dir" --network "$net" --scenario "$sc" --label "$label" --out "$dir/VIOLATIONS.json")
  local c1=("$PY" "$REPO/scripts_project/s4o_c1_precision.py" run --repo "$REPO" --solve-dir "$dir" --network "$net" --scenario "$sc" --label "$label" --violations "$dir/VIOLATIONS.json" ${ref[@]+"${ref[@]}"})
  if [ $DRY = 1 ]; then echo "DRY-RUN: C1 ${va[*]} ; ${c1[*]}" >> "$ST"; return 0; fi
  local t0; t0=$(date +%s)
  if [ -f "$dir/solution/X.npy" ]; then
    ( cd "$REPO" && exec env -u GRB_LICENSE_FILE /usr/bin/time -v "${va[@]}" > "$dir/c1_violations.log" 2> "$dir/c1_violations.err" )
  fi
  ( cd "$REPO" && exec env -u GRB_LICENSE_FILE /usr/bin/time -v "${c1[@]}" > "$dir/c1_precision.log" 2> "$dir/c1_precision.err" ); local rc=$?
  [ $rc = 0 ] || grep -viE "$SCRUB" "$dir/c1_precision.err" | tail -40 > "$dir/C1_ERR_TAIL.txt"
  echo "PRECISION_$tag:$( [ -f "$dir/PRECISION.json" ] && c1_summary "$dir/PRECISION.json" || echo missing):exit=$rc:$(( $(date +%s) - t0 ))s:$(grep -h 'Maximum resident' "$dir/c1_precision.err" "$dir/c1_violations.err" 2>/dev/null | awk '{printf "%.1fGiB ", $NF/1048576}')" >> "$ST"
}

batch_regrade() {   # S4O: once both STEPS runs have ledgers -> BATCH_REFERENCE.json (this batch's disconnected - integrated) and re-grade every finished run
  [ $DRY = 1 ] && { echo "DRY-RUN: batch reference + re-grade once integrated and disconnected have ledgers" >> "$ST"; return 0; }
  [ "$C1_STEP" = on ] || return 0
  [ -f "$RUN/integrated/COUNTRY_COST_LEDGER.csv" ] && [ -f "$RUN/disconnected/COUNTRY_COST_LEDGER.csv" ] || return 0
  if [ ! -f "$RUN/BATCH_REFERENCE.json" ]; then
    env -u GRB_LICENSE_FILE "$PY" "$REPO/scripts_project/s4o_c1_precision.py" reference --integrated "$RUN/integrated" --disconnected "$RUN/disconnected" --out "$RUN/BATCH_REFERENCE.json" > "$RUN/c1_reference.log" 2>&1 \
      && echo "BATCH_REFERENCE:$(date -u +%Y-%m-%dT%H:%M:%SZ):integrated=$(cat "$RUN/integrated/.cond" 2>/dev/null):disconnected=$(cat "$RUN/disconnected/.cond" 2>/dev/null)" >> "$ST" \
      || { echo "BATCH_REFERENCE:failed" >> "$ST"; return 0; }
    cp "$RUN/BATCH_REFERENCE.json" "$EXP/"
  fi
  local t
  for t in integrated disconnected integrated_nze disconnected_gap; do
    [ -f "$RUN/$t/PRECISION.json" ] || continue
    c1_summary "$RUN/$t/PRECISION.json" | grep -q ':ref=batch' && continue
    env -u GRB_LICENSE_FILE "$PY" "$REPO/scripts_project/s4o_c1_precision.py" regrade --solve-dir "$RUN/$t" --reference "$RUN/BATCH_REFERENCE.json" > "$RUN/$t/c1_regrade.log" 2>&1; local rc=$?
    echo "REGRADE_$t:$(c1_summary "$RUN/$t/PRECISION.json"):exit=$rc" >> "$ST"
    mkdir -p "$EXP/$t"; for f in PRECISION.json PRECISION.md EXPORTS.json; do [ -f "$RUN/$t/$f" ] && cp "$RUN/$t/$f" "$EXP/$t/"; done
  done
}

gap_wait() {   # $1 run tag; serial mode: >= RUN_GAP_S between the end of the previous solve and this one (project rule >= 5 min)
  [ "$MODE" = serial ] && [ -f "$RUN/.last_solve_end" ] || return 0
  local last; last=$(cat "$RUN/.last_solve_end"); [ $DRY = 1 ] && { echo "DRY-RUN: would wait until ${RUN_GAP_S} s after the previous solve ($1)" >> "$ST"; return 0; }
  while [ $(( $(date +%s) - last )) -lt "$RUN_GAP_S" ]; do sleep 5; done
  echo "GAP_$1:$(( $(date +%s) - last ))s:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$ST"
}

solve() {   # $1 run tag; prints the termination condition as the last line
  local tag=$1 dir="$RUN/$1" net sc label; net=$(net_of "$1"); sc=$(scen_of "$1"); label=$(label_of "$1")
  mkdir -p "$dir"
  local cmd=("$PY" "$REPO/scripts_project/s2_solve.py" --repo "$REPO" --network "$net" --scenario "$sc" --output "$dir"
             --label "$label" --authorization "$AUTH; run $tag" --solver gurobi --solver-profile "$PROFILE" --scaling on --time-limit "$GUROBI_TIME_LIMIT_S" --costs-table "$NETS/${1}_costs_active_research.csv")
  gap_wait "$tag"
  if [ $DRY = 1 ]; then echo "DRY-RUN: ${cmd[*]}" | tee -a "$ST" >/dev/null; precision "$tag" "$dir" "$net" "$sc" "$label"; date +%s > "$RUN/.last_solve_end"; echo dry; return 0; fi
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
  echo "$cond" > "$dir/.cond"; date +%s > "$RUN/.last_solve_end"   # S4O: the gap to the next solve counts from here (the C1 step is part of it)
  precision "$tag" "$dir" "$net" "$sc" "$label"
  local e="$EXP/$tag"; mkdir -p "$e"
  for f in SOLVE_RECEIPT.json V5_GATES.json INTERIOR_CHECKS.json BUNKER_ACCOUNT.json GUROBI_LOG_SCRUBBED.txt RESOURCE.jsonl CO2_FLOWS.json GAP_TABLE.json EMISSIONS_BY_COUNTRY.json CAPACITY_BY_TECH_COUNTRY.json cross_border_flows.csv COUNTRY_COST_LEDGER.csv COUNTRY_COST_LEDGER_DETAIL.csv LEDGER_IDENTITY.json NODAL_PRICES.csv DUALS_BY_CONSTRAINT.nc DUALS_INDEX.csv COMPONENT_COST_BREAKDOWN.csv COMPONENT_COST_BREAKDOWN_SUMMARY.json costs_active_research.csv PRECISION.json PRECISION.md VIOLATIONS.json C1_ERR_TAIL.txt EXPORTS.json; do [ -f "$dir/$f" ] && cp "$dir/$f" "$e/"; done
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
lane_integrated() {   # S4O stop rule: integrated non-optimal AND C1 (a)(b)(c) not passed -> STOP (no further run starts; no retry)
  want integrated || return 0
  local c; c=$(solve integrated | tail -1)
  if [ "$c" != "optimal" ] && [ "$c" != "dry" ] && ! c1_abc integrated; then
    echo "STOP_INTEGRATED_NONOPTIMAL_C1_FAILED:$c:$(c1_summary "$RUN/integrated/PRECISION.json" 2>/dev/null):$(date -u +%Y-%m-%dT%H:%M:%SZ) - no further run started (S4O stop condition)" >> "$ST"
    touch "$RUN/STOP"
  fi
  return 0
}
lane_nze() { want integrated_nze && solve integrated_nze > /dev/null; }
lane_disconnected() {   # the diagnostic runs only when the disconnected main ends non-optimal (or when named explicitly)
  local c="skipped"
  want disconnected && c=$(solve disconnected | tail -1)
  if want disconnected_gap; then licence_gap "before disconnected_gap in the lane"; solve disconnected_gap > /dev/null
  elif [ "$c" != "optimal" ] && [ "$c" != "skipped" ] && [ "$c" != "dry" ]; then echo "DISCONNECTED_MAIN_NON_OPTIMAL:$c -> running disconnected_gap diagnostic" >> "$ST"; licence_gap "before disconnected_gap in the lane"; solve disconnected_gap > /dev/null
  elif [ "$c" = "dry" ]; then echo "DRY-RUN: disconnected_gap would run only if the disconnected main ends non-optimal" >> "$ST"; fi
}
case "$MODE" in
  serial) lane_integrated; lane_disconnected; batch_regrade; lane_nze;;
  lanes2) licence_gap "start (token of the preflight licence check)"
          ( lane_integrated; want integrated && want integrated_nze && licence_gap "before integrated_nze in the lane"; lane_nze ) & p1=$!; lane_disconnected & p2=$!; wait $p1 $p2;;
esac
batch_regrade   # S4O: lanes2, or runs started without the disconnected main; no-op when already done or not possible
if [ $DRY = 1 ]; then echo "DRY-RUN done (no solve, no export)" >> "$ST"; cat "$ST"; exit 0; fi
if grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" "$EXP" >/dev/null 2>&1; then
  echo "LICENCE STRING FOUND IN EXPORT - not packed" >> "$ST"; exit 1
fi
cp "$ST" "$EXP/"
( cd "$RUN" && tar czf "results_$(basename "$RUN").tar.gz" export && sha256sum "results_$(basename "$RUN").tar.gz" > "results_$(basename "$RUN").tar.gz.sha256" )
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ) export:$RUN/results_$(basename "$RUN").tar.gz" >> "$ST"
cat "$ST"
