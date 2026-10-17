#!/bin/bash
# S4H cloud package: 365x24h day-resolution runs with the S4H main configuration - the S4C main (WEO 2025 STEPS fuel prices, decision-50 cost
# layer for the electric-base candidates incl. offshore connection cost and corridor subsea shares, hydro inflow national_observed, bunkers
# asean_pool with the separate net-zero bunker account, extra-ASEAN CO2 storage on, Kirchhoff row normalisation; scaling on) plus S4D:
# CO2 export only from coastal nodes and Lao rail transit (decision 93), intra-ASEAN CO2 shipping as maritime trade in both scenarios
# (decision 92), country cost ledger with the identity gate B16_LEDGER and nodal prices exported with every run (decision 91a); S4E: adjacent
# cross-border corridor candidates incl. BN, PH, TL and the APG domestic links (decision 94), one CO2 storage cost basis (extra-ASEAN 54.70
# EUR2020/t), pair-specific shipping distances and Lao transit then shipping (decision 95); S4F: PyPSA-Eur individual line / DC-link
# extension limit (lines.max_extension 20000 MW above the existing capacity, decision 96), TH-MY stock aligned to APG 380 MW, APG #4 at
# Pekanbaru, Lao CO2 into the Vietnamese national store by rail (decision 97); S4G: line-type electrical parameters (num_parallel, x, r, b)
# of the 19 cross-border AC lines readjusted by the author (decision 98); S4H: LA-VN grid stock 0 with lines 59 / 60 / 63 / 64 as
# zero-capacity candidates (decision 100), one-circuit reference reactance of every zero-capacity AC candidate, APG17 by the line-type
# relation, a reference candidate for every country pair with AC stock (decision 101). Replaces the void S4G package (code ed6af79c).
# PREPARED ONLY - run on the cloud instance after the user has authorised the run (CLAUDE.md: every optimisation needs a separate explicit
# authorisation).
#
#   GRB_LICENSE_FILE=/path/to/gurobi.lic bash run_365x24h.sh --solver-profile formal_barrier --mode serial|lanes2|lanes3 [--runs ...] [--auth "text"] [--dry-run]
#
# --solver-profile is REQUIRED and has no default; the cloud profile confirmed by the user (answer to S4C section 8 item 1) is A:
#   --solver-profile formal_barrier (with Kirchhoff row normalisation). Allowed values = research.solver.profiles in configs/research/baseline.yaml:
#   formal_barrier | crossover_diagnostic | barrier_numericfocus2. Without it the script refuses to start.
#
# Runs (default integrated,disconnected,integrated_nze):
#   integrated        integrated main, WEO 2025 STEPS fuel prices;
#   disconnected      disconnected main (STEPS, extra-ASEAN CO2 storage on) - expected feasible;
#   integrated_nze    integrated sensitivity with WEO 2025 NZE fuel prices (research.fuels.price_scenario = nze);
#   disconnected_gap  disconnected gap diagnostic (packaged; runs ONLY when the disconnected main ends non-optimal, or when named in --runs).
# Modes: serial = integrated -> disconnected (-> disconnected_gap) -> integrated_nze;
#        lanes2 = two lanes at the same time: [integrated -> integrated_nze] and [disconnected (-> disconnected_gap)];
#        lanes3 = three lanes at the same time: [integrated], [disconnected (-> disconnected_gap)], [integrated_nze].
#
# * one solve per run, no retry, no parameter change, no warm start (stop-loss of the project);
# * wall-clock cap 3 h per run (Gurobi TimeLimit 10,500 s, hard kill at 10,800 s);
# * every 60 s: RSS of the solve process tree, free memory, free disk and the last Gurobi progress line -> MONITOR_<run>.csv;
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
[ -n "$PROFILE" ] || { echo "REFUSED: --solver-profile is required (no default). User-confirmed cloud profile: --solver-profile formal_barrier (profile A)."; exit 2; }
case "$PROFILE" in formal_barrier|crossover_diagnostic|barrier_numericfocus2) ;; *) echo "REFUSED: unknown solver profile $PROFILE"; exit 2;; esac
case "$MODE" in serial|lanes2|lanes3) ;; *) echo "--mode serial|lanes2|lanes3"; exit 2;; esac
for r in ${RUNS//,/ }; do case "$r" in integrated|disconnected|integrated_nze|disconnected_gap) ;; *) echo "unknown run $r"; exit 2;; esac; done
want() { case ",$RUNS," in *",$1,"*) return 0;; *) return 1;; esac; }
: "${GRB_LICENSE_FILE:?set GRB_LICENSE_FILE to the licence path provided by the user}"
[ -r "$GRB_LICENSE_FILE" ] || { echo "GRB_LICENSE_FILE is not readable"; exit 2; }
[ -n "$AUTH" ] || AUTH="S4H cloud runs 365x24h (authorisation text to be supplied with --auth)"
REPO="$HERE/repo"                 # unpacked code snapshot (make_package.sh -> code_<commit>.tar.gz)
NETS="$HERE/networks"             # integrated_365_24h_unsolved.nc, disconnected_365_24h_unsolved.nc, integrated_nze_365_24h_unsolved.nc, disconnected_gap_diagnostic_365_24h_unsolved.nc
PY="${PY:-python}"                # python of the pypsa-earth environment (environment_pypsa-earth.yml)
RUN="$HERE/runs/$(date -u +%Y%m%dT%H%M%SZ)_$$"; EXP="$RUN/export"
mkdir -p "$(dirname "$RUN")" && mkdir "$RUN" && mkdir "$EXP" || { echo "run folder $RUN exists or cannot be created"; exit 2; }
ST="$RUN/STATUS.txt"
export PYTHONHASHSEED=0
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) mode:$MODE runs:$RUNS solver_profile:$PROFILE commit:$(cat "$HERE/COMMIT" 2>/dev/null)" >> "$ST"
SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic'   # licence-line filter (written so that the file itself holds no licence keyword)

net_of() { case "$1" in integrated) echo "$NETS/integrated_365_24h_unsolved.nc";; disconnected) echo "$NETS/disconnected_365_24h_unsolved.nc";;
                         integrated_nze) echo "$NETS/integrated_nze_365_24h_unsolved.nc";; disconnected_gap) echo "$NETS/disconnected_gap_diagnostic_365_24h_unsolved.nc";; esac; }
scen_of() { case "$1" in integrated|integrated_nze) echo integrated;; *) echo disconnected;; esac; }
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

solve() {   # $1 run tag; prints the termination condition as the last line
  local tag=$1 dir="$RUN/$1" net sc label; net=$(net_of "$1"); sc=$(scen_of "$1"); label=$(label_of "$1")
  mkdir -p "$dir"
  local cmd=("$PY" "$REPO/scripts_project/s2_solve.py" --repo "$REPO" --network "$net" --scenario "$sc" --output "$dir"
             --label "$label" --authorization "$AUTH; run $tag" --solver gurobi --solver-profile "$PROFILE" --scaling on --time-limit 10500)
  if [ $DRY = 1 ]; then echo "DRY-RUN: ${cmd[*]}" | tee -a "$ST" >/dev/null; echo dry; return 0; fi
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

lane_integrated() { want integrated && solve integrated > /dev/null; }
lane_nze() { want integrated_nze && solve integrated_nze > /dev/null; }
lane_disconnected() {   # the diagnostic runs only when the disconnected main ends non-optimal (or when named explicitly)
  local c="skipped"
  want disconnected && c=$(solve disconnected | tail -1)
  if want disconnected_gap; then solve disconnected_gap > /dev/null
  elif [ "$c" != "optimal" ] && [ "$c" != "skipped" ] && [ "$c" != "dry" ]; then echo "DISCONNECTED_MAIN_NON_OPTIMAL:$c -> running disconnected_gap diagnostic" >> "$ST"; solve disconnected_gap > /dev/null
  elif [ "$c" = "dry" ]; then echo "DRY-RUN: disconnected_gap would run only if the disconnected main ends non-optimal" >> "$ST"; fi
}
case "$MODE" in
  serial) lane_integrated; lane_disconnected; lane_nze;;
  lanes2) ( lane_integrated; lane_nze ) & p1=$!; lane_disconnected & p2=$!; wait $p1 $p2;;
  lanes3) lane_integrated & p1=$!; lane_disconnected & p2=$!; lane_nze & p3=$!; wait $p1 $p2 $p3;;
esac
if [ $DRY = 1 ]; then echo "DRY-RUN done (no solve, no export)" >> "$ST"; cat "$ST"; exit 0; fi
if grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" "$EXP" >/dev/null 2>&1; then
  echo "LICENCE STRING FOUND IN EXPORT - not packed" >> "$ST"; exit 1
fi
cp "$ST" "$EXP/"
( cd "$RUN" && tar czf "results_$(basename "$RUN").tar.gz" export && sha256sum "results_$(basename "$RUN").tar.gz" > "results_$(basename "$RUN").tar.gz.sha256" )
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ) export:$RUN/results_$(basename "$RUN").tar.gz" >> "$ST"
cat "$ST"
