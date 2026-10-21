#!/bin/bash
# M08b section 4 precondition (read-only): Gurobi / solve processes on this machine and the latest local Gurobi log time; no licence content is read
echo "now: $(date -Is)"
echo "--- processes (gurobi / s2_solve / grb):"
ps -eo pid,etimes,cmd | grep -E '[g]urobi|[s]2_solve|[g]rbtune|[g]rb_ts' || echo "none"
echo "--- newest gurobi.log / solver logs under results_project (mtime):"
find /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project -maxdepth 6 -name '*gurobi*.log' -printf '%TY-%Tm-%Td %TH:%TM %p\n' 2>/dev/null | sort | tail -3
