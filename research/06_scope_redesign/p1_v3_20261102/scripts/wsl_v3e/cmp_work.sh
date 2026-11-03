#!/bin/bash
# V3 supplement 06: compare the work/ mirrors with the branch versions (read-only)
D=/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102; WORK=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102
for f in $(cd "$WORK" && ls V3_* RUN_PLAN*.md); do
  if [ -f "$D/$f" ]; then cmp -s "$D/$f" "$WORK/$f" && echo "same    $f" || echo "DIFFER  $f  branch $(stat -c %s "$D/$f") work $(stat -c %s "$WORK/$f")"; else echo "no-branch $f"; fi
done
echo "== in branch, not in work"; for f in $(cd "$D" && ls V3_* RUN_PLAN*.md); do [ -f "$WORK/$f" ] || echo "  $f"; done
echo "== DATA_INTAKE history"; cd /home/jin/wt_v3_20261102 && git log --oneline -- research/06_scope_redesign/p1_v3_20261102/V3_DATA_INTAKE.md | head
diff <(sed -n '1,400p' "$WORK/V3_DATA_INTAKE.md") <(sed -n '1,400p' "$D/V3_DATA_INTAKE.md") | head -60
