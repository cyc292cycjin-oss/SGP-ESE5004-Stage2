#!/bin/bash
# S4N-4 point 4 (user 2026-10-19 ~16:25 SGT): delete the licence file on the instance after the light retrieval and verify. Refuses while any solve /
# analysis process runs. Other files are not touched. Host / port from the calling environment only.
set -u
source /home/jin/s4n_ssh.sh
s4n_ssh 'ps -eo cmd | grep -E "[s]2_solve|[l]23_violation|[s]4n_c1_precision|[s]4n_pilot_check|[r]un_365x24h|[s]peed_probe" && { echo "REFUSED: process still running"; exit 2; }
  echo "BEFORE: $(ls -la /root/.gurobi | grep -v total | awk "{print \$1, \$5, \$NF}" | tr "\n" ";")"
  shred -u /root/.gurobi/gurobi.lic && echo "SHRED_U_DONE:$(TZ=Asia/Singapore date "+%F %T") SGT"
  [ -e /root/.gurobi/gurobi.lic ] && echo "STILL PRESENT" || echo "VERIFIED_ABSENT: /root/.gurobi/gurobi.lic"
  echo "AFTER: dir entries $(ls -A /root/.gurobi | wc -l)"
  echo "OTHER_LIC_NAMES (outside the conda package files):"; find / -xdev \( -iname "gurobi.lic*" -o -iname "*.lic" \) -type f 2>/dev/null | grep -v "^/root/miniconda3/" ; find /root/autodl-tmp /tmp -iname "*.lic*" -type f 2>/dev/null; echo "(end)"'
