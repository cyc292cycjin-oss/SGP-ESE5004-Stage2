#!/bin/bash
# V3.1 section 5.2 prerequisite: the DRILL package of the current commit (same builder as the delivered package; V31_DRILL=1, outside work/). No solver.
set -u
WT=/home/jin/wt_v3_fix; C8=$(git -C $WT rev-parse --short=8 HEAD); D=/home/jin/v3fix/drill_pkg_$C8
LOG=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105/evidence/PKG_DRILL_$C8.log
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py|[p]ytest ')" = 0 ] || { echo "REFUSED: a solve or pytest is running"; exit 4; }
cd $WT && V31_DRILL=1 PYTHONHASHSEED=0 /usr/bin/time -v bash research/06_scope_redesign/p1_v3_20261102/hpc_v31/make_hpc_package_v31.sh /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3 "$D" > "$LOG" 2>&1
echo "EXIT=$?" >> "$LOG"
grep -vE '^\s+(Command being|User time|System time|Percent|Average|Minor|Major|Voluntary|Involuntary|Swaps|File system|Socket|Signals|Page size|Exit status)' "$LOG" | tail -25
tail -2 "$D/HPC_CONSISTENCY.txt" 2>/dev/null
echo "DRILL_PKG=$D"
