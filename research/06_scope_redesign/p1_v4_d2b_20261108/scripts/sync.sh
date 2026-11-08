#!/bin/bash
# D2b: mirror the delivery folder into the repository (research/06_scope_redesign/p1_v4_d2b_20261108/; zip files, __pycache__, msg_*.txt, cache/ excluded).
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2b_20261108; R=/home/jin/wt_v4_d2b; D=$R/research/06_scope_redesign/p1_v4_d2b_20261108
mkdir -p $D
rsync -a --delete --exclude '*.zip' --exclude '__pycache__' --exclude 'msg_*.txt' --exclude 'cache/' --exclude 'scripts/ref/__pycache__' $W/ $D/
echo "synced $(find $D -type f | wc -l) files"
