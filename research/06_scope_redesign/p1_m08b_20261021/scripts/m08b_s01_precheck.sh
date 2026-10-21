#!/bin/bash
# M08b supplement 01: read-only pre-smoke check (no solve): local Gurobi / solver processes and the time of the last local smoke run
echo "now: $(date -Is)"
echo "--- solver processes:"; ps -eo pid,etime,cmd | grep -E '[g]urobi|[s]2_solve|[g]rb' || echo none
S=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke
echo "--- last local smoke files (first round):"; ls -l --time-style=+%Y-%m-%dT%H:%M:%S%z $S 2>/dev/null | tail -5
free -g | head -2
