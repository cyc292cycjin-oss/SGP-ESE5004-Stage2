#!/bin/bash
# X20 B 段提交：同步本步目录 -> 暂存（代码目录 + 强制清单）-> 检查 -> 提交 -> 推送。用法：bcommit.sh <消息文件在 D 盘 scripts/ 下的文件名>
# 不用 --no-verify，不改 core.hooksPath，不合并 main，不 force-push。
set -u
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
WT=/home/jin/wt_v5_x20
STEP=research/06_scope_redesign/p1_v5_x20_20261111
BR=asean/v5-x20-20261111
MSG="$D/scripts/${1:?message file}"
[ -s "$MSG" ] || { echo "no message file $MSG"; exit 2; }
cd "$WT" || exit 2
[ "$(git branch --show-current)" = "$BR" ] || { echo "wrong branch"; exit 3; }
# 1) 同步交付目录的文档、脚本、证据与日志（不含网络与大文件目录）
mkdir -p "$STEP/scripts" "$STEP/logs" "$STEP/evidence"
for f in "$D"/*.md "$D"/*.csv "$D"/*.json; do [ -e "$f" ] && cp "$f" "$STEP/"; done
cp "$D"/scripts/* "$STEP/scripts/" 2>/dev/null
cp "$D"/evidence/* "$STEP/evidence/" 2>/dev/null
find "$D/logs" -maxdepth 1 -type f -size -2M -exec cp {} "$STEP/logs/" \;
find "$STEP" -type f \( -name "*.md" -o -name "*.csv" -o -name "*.sh" -o -name "*.py" -o -name "*.log" -o -name "*.txt" -o -name "*.json" \) ! -name "V5_X20_INSTRUCTION.md" ! -name "V5_X20_SHA256.txt" -print0 | xargs -0 sed -i 's/\r$//'
find "$STEP" -type f -exec chmod 644 {} +
(cd "$STEP" && sha256sum -c --quiet V5_X20_SHA256.txt) || { echo "instruction SHA changed"; exit 4; }
# 2) 暂存
git add -f "$STEP"
git add -A scripts_project configs tests
[ -s "$D/scripts/force_add.txt" ] && while read -r p; do [ -n "$p" ] && [ -e "$p" ] && git add -f "$p"; done < "$D/scripts/force_add.txt"
git add -u research_inputs
echo "== staged"; git diff --cached --stat | tail -40
echo "== untracked / ignored new files under research_inputs (not staged)"; git status --short --ignored research_inputs | grep -E '^(\?\?|!!)' | head -20
# 3) 检查
CR=$(git diff --cached --name-only -z | xargs -0 -r file 2>/dev/null | grep -ci crlf)
[ "$CR" = "0" ] || { echo "CRLF in staged files: $CR"; git diff --cached --name-only -z | xargs -0 -r file | grep -i crlf; exit 5; }
BIG=$(git diff --cached --name-only -z | xargs -0 -r ls -l 2>/dev/null | awk '$5 > 20000000 {print $9}')
[ -z "$BIG" ] || { echo "staged file > 20 MB: $BIG"; exit 6; }
[ "$(git diff --cached --name-only | wc -l)" -gt 0 ] || { echo "nothing staged"; exit 7; }
# 4) 提交与推送
git commit -F "$MSG" || exit 8
git log -1 --format='HEAD %H %s'
timeout 120 git push -u origin "$BR" > "$D/logs/push_last.log" 2>&1; rc=$?
tail -3 "$D/logs/push_last.log"; echo "push_exit=$rc"
timeout 60 git ls-remote origin "refs/heads/$BR"
