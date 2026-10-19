#!/bin/bash
# S4N-2 point 2: upload the verified S4M package (cloud_package_dist, COMMIT f50c8850; the local original, not the WSL copy with ./repo) to the data
# disk and check SHA256SUMS + COMMIT on the instance. Host and port from the calling command line environment only.
set -u
source /home/jin/s4n_ssh.sh
SRC=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4m_20261019/cloud_package_dist/
DST=/root/autodl-tmp/s4m_cloud
s4n_ssh "mkdir -p $DST && ls -A $DST | head -3" || exit 1
t0=$(date +%s)
s4n_rsync -a --partial --stats "$SRC" "root@$S4N_HOST:$DST/" 2>&1 | grep -E "Number of files|Total file size|Total transferred file size|rsync error"
echo "UPLOAD_SECONDS:$(( $(date +%s) - t0 ))"
s4n_ssh "cd $DST && echo SHA256SUMS_RESULT: \$(sha256sum -c SHA256SUMS 2>&1 | awk '{print \$NF}' | sort | uniq -c | tr '\n' ' '); echo COMMIT: \$(cat COMMIT); echo FILES: \$(find . -type f | wc -l); echo BYTES: \$(find . -type f -printf '%s\n' | awk '{s+=\$1} END {print s}')"
