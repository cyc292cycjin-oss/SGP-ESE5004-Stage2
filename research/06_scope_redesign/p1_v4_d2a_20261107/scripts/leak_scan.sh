#!/bin/bash
# D2a: licence-like content scan of the delivery folder and the review zip; patterns read at run time from a file outside the repository (never printed).
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2a_20261107; PF=${LEAK_PATTERN_FILE:-$HOME/.dfx_leak_patterns}
pat=$(grep -v '^#' "$PF" | grep -E '^key=' | cut -d= -f2-)
[ -n "$pat" ] || { echo "no patterns"; exit 2; }
n=$(grep -rIlE "$pat" "$W" --exclude='*.zip' --exclude-dir=cache 2>/dev/null | wc -l)
t=$(mktemp -d); /home/jin/miniforge3/envs/pypsa-earth/bin/python -c "import sys, zipfile, glob; zipfile.ZipFile(sorted(glob.glob(sys.argv[1]))[-1]).extractall(sys.argv[2])" "$W/REVIEW_*.zip" $t; z=$(grep -rIlE "$pat" $t 2>/dev/null | wc -l); rm -rf $t
echo "files_with_licence_like_content: folder=$n zip=$z"
