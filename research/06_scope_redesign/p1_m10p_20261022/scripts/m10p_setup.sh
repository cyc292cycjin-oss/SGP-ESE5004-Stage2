#!/bin/bash
# M10P-1: integration branch codex/m10-batch3-20261022 from the M12b head 1f46517d in its own worktree; ignored research inputs copied from the M12 worktree
set -u
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; WT=/home/jin/wt_m10p_20261022; SRC=/home/jin/wt_m12_20261021
cd $MAIN || exit 1
[ -e $WT ] && { echo "worktree path exists"; exit 2; }
git rev-parse --verify -q refs/heads/codex/m10-batch3-20261022 && { echo "branch exists"; exit 2; }
git worktree add -b codex/m10-batch3-20261022 $WT 1f46517dac13c811287f23141e929c06580aad16 || exit 3
cd $WT
echo "HEAD $(git rev-parse HEAD) branch $(git branch --show-current)"
# ignored inputs present in the M12 worktree (tests and the build read them); same files as M12b used
cd $SRC
git status --ignored=matching --porcelain research_inputs configs scripts_project | sed -n 's/^!! //p' > /tmp/m10p_ignored.txt
cat /tmp/m10p_ignored.txt
while read -r f; do [ -f "$f" ] && { mkdir -p "$WT/$(dirname "$f")"; cp -p "$f" "$WT/$f"; echo "copied $f $(sha256sum "$f" | cut -c1-16)"; }; done < /tmp/m10p_ignored.txt
cd $WT; echo "ignored now:"; git status --ignored=matching --porcelain research_inputs configs scripts_project
echo "dirty tracked: $(git status --porcelain --untracked-files=no | wc -l)"
git config user.name; git config user.email
