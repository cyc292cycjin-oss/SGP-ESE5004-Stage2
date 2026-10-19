#!/bin/bash
# S4N-2 point 4: preflight (all sections) on the instance; output saved there and printed (the licence section suppresses Gurobi output; lines are
# filtered again). Holds one WLS token for >= 5 min afterwards. Host and port from the calling command line environment only.
set -u
source /home/jin/s4n_ssh.sh
s4n_ssh 'cd /root/autodl-tmp/s4m_cloud && echo "PREFLIGHT_START:$(date "+%F %T")" > /root/autodl-tmp/s4n_preflight.log && PY=/root/miniconda3/envs/pypsa-earth/bin/python GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash preflight.sh serial formal_barrier 2>&1 | grep -viE "licen[cs]e[i]d|registered[[:space:]]+to|wls(access|secret)|academic|PROJ" >> /root/autodl-tmp/s4n_preflight.log; echo "PREFLIGHT_END:$(date "+%F %T")" >> /root/autodl-tmp/s4n_preflight.log; cat /root/autodl-tmp/s4n_preflight.log'
