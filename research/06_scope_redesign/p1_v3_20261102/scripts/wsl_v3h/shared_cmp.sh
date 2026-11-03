#!/bin/bash
# the three shared files (RUN_PLAN_V3.md, V3_RULES.md, batch_def/BATCH_DEF_2920x3h.json): work/ copy vs the base 5e372e5d, the V27 branch head and this branch (read only)
W=/home/jin/wt_v3_hpc; D=research/06_scope_redesign/p1_v3_20261102; WK=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102
cd $W || exit 2
V27=$(git rev-parse --verify -q codex/v3-20261102 || echo none); echo "V27 branch head: $V27 ; this branch: $(git rev-parse HEAD)"
for f in RUN_PLAN_V3.md V3_RULES.md batch_def/BATCH_DEF_2920x3h.json; do
  w=$(sha256sum "$WK/$f" 2>/dev/null | cut -c1-12); b=$(git show "5e372e5d:$D/$f" 2>/dev/null | sha256sum | cut -c1-12)
  v=$( [ "$V27" != none ] && git show "$V27:$D/$f" 2>/dev/null | sha256sum | cut -c1-12 ); h=$(sha256sum "$D/$f" | cut -c1-12)
  echo "$f work=$w base=$b v27_head=${v:-none} this_branch_worktree=$h"
done
[ "$V27" != none ] && git log --oneline 5e372e5d..$V27 -- $D/RUN_PLAN_V3.md $D/V3_RULES.md $D/batch_def/BATCH_DEF_2920x3h.json | head
