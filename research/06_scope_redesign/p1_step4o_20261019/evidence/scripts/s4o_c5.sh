#!/bin/bash
# S4O-6 point 4: preflight (all sections, serial, default profile = profile A) on the instance; output saved there and printed with licence-type lines
# filtered. The licence section holds one WLS token for >= 5 min afterwards. Host and port from the calling command line environment only.
set -u
source /home/jin/s4o_ssh.sh
s4o_ssh 'cd /root/autodl-tmp/s4o_cloud && echo "PREFLIGHT_START:$(date "+%F %T")" > /root/autodl-tmp/s4o_preflight.log && PY=/root/miniconda3/envs/pypsa-earth/bin/python GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash preflight.sh serial 2>&1 | grep -viE "licen[cs]e[i]d|registered[[:space:]]+to|wls(access|secret)|academic|PROJ" >> /root/autodl-tmp/s4o_preflight.log; echo "PREFLIGHT_END:$(date "+%F %T")" >> /root/autodl-tmp/s4o_preflight.log; cat /root/autodl-tmp/s4o_preflight.log'
date +%s > /home/jin/s4o_tmp/last_gurobi_env_end_epoch
