#!/bin/bash
# X20 A 段：最终镜像、提交 X20_SPEC.md 等到 asean/v5-x20-20261111 并推送（不合并 main，不 force-push，不跳过 hooks）
set -u
DELIV=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
WT=/home/jin/wt_v5_x20
STEP=research/06_scope_redesign/p1_v5_x20_20261111
BR=asean/v5-x20-20261111
cd "$WT" || exit 2
[ "$(git branch --show-current)" = "$BR" ] || { echo "wrong branch"; exit 3; }
for f in X20_SPEC.md PROGRESS.md DOWNLOAD_CANDIDATES.csv; do cp "$DELIV/$f" "$STEP/$f"; done
for d in scripts logs evidence; do cp "$DELIV/$d"/* "$STEP/$d/"; done
find "$STEP" -type f \( -name "*.md" -o -name "*.csv" -o -name "*.sh" -o -name "*.py" -o -name "*.log" -o -name "*.txt" \) ! -name "V5_X20_INSTRUCTION.md" ! -name "V5_X20_SHA256.txt" -print0 | xargs -0 sed -i 's/\r$//'
(cd "$STEP" && sha256sum -c V5_X20_SHA256.txt) || exit 4
git add -f "$STEP"
echo "== staged"; git diff --cached --name-only | sed 's/^/  /'
OUTSIDE=$(git diff --cached --name-only | grep -v "^$STEP/" | wc -l)
[ "$OUTSIDE" = "0" ] || { echo "staged files outside the step dir: $OUTSIDE"; exit 5; }
echo "== eol"; git ls-files --eol "$STEP" | grep -i crlf || echo "no CRLF in index"
git commit -F "$DELIV/scripts/commit_msg_A.txt" || exit 6
echo "== head"; git rev-parse HEAD; git log -1 --format='%H %s'
echo "== sha of spec at HEAD"; git show HEAD:"$STEP/X20_SPEC.md" | sha256sum
echo "== push"; timeout 120 git push -u origin "$BR"; echo "push_exit=$?"
echo "== remote"; timeout 60 git ls-remote origin "refs/heads/$BR"
