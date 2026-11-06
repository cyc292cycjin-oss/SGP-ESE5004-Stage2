#!/bin/bash
# W08: wait until the smoke runner has written DONE (or 2.5 h passed); prints the status file.
S=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/smoke56/STATUS.txt
for i in $(seq 1 150); do
  grep -q '^DONE' $S 2>/dev/null && break
  sleep 60
done
cat $S
