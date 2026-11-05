#!/bin/bash
cd /home/jin/wt_v3_fix
for f in research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/hpr_job.sh research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/hpr_submit.sh research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/hpr_status.sh research/06_scope_redesign/p1_v3_20261102/hpc_v31/make_hpc_package_v31.sh; do
  a=$(/home/jin/v3h/bash42/src/bash -n "$f" 2>&1 && echo ok42); b=$(bash -n "$f" 2>&1 && echo ok5); echo "$(basename $f): bash4.2=$a bash5=$b"
done
