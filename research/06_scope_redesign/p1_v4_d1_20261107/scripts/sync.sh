#!/bin/bash
# D1: mirror the delivery folder into the repository (research/06_scope_redesign/p1_v4_d1_20261107/; zip files, __pycache__, msg_*.txt excluded).
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d1_20261107; R=/home/jin/wt_v4_d1; D=$R/research/06_scope_redesign/p1_v4_d1_20261107
mkdir -p $D
rsync -a --delete --exclude '*.zip' --exclude '__pycache__' --exclude 'msg_*.txt' --exclude 'cache/' $W/ $D/
echo "synced $(find $D -type f | wc -l) files"
