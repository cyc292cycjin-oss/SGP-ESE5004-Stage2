#!/bin/bash
# M10P-4 (before RUN_PLAN.md): one 365x24h integrated LP build with s2_solve.py --stop-before-solve (no solver call; GRB_LICENSE_FILE points to a
# non-existent file as a tripwire) on the registered network of builds_s01, to size the run folders (LP arrays) and the build memory for the
# disk / memory requirement of RUN_PLAN.md section 5. Output: main checkout results_project/m10p/measure_r1 (not committed).
set -u
WT=/home/jin/wt_m10p_20261022; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; B=$MAIN/results_project/m08b/builds_s01
O=$MAIN/results_project/m10p/measure_r1; E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022/evidence
[ -e $O ] && { echo "exists $O"; exit 2; }
mkdir -p $O; cd $WT || exit 1
[ "$(ps -eo cmd | grep -cE '[s]2_solve.py')" = 0 ] || { echo "solver process running"; exit 3; }
echo "START $(date -u +%FT%TZ) commit $(git rev-parse HEAD) dirty $(git status --porcelain --untracked-files=no | wc -l)" > $O/STATUS.txt
env PYTHONHASHSEED=0 GRB_LICENSE_FILE=/nonexistent/m10p_measure_no_licence /usr/bin/time -v $PY scripts_project/s2_solve.py --repo . --network $B/integrated/integrated_365_24h_unsolved.nc \
  --scenario integrated --output $O/R1 --label BATCH3_365X24H --authorization "M10P-4 measurement, stop before solve (no solver call)" --solver gurobi \
  --solver-profile formal_barrier --scaling on --time-limit 21600 --costs-table $B/integrated/costs_active_research.csv --stop-before-solve > $O/R1.log 2> $O/R1.err
echo "EXIT $? $(date -u +%FT%TZ)" >> $O/STATUS.txt
grep -E "Maximum resident|Elapsed \(wall" $O/R1.err >> $O/STATUS.txt
du -sb $O/R1/lp $O/R1 >> $O/STATUS.txt
ls $O/R1 >> $O/STATUS.txt
tail -1 $O/R1.log | cut -c1-600 >> $O/STATUS.txt
cp $O/STATUS.txt $E/M10P_MEASURE_R1_STATUS.txt
cat $O/STATUS.txt
