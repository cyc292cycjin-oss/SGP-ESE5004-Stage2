#!/bin/bash
# X20 A 段结束：磁盘记录；把交付目录镜像到 worktree 的本步目录（LF 规范化）；显示 git 状态（不提交）
set -u
DELIV=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
WT=/home/jin/wt_v5_x20
STEP=research/06_scope_redesign/p1_v5_x20_20261111
echo "== date"; date '+%Y-%m-%d %H:%M:%S %Z'
echo "== df -h /"; df -h /
echo "== du delivery"; du -sb "$DELIV"; du -sh "$DELIV"
echo "== du worktree"; du -sb "$WT"
echo "== free"; free -b | head -2
cd "$WT" || exit 2
mkdir -p "$STEP"
for f in V5_X20_INSTRUCTION.md V5_X20_SHA256.txt X20_SPEC.md PROGRESS.md DOWNLOAD_CANDIDATES.csv; do cp "$DELIV/$f" "$STEP/$f"; done
for d in scripts logs evidence; do mkdir -p "$STEP/$d"; cp "$DELIV/$d"/* "$STEP/$d/"; done
# LF 规范化（指令文件与其 SHA 文件保持原样，以便 sha256sum -c 仍然通过）
find "$STEP" -type f \( -name "*.md" -o -name "*.csv" -o -name "*.sh" -o -name "*.py" -o -name "*.log" -o -name "*.txt" \) ! -name "V5_X20_INSTRUCTION.md" ! -name "V5_X20_SHA256.txt" -print0 | xargs -0 sed -i 's/\r$//'
(cd "$STEP" && sha256sum -c V5_X20_SHA256.txt)
echo "== files in mirror"; find "$STEP" -type f | sort | sed "s|$STEP/||"
echo "== ignored (need -f)"; git status --short --ignored "$STEP" | head -40
echo "== crlf check"; git add -n -f "$STEP" >/dev/null; file $(find "$STEP" -type f) | grep -i crlf || echo "no CRLF"
