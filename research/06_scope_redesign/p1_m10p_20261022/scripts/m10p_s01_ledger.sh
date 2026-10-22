#!/bin/bash
# M10P supplement 01 S01-4: append the ledger entry (work-folder original M10P_S01_LEDGER_ENTRY.md) to research/STAGE2_PROJECT_LEDGER.md once
set -u
WT=/home/jin/wt_m10p_20261022; L=$WT/research/STAGE2_PROJECT_LEDGER.md; S=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022/M10P_S01_LEDGER_ENTRY.md
cd $WT || exit 1
[ "$(git branch --show-current)" = codex/m10-batch3-20261022 ] || { echo "WRONG BRANCH"; exit 2; }
grep -q '^### M10P 补充 01' $L && { echo "entry already in the ledger"; exit 0; }
printf '\n' >> $L && cat $S >> $L
echo "ledger lines $(wc -l < $L); last heading: $(grep '^### ' $L | tail -1 | cut -c1-80)"
