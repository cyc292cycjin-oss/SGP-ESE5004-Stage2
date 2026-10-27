#!/bin/bash
# HPR: wait until the H4 drill's first in-job preflight has been recorded (or the drill ended), then print the early records.
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/hpr/h4
until grep -q "PREFLIGHT:" $R/runs/smoke56/PBS_JOBS.txt 2>/dev/null || grep -q "DONE:" $R/H4_DRILL_STATUS.txt 2>/dev/null; do sleep 10; done
cat $R/H4_DRILL_STATUS.txt; echo "--- PBS_JOBS ---"; cut -c1-400 $R/runs/smoke56/PBS_JOBS.txt 2>/dev/null
echo "--- STATUS ---"; cut -c1-300 $R/runs/smoke56/STATUS.txt 2>/dev/null | tail -5
echo "--- preflight tail ---"; tail -4 $R/runs/smoke56/preflight_smoke56_F1_*.txt 2>/dev/null
