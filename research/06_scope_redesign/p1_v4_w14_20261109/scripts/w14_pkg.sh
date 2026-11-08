#!/bin/bash
# W14 section 3.1: the delivered package at the current commit (= package COMMIT) into work/p1_v4_w14_20261109/hpc_package_v4 (no drill switch). No solver.
set -u
WT=/home/jin/wt_v4_w14; D=${1:-/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w14_20261109/hpc_package_v4}
LOG=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w14_20261109/logs/pkg_$(basename "$D").txt
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py|[p]ytest ')" = 0 ] || { echo "REFUSED: a solve or pytest is running"; exit 4; }
cd $WT
echo "package commit $(git rev-parse HEAD); code differs from the build commit 59b128ea outside research/: $(git diff --name-only 59b128ea HEAD -- . ':!research/' | wc -l) file(s)" > "$LOG"
/usr/bin/time -v bash research/06_scope_redesign/p1_v4_w14_20261109/hpc_v4/make_hpc_package_v4.sh "$D" >> "$LOG" 2>&1
echo "EXIT=$?" >> "$LOG"
grep -vE '^\s+(Command being|User time|System time|Percent|Average|Minor|Major|Voluntary|Involuntary|Swaps|File system|Socket|Signals|Page size|Exit status)' "$LOG" | grep -v 'INFO:' | cut -c1-300
[ -f "$D/COMMIT" ] && { cat "$D/COMMIT"; sha256sum "$D/SHA256SUMS"; wc -l < "$D/SHA256SUMS"; find "$D" -type f | wc -l; du -sb "$D"; tail -1 "$D/HPC_CONSISTENCY.txt"; grep -c '^OK ' "$D/HPC_CONSISTENCY.txt"; }
