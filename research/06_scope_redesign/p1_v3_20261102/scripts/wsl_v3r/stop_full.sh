#!/bin/bash
# V3 supplement 07 rerun (user instruction 2026-11-04): stop the full-pack download, keep the partial file (rsync --partial keeps it under its name), record its bytes.
# Only the rsync of this full pack is signalled (TERM); the light pack and its SHA256 file are separate files and not touched.
F=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/cloud_results/final_20261103T160537Z/results_full_final_20261103T160537Z.tar.gz
echo "before: $(stat -c %s "$F" 2>/dev/null) B at $(TZ=Asia/Singapore date '+%F %T') SGT; rsync processes: $(pgrep -fc 'rsync.*results_full_final_20261103T160537Z')"
pkill -TERM -f 'rsync.*results_full_final_20261103T160537Z'; sleep 5
echo "after:  $(stat -c %s "$F" 2>/dev/null) B at $(TZ=Asia/Singapore date '+%F %T') SGT; rsync processes left: $(pgrep -fc 'rsync.*results_full_final_20261103T160537Z')"
ls -la "$(dirname "$F")" | awk '{print $5, $9}'
echo "light pack sha256 still OK: $(cd "$(dirname "$F")" && sha256sum -c --quiet results_light_final_20261103T160537Z.tar.gz.sha256 && echo yes)"
