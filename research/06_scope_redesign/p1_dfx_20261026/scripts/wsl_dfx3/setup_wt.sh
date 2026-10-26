#!/bin/bash
# DFX v3 step 0: new branch codex/dfx-v3-20261026 + worktree /home/jin/wt_dfx_v3_20261026 from the local head of codex/b4-prep-20261026.
# The paused session's branch codex/dfx-20261026 / worktree wt_dfx_20261026 / helper dir /home/jin/dfx are left untouched.
set -u
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
WT=/home/jin/wt_dfx_v3_20261026
BR=codex/dfx-v3-20261026
BASE=codex/b4-prep-20261026
cd "$MAIN" || exit 1
echo "local base head: $(git rev-parse --short $BASE) $(git log --format=%s -1 $BASE | cut -c1-80)"
echo "remote base head: $(git ls-remote origin refs/heads/$BASE | cut -c1-8)"
if [ -e "$WT" ]; then echo "worktree path exists already: $WT"; exit 2; fi
git worktree add -b "$BR" "$WT" "$BASE" || exit 4
cd "$WT" || exit 5
git log --oneline -1
mkdir -p research_inputs/finance_v5
for f in COUNTRY_WACC_PUBLIC_SOURCES.csv DISCOUNT_RATE_IN_USE.csv; do
  [ -f research_inputs/finance_v5/$f ] || cp /home/jin/wt_b4p_20261026/research_inputs/finance_v5/$f research_inputs/finance_v5/
done
ls research_inputs/finance_v5/
mkdir -p results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
ls -la results_project/
mkdir -p research/06_scope_redesign/p1_dfx_20261026/scripts
cp /mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/DFX_CLAUDE_CODE_INSTRUCTION.md /mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/DFX_INSTRUCTION_SHA256.txt research/06_scope_redesign/p1_dfx_20261026/
mkdir -p $MAIN/results_project/dfx_v3
git status --short | head
echo "diff base..ec80668f (scripts_project research_inputs configs) name-only:"
git diff --name-only ec80668f HEAD -- scripts_project research_inputs configs
echo SETUP_DONE
