#!/bin/bash
# D2a section 2 (Fable F-02): the W08 reference runs (main, iid, i2chk) repeated with the patched reference engine (scripts/ref; d2a_ref_run.py) in fresh
# scratch folders copied from the W08 scratch (inputs only, no results): the corrected reference snapshots (overflow after the conservation layer).
# No solver, repository untouched (the engine reads the frozen I2 worktree /home/jin/wt_v4_i2 and the W07 deliveries).
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2a_20261107; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; T=/home/jin/v4d2a
mkdir -p $T
for n in main iid i2chk; do
  [ -d $T/ref_$n ] || { rsync -a --exclude results /home/jin/v4w08/ref_$n/ $T/ref_$n/; echo "scratch ref_$n copied"; }
done
cd $W || exit 1
run() { n=$1; shift; ( export W08_REF_SCRATCH=$T/ref_$n PYTHONHASHSEED=0 "$@"; $PY scripts/d2a_ref_run.py ${STEPS:-} > $T/ref_log_$n.txt 2>&1; echo "EXIT:$?" >> $T/ref_log_$n.txt ) & }
run main W08_ANCHOR_MODE=ras W08_ID_PAPER_FW=residue
run iid W08_ANCHOR_MODE=fixedcol W08_ID_PAPER_FW=residue
STEPS="--steps S1,S7" run i2chk W08_ANCHOR_MODE=fixedcol W08_ID_PAPER_FW=purchased
wait
for n in main iid i2chk; do echo "--- ref_$n"; tail -4 $T/ref_log_$n.txt; done
echo REF_DONE
