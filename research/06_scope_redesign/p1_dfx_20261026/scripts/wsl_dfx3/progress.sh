#!/bin/bash
# DFX v3: progress of the full test suite (read-only)
f=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/tests/full.log
[ -f "$f" ] && { echo "bytes=$(wc -c < "$f") dots=$(tr -cd '.' < "$f" | wc -c) F=$(tr -cd 'F' < "$f" | wc -c) s=$(tr -cd 's' < "$f" | wc -c)"; tail -c 300 "$f"; echo; } || echo "no log yet"
echo "pytest processes: $(ps -eo etimes=,args= | grep -c '[p]ytest')"; ps -eo etimes=,args= | grep '[p]ytest' | head -1 | cut -c1-100
