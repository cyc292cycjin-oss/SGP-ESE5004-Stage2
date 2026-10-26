#!/bin/bash
# DFX v3 phase 3: facts for P1 (order of commits vs builds / solves) and P9 (licence file: existence, owner, mode, size, mtime only; no content).
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3
cd /home/jin/wt_dfx_v3_20261026 || exit 1
echo "=== commits (committer time, ISO) ==="; git log --format="%h %cI %s" 55ab07c0..HEAD | cut -c1-120
echo "=== file times (UTC mtime) ==="
for f in $MAIN/builds_v2/integrated/integrated_2920_3h_unsolved.nc $MAIN/builds_v2/integrated/integrated_365_24h_unsolved.nc $MAIN/builds_v2/disconnected/disconnected_365_24h_unsolved.nc $MAIN/builds_v2/integrated/integrated_BUILD_RECEIPT.json $MAIN/builds_v2/disconnected/disconnected_BUILD_RECEIPT.json $MAIN/smoke_v2/integrated/gurobi.linopy.log $MAIN/smoke_v2/disconnected/gurobi.linopy.log $MAIN/smoke_v2/STATUS.txt $MAIN/dry_run_v8/DRY_RUN_DFX.json; do
  echo "$(date -u -r "$f" +%FT%TZ)  $(stat -c %s "$f")  ${f#$MAIN/}"
done
echo "=== smoke STATUS first lines ==="; head -2 $MAIN/smoke_v2/STATUS.txt
echo "=== P9 licence file (stat only) ==="; stat -c "mode=%a owner=%U size=%s mtime=%y path=%n" /home/jin/gurobi.lic
echo "readable_by_user=$([ -r /home/jin/gurobi.lic ] && echo yes || echo no)"
echo "gurobi_or_solve_processes=$(ps -eo args= | grep -ciE '[g]urobi|[s]2_solve\.py')"
echo "=== worktree status ==="; git status --short | head; echo "branch=$(git branch --show-current) head=$(git rev-parse HEAD)"
echo "=== upstream ==="; git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>&1 | head -1; git log --oneline -1 origin/codex/b4-prep-20261026 2>/dev/null; git merge-base --is-ancestor 55ab07c0 HEAD && echo "base 55ab07c0 is an ancestor of HEAD"; git log --oneline main..HEAD 2>/dev/null | wc -l; git log --oneline HEAD..main 2>/dev/null | wc -l
