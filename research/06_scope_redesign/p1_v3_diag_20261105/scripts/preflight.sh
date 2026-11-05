#!/bin/bash
# V3 DIAG preflight: WSL outbound to the WLS token server, Gurobi processes, resources.
# Prints no licence content.
set -u
echo "== time $(date -Is)"
echo "== tcp token.gurobi.com:443"
if timeout 15 bash -c 'exec 3<>/dev/tcp/token.gurobi.com/443' 2>/dev/null; then
  echo "TCP_OK"
else
  echo "TCP_FAIL rc=$?"
fi
echo "== gurobi / solve processes (WSL)"
ps -eo pid,etime,rss,cmd | grep -Ei '[g]urobi|[s]2_solve|[g]rb' || echo "NONE"
echo "== memory"
free -g
echo "== cpu"
nproc
lscpu | grep -E 'Model name|^CPU\(s\)|Thread|Core|Socket' || true
echo "== disk"
df -h /home /mnt/d 2>/dev/null
