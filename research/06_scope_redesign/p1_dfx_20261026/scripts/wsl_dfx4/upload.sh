#!/bin/bash
# DFX phase 4: ONE rsync stream (no parallel streams; never interrupt --partial) of the whole v8 package to a NEW folder on the instance data disk.
# Usage: wsl env DFX_HOST=.. DFX_PORT=.. bash /home/jin/dfx4/upload.sh        (target /root/autodl-tmp/dfx_v8; refused if it exists)
set -u
source /home/jin/dfx4/ssh.sh
SRC=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/cloud_package_dfx/; DST=/root/autodl-tmp/dfx_v8; LOG=/home/jin/dfx4/upload.log
[ "$(cut -c1-8 ${SRC}COMMIT)" = 16b209e2 ] || { echo "local package is not the registered commit 16b209e2"; exit 2; }
( cd $SRC && sha256sum -c --quiet SHA256SUMS ) || { echo "LOCAL PACKAGE CHECKSUM MISMATCH"; exit 2; }
err=$(mktemp)
dfx_ssh "[ ! -e $DST ] && mkdir -p $DST && echo created" 2>"$err" | grep -q created || { dfx_scrub "REFUSED: $DST exists or ssh failed $(cat "$err")"; rm -f "$err"; exit 2; }
bytes=$(du -sb $SRC | cut -f1); echo "UPLOAD_START:$(date -u +%FT%TZ):bytes=$bytes" | tee -a "$LOG"; t0=$(date +%s)
rsync -a --no-owner --no-group --chmod=D755,F644 --partial --info=stats2 -e "ssh ${DFX_OPTS[*]} -p $DFX_PORT" "$SRC" "root@$DFX_HOST:$DST/" > "$LOG.out" 2> "$err"
rc=$?; t1=$(date +%s)
dfx_scrub "$(cat "$LOG.out")" >> "$LOG"; [ -s "$err" ] && dfx_scrub "STDERR: $(cat "$err")" | tee -a "$LOG"; rm -f "$err" "$LOG.out"
echo "UPLOAD_END:$(date -u +%FT%TZ):rsync_exit=$rc:seconds=$((t1-t0)):MBps=$(awk -v b=$bytes -v s=$((t1-t0)) 'BEGIN {printf "%.3f", b/1e6/(s>0?s:1)}')" | tee -a "$LOG"
