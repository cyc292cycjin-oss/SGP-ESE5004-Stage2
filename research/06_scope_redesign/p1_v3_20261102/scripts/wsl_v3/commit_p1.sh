#!/bin/bash
# V3 phase 1: three commits (1.1 / 1.2 / 1.3 + report), push, mirror to work/. Patterns for the leak scan come from the environment only.
set -e
W=/home/jin/wt_v3_20261102; D=research/06_scope_redesign/p1_v3_20261102; WORK=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102
cd "$W"
mkdir -p "$D/scripts/wsl_v3"
cp "$WORK/V3_CLAUDE_CODE_INSTRUCTION.md" "$WORK/V3_INSTRUCTION_SHA256.txt" "$D/"
cp /home/jin/v3/*.py /home/jin/v3/*.sh "$D/scripts/wsl_v3/"
echo "== licence / credential scan (file names only)"
if grep -rIlE --exclude=commit_p1.sh "WLSACCESSID|WLSSECRET|LICENSEID|BEGIN (RSA|OPENSSH) PRIVATE KEY|GRB_LICENSE_FILE=" "$D"; then echo "LEAK SUSPECT"; exit 3; fi
echo clean
git add "$D/V3_CODE_LOCATIONS.md"
git commit -q -F /home/jin/v3/msg_a.txt
git add -f "$D/V3_DATA_INTAKE.md" "$D/evidence"
git commit -q -F /home/jin/v3/msg_b.txt
git add -f "$D"
git commit -q -F /home/jin/v3/msg_c.txt
git log --oneline -3 | cut -c1-110
git push -q origin codex/v3-20261102 2>&1 | tail -2
git ls-remote origin refs/heads/codex/v3-20261102
git status --short | head -5
echo "== mirror (new files only, the two instruction files stay untouched)"
for f in V3_CODE_LOCATIONS.md V3_DATA_INTAKE.md V3_DESIGN.md V3_PROGRESS.md V3_REPORT_PHASE1.md; do cp "$D/$f" "$WORK/$f"; done
cp -r "$D/evidence" "$WORK/"
cd "$WORK" && sha256sum -c V3_INSTRUCTION_SHA256.txt && ls -la | head -14
