#!/bin/bash
# status of a B4P solve folder: bash st.sh <tag>
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/b4p; D=$R/solves/${1:?tag}
date -u +%H:%M:%SZ; free -m | sed -n 2p
ps -eo pid,etime,rss,args | grep -E "[s]2_solve|[b]4_split" | cut -c1-110
echo "--- status"; grep -E "_${1}:" $R/SOLVES_STATUS.txt | cut -c1-400
echo "--- files"; ls $D 2>/dev/null | tr '\n' ' '; echo
for f in solve.err p1.err p2.err p3.err; do [ -f "$D/$f" ] && { echo "--- $f tail"; tail -c 500 "$D/$f" | grep -v "^$" | tail -8; }; done
for f in solve.log p1.log p2.log p3.log; do [ -f "$D/$f" ] && { echo "--- $f tail"; tail -c 400 "$D/$f"; echo; }; done
[ -f "$D/gurobi.linopy.log" ] && { echo "--- gurobi log tail"; tail -3 "$D/gurobi.linopy.log" | cut -c1-160; }
