#!/bin/bash
# wait until the number of lines matching $1 across the run STATUS files and the driver status reaches $2, or $3 seconds pass
pat=$1; want=$2; lim=${3:-540}; t0=$(date +%s)
cnt() { cat /home/jin/s4q_local/DRIVER_STATUS.txt /home/jin/s4q_local/pkg/runs/*/STATUS.txt 2>/dev/null | grep -cE "$pat"; }
while [ "$(cnt)" -lt "$want" ] && [ $(( $(date +%s) - t0 )) -lt "$lim" ]; do sleep 10; done
echo "count=$(cnt) waited=$(( $(date +%s) - t0 ))s"; bash /home/jin/s4q_watch.sh
