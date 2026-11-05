#!/bin/bash
# V3 DIAG common settings (sourced). No licence content is read or printed: only its path is passed to the Gurobi process.
REPO=/home/jin/wt_v3_diag
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
WORK=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_diag_20261105
S=$WORK/scripts
EV=$WORK/evidence
PKG=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3
NETS=$PKG/networks
RUNROOT=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3diag
LICPATH=/home/jin/gurobi.lic
CALLS=$EV/GUROBI_CALLS.csv
STATUS=$EV/DIAG_STATUS.txt
MAXCALLS=40
TL=864000                      # registered TimeLimit (pbs/HPC_PLAN.txt LIMITS; run_batch4.sh R_TL from b4_batch4.py hpc-plan)
PROFILE=formal_barrier_1e6_t16
SCRUB='licen[cs]e|registered[[:space:]]+to|wls|academic|secret|accessid|token'
export PYTHONHASHSEED=0
mkdir -p "$RUNROOT/tmp" "$EV"
export TMPDIR=$RUNROOT/tmp
[ -f "$CALLS" ] || echo "call,id,kind,start_utc,end_utc,exit,status,presolve_s,runtime_s,maxmem_gb,peak_rss_gib,extra" > "$CALLS"
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "$*" >> "$STATUS"; echo "$*"; }
net_of() { case "$1" in F1) echo "$NETS/integrated_2920_3h_unsolved.nc";; F2) echo "$NETS/no_new_xb_2920_3h_unsolved.nc";; F3) echo "$NETS/integrated_ev05_2920_3h_unsolved.nc";; F4) echo "$NETS/no_new_xb_ev05_2920_3h_unsolved.nc";; *) return 1;; esac; }
scen_of() { case "$1" in F1|F3) echo integrated;; F2|F4) echo no_new_xb;; *) return 1;; esac; }
costs_of() { echo "$NETS/integrated_costs_active_research.csv"; }   # the only costs table of the package (post-solve export only; not read by the build)
calls_used() { tail -n +2 "$CALLS" | grep -c .; }
gurobi_running() { ps -eo args= | grep -E '[b]4_split_solve\.py|[d]iag_build\.py --mode iis|[g]urobi_cl|[s]2_solve\.py' | grep -vcE '^(/usr/bin/)?time |^env '; }
token_ok() { timeout 15 bash -c 'exec 3<>/dev/tcp/token.gurobi.com/443' 2>/dev/null; }
peak_gib() { grep -h 'Maximum resident' "$1" 2>/dev/null | awk '{printf "%.2f", $NF/1048576}'; }
