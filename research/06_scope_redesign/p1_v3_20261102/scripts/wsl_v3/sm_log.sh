#!/bin/bash
# barrier tails only; licence lines dropped
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
for f in $R/v3/smoke_r2/integrated $R/v3/smoke_r2/no_new_xb $R/dfx_v3/smoke_v2/integrated $R/dfx_v3/smoke_v2/disconnected; do
  echo "== ${f#$R/}"
  L=$f/GUROBI_LOG_SCRUBBED.txt; [ -f $L ] || L=$f/gurobi.linopy.log
  grep -nE "Set parameter (BarConvTol|Threads|Crossover|BarHomogeneous)|Barrier solved|Barrier performed|Sub-optimal|suboptimal|Numerical trouble|numerical|Solved in|Solved with|Optimal objective|Unable|Model fingerprint|Barrier statistics" $L | grep -vi "licen\|wls\|access" | cut -c1-110 | tail -9
  n=$(grep -nE "^ *[0-9]+ +[-+0-9.e]+ +[-+0-9.e]+ +[0-9.e+-]+ +[0-9.e+-]+ +[0-9.e+-]+ +[0-9.]+s" $L | tail -3 | cut -d: -f2- | cut -c1-90); echo "$n"
done
