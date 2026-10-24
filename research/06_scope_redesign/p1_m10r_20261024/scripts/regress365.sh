#!/bin/bash
# M10R supplement (user authorisation 2026-10-24: ~40 min local compute, no Gurobi, no cloud): on the verified full results pack of the third batch,
# recompute for R1-R8 and R10 the country cost ledger, B16 and the M12 allocation from the solved 365x24h networks with the FIXED code
# (s4d_ledger_redo.py + m12_allocation.py run), into NEW folders on the WSL disk, and compare every output with the original cloud results of the
# light pack (B2 item 3 criterion: every number identical). The pack folder is read only (solved networks linked, small files copied).
#   bash regress365.sh            (env: RIDS to restrict)
set -u
WT=/home/jin/wt_m10p_20261022; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; export PYTHONHASHSEED=0
U=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10_20261022/cloud_results/20261023T174135Z_halted/full/unpacked/export
L=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10_20261022/cloud_results/20261023T174135Z_halted/light_unpacked/export
R=/home/jin/m10r_365; mkdir -p $R; ST=$R/STATUS.txt
RIDS=${RIDS:-"R1 R2 R3 R4 R5 R6 R7 R8 R10"}
cd $WT || exit 1
mkdir -p results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/$d results_project/$d; done
echo "START:$(date -u +%FT%TZ):head=$(git rev-parse HEAD):dirty=$(git status --porcelain --untracked-files=no scripts_project | wc -l):rids=$RIDS" >> $ST
log() { echo "$1:$(date -u +%FT%TZ)${2:+:$2}" >> $ST; }
jget() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split('.'): d=d.get(k) if isinstance(d, dict) else None
print('' if d is None else d)" "$1" "$2" 2>/dev/null; }
for rid in $RIDS; do
  S=$U/$rid; D=$R/$rid
  [ -e $D ] && { log "SKIP_$rid" exists; continue; }
  mkdir -p $D/v5; sc=$(jget $S/RUN.json scenario)
  for f in RUN.json SOLVE_RECEIPT.json PRECISION.json EXPORTS.json INTERIOR_CHECKS.json; do [ -f $S/$f ] && cp $S/$f $D/; done
  [ -f $S/kkt_summary.json ] && cp $S/kkt_summary.json $D/v5/
  for f in $S/*_solved.nc; do [ -f "$f" ] && ln -s "$f" $D/$(basename "$f"); done
  log "RUN_$rid" "scenario=$sc:nc=$(ls $S/*_solved.nc | head -1 | xargs -n1 basename)"
  t0=$(date +%s)
  ( env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" scripts_project/s4d_ledger_redo.py --solve-dir $S --into $D --repo . > $D/ledger_redo.log 2> $D/ledger_redo.err ); rc=$?
  log "LEDGER_$rid" "exit=$rc:$(( $(date +%s) - t0 ))s:peak=$(grep -h 'Maximum resident' $D/ledger_redo.err | awk '{printf "%.2fGiB", $NF/1048576}'):$(tail -1 $D/ledger_redo.log | cut -c1-220)"
  t1=$(date +%s)
  ( env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" scripts_project/m12_allocation.py run --repo . --solve-dir $D --scenario $sc --label REGRESS365_$rid --out $D --register > $D/m12.log 2> $D/m12.err ); rc=$?
  log "M12_$rid" "exit=$rc:$(( $(date +%s) - t1 ))s:peak=$(grep -h 'Maximum resident' $D/m12.err | awk '{printf "%.2fGiB", $NF/1048576}'):$(tail -1 $D/m12.log | cut -c1-200)"
  "$PY" /home/jin/m10r/compare_dirs.py $L/$rid $D $D/COMPARE_VS_LIGHT.json --label $rid > $D/compare.log 2>&1; log "COMPARE_$rid" "exit=$?:$(cut -c1-300 $D/compare.log)"
done
for d in assembly_v1 s1; do [ -L results_project/$d ] && rm results_project/$d; done
log DONE; cat $ST
