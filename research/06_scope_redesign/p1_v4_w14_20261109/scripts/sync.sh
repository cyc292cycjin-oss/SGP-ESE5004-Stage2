#!/bin/bash
# W14: mirror the delivery folder into the repository (research/06_scope_redesign/p1_v4_w14_20261109/). Excluded: the upload package hpc_package_v4*/
# (instruction section 6: not committed), zip files, __pycache__, msg_*.txt, cache/. Text files written on Windows are normalised to LF in the mirror
# (the repository commits LF; the Windows originals are not touched).
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w14_20261109; R=/home/jin/wt_v4_w14; D=$R/research/06_scope_redesign/p1_v4_w14_20261109
mkdir -p $D
rsync -a --delete --exclude '/hpc_package_v4*' --exclude '*.zip' --exclude '__pycache__' --exclude 'msg_*.txt' --exclude 'cache/' $W/ $D/
echo "synced $(find $D -type f | wc -l) files"
find $D -type f \( -name '*.json' -o -name '*.txt' -o -name '*.csv' -o -name '*.md' -o -name '*.py' -o -name '*.sh' \) -exec grep -l $'\r' {} + 2>/dev/null | while read f; do sed -i 's/\r$//' "$f"; echo "LF $f"; done
