#!/bin/bash
# S4N supplement 01 B1.2 (authorised in the supplement; user 2026-10-19): ONE local solve of the PACKAGED probe network
# (networks/integrated_56_3h_probe_unsolved.nc) with profile A through the packaged speed_probe.sh (30 min stop-loss inside, no retry), in the WSL
# copy of the package (/home/jin/s4n_local/pkg; writes probe/<timestamp>/ there, the D: original stays untouched). PROBE_REFERENCE.json holds the
# S4M-2 objective of the 2920x3h network truncated to 56 snapshots, not a solve of the probe file itself -> this run records the probe network's own
# objective, iterations and work units. Must end >= 5 min before any cloud Gurobi session.
set -u
cd /home/jin/s4n_local/pkg
L=/home/jin/s4n_local/probe_local_console.log
pgrep -af "gurobi|s2_solve" | grep -v pgrep && { echo "REFUSED: another solver process is running" > $L; exit 2; }
echo "LOCAL_PROBE_START:$(date -u +%Y-%m-%dT%H:%M:%SZ)" > $L
AUTH="S4N supplement 01 B1.2 (user 2026-10-19): one local solve of the packaged probe network, profile A, stop-loss 30 min, no retry - local reference objective"
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python GRB_LICENSE_FILE=/home/jin/gurobi.lic bash speed_probe.sh --auth "$AUTH" >> $L 2>&1
echo "LOCAL_PROBE_EXIT:$? END:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $L
echo "DONE" >> $L
