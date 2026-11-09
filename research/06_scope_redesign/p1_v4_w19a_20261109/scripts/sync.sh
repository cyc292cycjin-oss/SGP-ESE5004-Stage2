#!/bin/bash
# W19a: mirror the delivery folder into the repository (cache/, zip, __pycache__ excluded); then list what git sees.
set -u
SRC=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w19a_20261109/
DST=/home/jin/wt_v4_w19a/research/06_scope_redesign/p1_v4_w19a_20261109/
mkdir -p "$DST"
rsync -a --delete --exclude cache/ --exclude '*.zip' --exclude __pycache__/ "$SRC" "$DST"
cd /home/jin/wt_v4_w19a && git status --porcelain | head -60 && git status --porcelain | wc -l
du -sh "$DST"
