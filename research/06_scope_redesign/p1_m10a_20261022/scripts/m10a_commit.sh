#!/bin/bash
# M10A commit: $1 = message file, $2.. = paths (git add -A on them; research/ evidence copies may be ignored patterns -> add with -f when listed in FORCE)
set -u
WT=/home/jin/wt_m10p_20261022; MSG=${1:?message file}; shift
cd $WT || exit 1
[ -s "$MSG" ] || { echo "message file missing"; exit 1; }
git add -A -- "$@" || exit 1
[ -n "${FORCE:-}" ] && git add -f -- $FORCE
git status --short | head -40
git commit -q -F "$MSG" || { echo "COMMIT FAILED"; exit 1; }
echo "COMMIT $(git rev-parse HEAD) $(git log -1 --format=%s | cut -c1-120)"
git status --porcelain --untracked-files=no | wc -l
