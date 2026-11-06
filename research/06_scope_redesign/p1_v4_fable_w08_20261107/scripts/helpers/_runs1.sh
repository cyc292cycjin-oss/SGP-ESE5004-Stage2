#!/bin/bash
# Fable W08 review: A2 fallback reproduction, S7 checkpoints (ras, iid), out_ras / out_iid regeneration. Read-only on the repository.
set -u
T=/home/jin/v4fable; WT=/home/jin/wt_v4_fable; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
LOG=$T/runs1.log; : > $LOG
log() { echo "[$(date -u +%H:%M:%S)] $*" >> $LOG; }
# ---------- A2: scripts without options in a separate copy ----------
log "A2 start"
rm -rf $T/a2; mkdir -p $T/a2
rsync -a --exclude __pycache__ $T/repo/research_inputs $T/repo/scripts_project $T/a2/
( cd $T/a2 && find research_inputs -type f -exec sha256sum {} + | sort -k2 > $T/a2_before.sha )
( cd $T/a2/scripts_project && $PY m08b_demand.py > $T/a2_m08b.out 2>&1; echo "m08b exit $?" >> $LOG; $PY s3_0_industry.py > $T/a2_s30.out 2>&1; echo "s3_0 exit $?" >> $LOG )
( cd $T/a2 && find research_inputs -type f -exec sha256sum {} + | sort -k2 > $T/a2_after.sha )
diff $T/a2_before.sha $T/a2_after.sha > $T/a2_diff.txt; log "A2 sha diff lines: $(wc -l < $T/a2_diff.txt)"
# files touched (mtime newer than before marker) and comparison with v3.1 commit d3b9a3bc and with the worktree head
( cd $T/a2 && find research_inputs -type f -newer $T/a2_before.sha | sort ) > $T/a2_touched.txt
log "A2 touched files: $(wc -l < $T/a2_touched.txt)"
: > $T/a2_compare.txt
while read f; do
  h_new=$(sha256sum $T/a2/$f | cut -c1-64)
  h_v31=$(git -C $WT show d3b9a3bc:$f 2>/dev/null | sha256sum | cut -c1-64)
  h_head=$(git -C $WT show HEAD:$f 2>/dev/null | sha256sum | cut -c1-64)
  st_v31=DIFF; [ "$h_new" = "$h_v31" ] && st_v31=SAME
  st_head=DIFF; [ "$h_new" = "$h_head" ] && st_head=SAME
  echo "$f v31:$st_v31 head:$st_head $h_new" >> $T/a2_compare.txt
done < $T/a2_touched.txt
log "A2 done"
# ---------- S7 checkpoints ----------
cd $T/repo || exit 1
for m in ras iid; do
  log "checkpoints $m start"
  /usr/bin/time -f "%e s %M KB" $PY scripts_project/v4_industry.py --checkpoints $T/cp_$m --steps S7 --work $T/work_cp_$m --anchor-mode $m > $T/cp_$m.out 2> $T/cp_$m.err
  log "checkpoints $m exit $? $(tail -1 $T/cp_$m.err)"
done
# ---------- out tables regeneration ----------
for m in ras iid; do
  log "out_$m start"
  /usr/bin/time -f "%e s %M KB" $PY scripts_project/v4_industry.py --anchor-mode $m --work $T/work_out_$m > $T/out_$m.out 2> $T/out_$m.err
  log "out_$m exit $? $(tail -1 $T/out_$m.err)"
  for f in $T/repo/research_inputs/industry_v4/out_$m/*; do
    b=$(basename $f); h1=$(sha256sum $f | cut -c1-64); h2=$(sha256sum $WT/research_inputs/industry_v4/out_$m/$b 2>/dev/null | cut -c1-64)
    [ "$h1" = "$h2" ] && echo "out_$m/$b SAME" >> $T/out_compare.txt || echo "out_$m/$b DIFF" >> $T/out_compare.txt
  done
done
log "ALL DONE"
