#!/bin/bash
# S4N-2 point 2, re-balance: stop the main rsync (its top-level files are complete; in networks/ it duplicated the parallel stream) and upload the
# integrated_nze_* and integrated_56_* network files as a third stream, so the two live streams work on disjoint files. A final full rsync and
# SHA256SUMS on the instance follow separately. Host and port from the calling command line environment only.
set -u
echo "RSYNC_BEFORE:"; pgrep -af "rsync -e" | grep -v pgrep | sed -E "s/root@[^:]+:/root@HOST:/; s/-p [0-9]+/-p PORT/" | cut -c1-200
pkill -f "cloud_package_dist/ root@" && echo "MAIN_RSYNC_STOPPED" || echo "MAIN_RSYNC_NOT_FOUND"
sleep 2
source /home/jin/s4n_ssh.sh
SRC=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4m_20261019/cloud_package_dist/networks/
t0=$(date +%s)
s4n_rsync -a --partial --stats --include="integrated_nze_*" --include="integrated_56_*" --exclude="*" "$SRC" "root@$S4N_HOST:/root/autodl-tmp/s4m_cloud/networks/" 2>&1 | grep -E "Number of files|Total transferred file size|rsync error"
echo "UPLOAD_STREAM3_SECONDS:$(( $(date +%s) - t0 ))"
