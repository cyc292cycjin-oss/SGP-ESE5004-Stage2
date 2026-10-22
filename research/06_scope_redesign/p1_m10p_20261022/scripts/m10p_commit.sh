#!/bin/bash
# M10P commit helper: mirror work/p1_m10p_20261022 (without cloud_package_dist/ and *.zip) into research/06_scope_redesign/p1_m10p_20261022/,
# force-add that folder (root .gitignore ignores *.csv / *.log / *.nc) plus the tracked code paths given as arguments, commit with /home/jin/m10p_msg.txt.
set -u
WT=/home/jin/wt_m10p_20261022; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022; D=research/06_scope_redesign/p1_m10p_20261022
cd $WT || exit 1
[ "$(git branch --show-current)" = codex/m10-batch3-20261022 ] || { echo "WRONG BRANCH"; exit 2; }
mkdir -p $D
rsync -a --delete --exclude cloud_package_dist/ --exclude '*.zip' --exclude dryrun_local/ --exclude __pycache__/ --exclude cloud_package/ "$W/" "$D/"
big=$(find $D -type f -size +5M | head -5); [ -z "$big" ] || { echo "REFUSED: files > 5 MB in $D: $big"; exit 3; }
if grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $D > /tmp/m10p_lic_hits.txt 2>/dev/null; then echo "REFUSED: licence-like strings in $(cat /tmp/m10p_lic_hits.txt)"; exit 4; fi
git add -f $D
[ $# -gt 0 ] && git add -- "$@"
git status --short | head -40
git commit -q -F /home/jin/m10p_msg.txt || { echo "COMMIT FAILED"; exit 5; }
echo "COMMIT $(git rev-parse HEAD) $(git log -1 --format=%s | cut -c1-100)"
echo "dirty_tracked_after $(git status --porcelain --untracked-files=no | wc -l)"
