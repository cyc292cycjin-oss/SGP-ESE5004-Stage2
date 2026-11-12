#!/bin/bash
# X20 C 段：把 LEDGER_ENTRY_X20_C.md 追加到 worktree 的总台账（只追加一次；已存在则不动）
set -eu
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
L=/home/jin/wt_v5_x20/research/STAGE2_PROJECT_LEDGER.md
H=$(head -1 "$D/LEDGER_ENTRY_X20_C.md")
if grep -qF "$H" "$L"; then echo "already present"; exit 0; fi
[ "$(tail -c 1 "$L" | od -An -c | tr -d ' ')" = '\n' ] || printf '\n' >> "$L"
printf '\n' >> "$L"
tr -d '\r' < "$D/LEDGER_ENTRY_X20_C.md" >> "$L"
wc -l "$L"; tail -c 300 "$L"; echo
git -C /home/jin/wt_v5_x20 diff --stat -- research/STAGE2_PROJECT_LEDGER.md
