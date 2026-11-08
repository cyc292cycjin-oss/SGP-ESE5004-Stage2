#!/bin/bash
# W14: licence-like content scan of the delivery folder (incl. the package folder), the drill folders and the newest review zip. Two scans: the pattern file outside the
# repository (patterns never printed) and the regex of pack_results.sh (text files, case-insensitive). Prints counts and the names of matching files only.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w14_20261109; PF=${LEAK_PATTERN_FILE:-$HOME/.dfx_leak_patterns}
LRX='license[i]d|registered[[:space:]]+to|wls(secret|accessid)'
pat=$(grep -v '^#' "$PF" | grep -E '^key=' | cut -d= -f2-)
[ ${#pat} -gt 3 ] || { echo "no patterns"; exit 2; }
n=$(grep -rIlE "$pat" "$W" --exclude='*.zip' 2>/dev/null | wc -l)
r=$(grep -rIilE "$LRX" "$W" --exclude='*.zip' 2>/dev/null); rn=$(printf '%s' "$r" | grep -c .)
d=0; for x in /home/jin/v4w14/dry_* /home/jin/v4w14/smoke_*; do [ -d "$x" ] || continue; d=$((d + $(grep -rIlE "$pat" "$x" --exclude-dir=repo 2>/dev/null | wc -l))); done
t=$(mktemp -d); z=$(ls -t $W/REVIEW_*.zip 2>/dev/null | head -1)
if [ -n "$z" ]; then /home/jin/miniforge3/envs/pypsa-earth/bin/python -c "import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$z" $t; fi
zp=$(grep -rIlE "$pat" $t 2>/dev/null | wc -l); zr=$(grep -rIilE "$LRX" $t 2>/dev/null | grep -c .); rm -rf $t
echo "pattern_file: folder=$n drill_folders_outside_repo=$d zip=$zp ($(basename "${z:-none}"))"
echo "pack_results_regex: folder=$rn zip=$zr"
[ "$rn" = 0 ] || printf '%s\n' "$r" | sed "s|$W/||" | head -10
