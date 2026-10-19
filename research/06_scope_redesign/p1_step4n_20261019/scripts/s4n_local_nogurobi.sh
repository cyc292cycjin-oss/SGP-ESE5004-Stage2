#!/bin/bash
# local check: no Gurobi / solve process in WSL (the cloud instance must be the only Gurobi user while it runs)
P=$(pgrep -af "gurobi|s2_solve|speed_probe" | grep -v pgrep | grep -v s4n_local_nogurobi)
[ -z "$P" ] && echo "LOCAL_NO_GUROBI_PROCESS $(TZ=Asia/Singapore date '+%F %T') SGT" || { echo "LOCAL GUROBI PROCESS RUNNING:"; echo "$P" | cut -c1-150; }
