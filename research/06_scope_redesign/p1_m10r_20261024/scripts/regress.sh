#!/bin/bash
# M10R B2.3 regression driver (no solve; GRB_LICENSE_FILE removed): for ONE solved 56x3h run, redo the whole ledger-dependent post-processing chain
# into a NEW folder with the code of the current worktree state (pre-fix or post-fix): ledger redo (s4d_ledger_redo.py) -> C1 run (with the batch
# reference) -> M12 allocation -> Owen dual-form audit -> GATES_V6 accept -> stop-class. The source run folder is read only (small files copied,
# the solved network / duals / LP and solution arrays linked).
#   bash regress.sh <src run dir> <unsolved network nc> <scenario> <registered sha256> <reference json> <out dir> <tag>
set -u
SRC=$1; NET=$2; SC=$3; REG=$4; REF=$5; OUT=$6; TAG=$7
WT=/home/jin/wt_m10p_20261022; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; export PYTHONHASHSEED=0; N=56
cd $WT || exit 1
mkdir -p results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/$d results_project/$d; done
[ -e "$OUT" ] && { echo "exists $OUT"; exit 2; }
mkdir -p "$OUT/v5"; ST=$OUT/REGRESS_STATUS.txt
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
for f in SOLVE_RECEIPT.json INTERIOR_CHECKS.json BUNKER_ACCOUNT.json EXPORTS.json GUROBI_LOG_SCRUBBED.txt VIOLATIONS.json costs_active_research.csv \
         COMPONENT_COST_BREAKDOWN.csv COMPONENT_COST_BREAKDOWN_SUMMARY.json DUALS_INDEX.csv RUN.json; do [ -f "$SRC/$f" ] && cp "$SRC/$f" "$OUT/"; done
[ -f "$SRC/v5/kkt_summary.json" ] && cp "$SRC/v5/kkt_summary.json" "$OUT/v5/"
for f in "$SRC"/*_solved.nc "$SRC"/DUALS_BY_CONSTRAINT.nc; do [ -f "$f" ] && ln -s "$f" "$OUT/$(basename "$f")"; done
for d in lp solution; do [ -d "$SRC/$d" ] && ln -s "$SRC/$d" "$OUT/$d"; done
log START "tag=$TAG:src=$SRC:head=$(git rev-parse --short HEAD):dirty=$(git status --porcelain --untracked-files=no scripts_project | wc -l)"
( env -u GRB_LICENSE_FILE "$PY" scripts_project/s4d_ledger_redo.py --solve-dir "$SRC" --into "$OUT" --repo . > "$OUT/ledger_redo.log" 2> "$OUT/ledger_redo.err" ); log LEDGER "exit=$?:$(tail -1 "$OUT/ledger_redo.log" | cut -c1-200)"
[ -f "$OUT/V5_GATES.json" ] || cp "$SRC/V5_GATES.json" "$OUT/V5_GATES.json" 2>/dev/null   # ledger failed (pre-fix on the defect): keep the original gates for the rest of the chain
( env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py run --repo . --solve-dir "$OUT" --network "$NET" --scenario $SC --label SMOKE_TEST_ONLY \
    --violations "$OUT/VIOLATIONS.json" --reference "$REF" --truncate $N > "$OUT/c1_precision.log" 2> "$OUT/c1_precision.err" ); log C1 "exit=$?:$(tail -1 "$OUT/c1_precision.log" | cut -c1-200)"
( env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_allocation.py run --repo . --solve-dir "$OUT" --scenario $SC --label REGRESS_$TAG --out "$OUT" --register > "$OUT/m12.log" 2> "$OUT/m12.err" ); log M12 "exit=$?:$(tail -1 "$OUT/m12.err" | cut -c1-160)"
if [ -f "$OUT/ALLOCATION.json" ] && [ -e "$OUT/solution/X.npy" ]; then
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_rhs_audit.py audit --repo . --network "$NET" --scenario $SC --truncate $N --solve-dir "$OUT" \
      --allocation "$OUT/ALLOCATION.json" --tag REGRESS_$TAG --out "$OUT/m12_owen" --register-dir "$OUT" > "$OUT/m12_owen.log" 2> "$OUT/m12_owen.err" ); log M12_OWEN "exit=$?:$(tail -1 "$OUT/m12_owen.err" | cut -c1-160)"
else
  log M12_OWEN "skipped (no ALLOCATION.json or no solution arrays)"
fi
lab=$(env -u GRB_LICENSE_FILE "$PY" scripts_project/v5/gates_v6.py accept --solve-dir "$OUT" --registered-sha256 "$REG" --repo . --out "$OUT/V6_ACCEPTANCE.json" 2> "$OUT/v6.err" | tail -1)
log V6 "$lab"
cls=$(env -u GRB_LICENSE_FILE "$PY" scripts_project/m10_batch3_summary.py stop-class --dir "$OUT" 2> "$OUT/stop_class.err" | tail -1); log STOP_CLASS "$cls"
log DONE
cat $ST
