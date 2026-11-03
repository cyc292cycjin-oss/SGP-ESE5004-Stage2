#!/bin/bash
# V3 screening: ONE rsync stream (no parallel streams; never interrupt --partial) of the whole screening package to a NEW folder on the data disk.
# Usage: wsl env V3S_HOST=.. V3S_PORT=.. bash /home/jin/v3s/upload.sh        (target /root/autodl-tmp/v3_screen; refused if it exists)
set -u
source /home/jin/v3s/ssh.sh
SRC=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_op/; DST=/root/autodl-tmp/v3_screen; LOG=/home/jin/v3s/upload.log
[ "$(cut -c1-8 ${SRC}COMMIT)" = 55253dd7 ] || { echo "local package is not the registered commit 55253dd7"; exit 2; }
( cd $SRC && sha256sum -c --quiet SHA256SUMS ) || { echo "LOCAL PACKAGE CHECKSUM MISMATCH"; exit 2; }
err=$(mktemp)
v3s_ssh "[ ! -e $DST ] && mkdir -p $DST && echo created" 2>"$err" | grep -q created || { v3s_scrub "REFUSED: $DST exists or ssh failed $(cat "$err")"; rm -f "$err"; exit 2; }
bytes=$(du -sb $SRC | cut -f1); echo "UPLOAD_START:$(date -u +%FT%TZ):bytes=$bytes" | tee -a "$LOG"; t0=$(date +%s)
rsync -a --no-owner --no-group --chmod=D755,F644 --partial --info=stats2 -e "ssh ${V3S_OPTS[*]} -p $V3S_PORT" "$SRC" "root@$V3S_HOST:$DST/" > "$LOG.out" 2> "$err"
rc=$?; t1=$(date +%s)
v3s_scrub "$(cat "$LOG.out")" >> "$LOG"; [ -s "$err" ] && v3s_scrub "STDERR: $(cat "$err")" | tee -a "$LOG"; rm -f "$err" "$LOG.out"
echo "UPLOAD_END:$(date -u +%FT%TZ):rsync_exit=$rc:seconds=$((t1-t0)):MBps=$(awk -v b=$bytes -v s=$((t1-t0)) 'BEGIN {printf "%.3f", b/1e6/(s>0?s:1)}')" | tee -a "$LOG"
