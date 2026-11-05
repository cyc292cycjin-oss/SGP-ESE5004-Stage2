#!/bin/bash
# V3.1 section 6.1: the delivered package (no drill switch) at the current commit into work/p1_v3_20261102/hpc_package_v3_1. No solver.
set -u
WT=/home/jin/wt_v3_fix; D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1
LOG=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105/evidence/PKG_FINAL.log
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py|[p]ytest ')" = 0 ] || { echo "REFUSED: a solve or pytest is running"; exit 4; }
cd $WT
echo "code differs from the regression commit 13ebce95 outside research/: $(git diff --name-only 13ebce95 HEAD -- . ':!research/' | wc -l) file(s)"
PYTHONHASHSEED=0 /usr/bin/time -v bash research/06_scope_redesign/p1_v3_20261102/hpc_v31/make_hpc_package_v31.sh /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3 "$D" > "$LOG" 2>&1
echo "EXIT=$?" >> "$LOG"
grep -E 'ZERO_SLACK|licence|manifest|EXIT|Elapsed|REFUSED|missing|differ' "$LOG" | cut -c1-220
tail -1 "$D/HPC_CONSISTENCY.txt"; grep -c '^OK ' "$D/HPC_CONSISTENCY.txt"
cat "$D/COMMIT"; sha256sum "$D/SHA256SUMS"; wc -l < "$D/SHA256SUMS"; find "$D" -type f | wc -l; du -sb "$D"
