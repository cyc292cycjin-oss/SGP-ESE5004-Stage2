#!/bin/bash
# W08 section 1: three reference runs in parallel (separate scratch folders): main (ras + paper fuelwood residue), iid (fixedcol + residue),
# i2chk (fixedcol + purchased, S1 and S7 only = I2 main: checks the copy against the I2 results). No solver, repository untouched.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w08_20261106; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W || exit 1
run() { n=$1; shift; ( export W08_REF_SCRATCH=/home/jin/v4w08/ref_$n PYTHONHASHSEED=0 "$@"; $PY scripts/w08_ref_run.py ${STEPS:-} > /home/jin/v4w08/log_$n.txt 2>&1; echo "EXIT:$?" >> /home/jin/v4w08/log_$n.txt ) & }
run main W08_ANCHOR_MODE=ras W08_ID_PAPER_FW=residue
run iid W08_ANCHOR_MODE=fixedcol W08_ID_PAPER_FW=residue
STEPS="--steps S1,S7" run i2chk W08_ANCHOR_MODE=fixedcol W08_ID_PAPER_FW=purchased
wait
echo ALLDONE > /home/jin/v4w08/ref_runs.done
