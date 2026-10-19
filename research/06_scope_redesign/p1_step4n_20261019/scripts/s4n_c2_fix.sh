#!/bin/bash
# S4N-2 point 2 (user 2026-10-19 ~14:50): re-send ONE failed file with rsync --checksum (single stream), then the full SHA256SUMS check is run again
# separately. Host and port from the calling command line environment only.
set -u
source /home/jin/s4n_ssh.sh
F=${1:?relative path inside the package}
SRC=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4m_20261019/cloud_package_dist/$F
echo "LOCAL: $(stat -c %s $SRC) bytes $(sha256sum $SRC | cut -c1-16)"
t0=$(date +%s)
s4n_rsync -a --checksum --stats "$SRC" "root@$S4N_HOST:/root/autodl-tmp/s4m_cloud/$F" 2>&1 | grep -E "Number of files|Total file size|Total transferred file size|Literal data|Matched data|rsync error"
echo "RESEND_SECONDS:$(( $(date +%s) - t0 ))"
