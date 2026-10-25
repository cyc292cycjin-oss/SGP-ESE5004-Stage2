#!/bin/bash
# B4P A3.1 regression (instruction A3.1 "回归"): the post-processing chain of every third-batch network type re-run with the B4P code on the
# existing 56x3h results (M10R drill_postproc.sh: M08b smoke integrated / disconnected, M12b minus VN / TH / LA, M10R keep-stock / wacc disconnected /
# b1 disconnected real; wacc integrated synthetic) -> results_project/b4p/regress/drill9, compared file by file with the M10R post-fix drill outputs
# (results_project/m10r/drill/<type>) using the M10R comparator. No solver call. Must not run beside a real local solve (synthetic types build an LP
# with s2_solve.py --stop-before-solve, which the solve runner's busy() would count).
set -u
WT=/home/jin/wt_b4p_20261026; RES=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; OUT=$RES/b4p/regress/drill9; E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_b4p_20261026/evidence/regress
mkdir -p "$E"
n=$(ps -eo args= | grep -cE "[s]2_solve\.py|[b]4_split_solve\.py"); [ "$n" = 0 ] || { echo "solve process running ($n) - not started"; exit 3; }
t0=$(date +%s)
WT=$WT PY=$PY RES=$RES bash "$WT/research/06_scope_redesign/p1_m10r_20261024/scripts/drill_postproc.sh" "$OUT" > "$E/drill9.log" 2>&1; echo "DRILL_EXIT $? $(( $(date +%s) - t0 ))s" >> "$E/drill9.log"
cp "$OUT/DRILL_POSTPROC.json" "$E/DRILL_POSTPROC_b4p.json" 2>/dev/null
all=1
for t in integrated disconnected minusVN minusTH minusLA keepstock wacc_disconnected b1_disconnected wacc_integrated; do
  if [ -d "$RES/m10r/drill/$t" ] && [ -d "$OUT/$t" ]; then
    env -u GRB_LICENSE_FILE "$PY" /home/jin/m10r/compare_dirs.py "$RES/m10r/drill/$t" "$OUT/$t" "$E/REGRESS_$t.json" --label "$t" || all=0
  else echo "{\"label\": \"$t\", \"missing\": true}"; all=0; fi
done
echo "ALL_EQUAL=$all $(( $(date +%s) - t0 ))s" | tee -a "$E/drill9.log"
