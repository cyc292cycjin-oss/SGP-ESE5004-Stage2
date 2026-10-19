#!/bin/bash
# S4N-2 point 2, parallel stream: networks/ of the same verified package (the main rsync of s4n_c2.sh skips files already complete; SHA256SUMS is
# checked on the instance afterwards). Host and port from the calling command line environment only.
set -u
source /home/jin/s4n_ssh.sh
SRC=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4m_20261019/cloud_package_dist/networks/
t0=$(date +%s)
s4n_rsync -a --partial --stats "$SRC" "root@$S4N_HOST:/root/autodl-tmp/s4m_cloud/networks/" 2>&1 | grep -E "Number of files|Total transferred file size|rsync error"
echo "UPLOAD_NETWORKS_SECONDS:$(( $(date +%s) - t0 ))"
