#!/bin/bash
# S4O-6 point 2 (empty data disk on the clone -> the WHOLE S4O package, not only the PACKAGE_DELTA.json files): ONE rsync stream for the package, then
# ONE rsync stream for the three pilot files of the local light package (authorisation point 3: new instance -> upload from the light package);
# never interrupted, never parallel; afterwards the full sha256sum -c SHA256SUMS on the instance, COMMIT and the pilot file hashes.
# Host and port from the calling command line environment only.
set -u
source /home/jin/s4o_ssh.sh
SRC=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019/cloud_package_dist/
DST=/root/autodl-tmp/s4o_cloud
PL=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019/cloud_results/20261019T072454Z_5125/unpacked/s4n_pilot_light_20261019T072454Z_5125
PD=/root/autodl-tmp/s4n_pilot
s4o_ssh "mkdir -p $DST $PD/integrated && ls -A $DST | head -3" || exit 1
t0=$(date +%s)
s4o_rsync -a --partial --stats "$SRC" "root@$S4O_HOST:$DST/" 2>&1 | grep -E "Number of files|Total file size|Total transferred file size|rsync error"
echo "UPLOAD_PACKAGE_SECONDS:$(( $(date +%s) - t0 ))"
t1=$(date +%s)
s4o_rsync -a --partial "$PL/export_integrated/COUNTRY_COST_LEDGER.csv" "$PL/export_integrated/SOLVE_RECEIPT.json" "root@$S4O_HOST:$PD/integrated/" && \
s4o_rsync -a --partial "$PL/PILOT_PRECISION.json" "root@$S4O_HOST:$PD/" && echo "UPLOAD_PILOT_SECONDS:$(( $(date +%s) - t1 ))"
s4o_ssh "cd $DST && echo SHA256SUMS_RESULT: \$(sha256sum -c SHA256SUMS 2>&1 | awk '{print \$NF}' | sort | uniq -c | tr '\n' ' '); echo COMMIT: \$(cat COMMIT); echo FILES: \$(find . -type f | wc -l); echo BYTES: \$(find . -type f -printf '%s\n' | awk '{s+=\$1} END {print s}'); ls -a | grep -c '^\.' ; find . -name '.*' -type f | head"
echo "PILOT_FILES local / remote sha256:"
for f in export_integrated/COUNTRY_COST_LEDGER.csv export_integrated/SOLVE_RECEIPT.json PILOT_PRECISION.json; do echo "local  $(sha256sum $PL/$f | cut -c1-16) $f"; done
s4o_ssh "cd $PD && sha256sum integrated/COUNTRY_COST_LEDGER.csv integrated/SOLVE_RECEIPT.json PILOT_PRECISION.json | cut -c1-16,65-"
