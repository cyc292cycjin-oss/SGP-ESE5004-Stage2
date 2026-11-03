#!/bin/bash
# V3 supplement 06: mirror the session scripts into the branch, refuse a licence-like string, stage only the supplement 06 files, commit, print the head.
# usage: commit_e.sh <message file>
set -e
W=/home/jin/wt_v3_20261102; D=research/06_scope_redesign/p1_v3_20261102
cd "$W"
mkdir -p "$D/scripts/wsl_v3e"
cp /home/jin/v3e/*.py /home/jin/v3e/*.sh "$D/scripts/wsl_v3e/"
P="WLS""ACCESSID|WLS""SECRET|LICENSE""ID|BEGIN (RSA|OPENSSH) PRIVATE"" KEY"
if grep -rIlE "$P" "$D/V3_REPORT_EVDIAG.md" "$D/V3_RULES.md" "$D/V3_PROGRESS.md" "$D/evidence/evdiag" "$D/scripts/wsl_v3e" 2>/dev/null; then echo "LEAK SUSPECT"; exit 3; fi
echo "== tracked changes before staging"; git status --short --untracked-files=no
git add -f "$D/V3_REPORT_EVDIAG.md" "$D/V3_RULES.md" "$D/V3_PROGRESS.md" "$D/evidence/evdiag" "$D/scripts/wsl_v3e"
echo "== staged"; git diff --cached --stat | tail -40
git commit -q -F "$1"
git log --oneline -1 | cut -c1-120
git status --short | head -5
