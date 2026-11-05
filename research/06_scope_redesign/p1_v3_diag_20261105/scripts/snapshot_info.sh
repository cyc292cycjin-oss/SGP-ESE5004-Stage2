#!/bin/bash
set -u
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
PKG=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3/networks
EV=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_diag_20261105/evidence
S=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_diag_20261105/scripts
cd /home/jin/wt_v3_diag/scripts_project
env -u GRB_LICENSE_FILE PYTHONHASHSEED=0 "$PY" "$S/snapshot_info.py" "$PKG/integrated_2920_3h_unsolved.nc" "$EV/F1_SNAPSHOTS.json"
