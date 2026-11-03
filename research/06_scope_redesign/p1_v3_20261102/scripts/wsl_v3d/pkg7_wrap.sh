#!/bin/bash
# V3 supplement 07: the package is built at the commit of the dry run (fbdf2c2e) with a clean tracked tree: the uncommitted progress-table edit is stashed for the packaging and restored after it.
set -u
W=/home/jin/wt_v3_20261102; D=research/06_scope_redesign/p1_v3_20261102
cd $W || exit 1
cp /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/dry_screen7/DRY_RUN_SCREEN.json $D/evidence/dmax/DRY_RUN_SCREEN.json
echo "head $(git rev-parse --short HEAD); dry run commit $(/home/jin/miniforge3/envs/pypsa-earth/bin/python -c "import json; print(json.load(open('$D/evidence/dmax/DRY_RUN_SCREEN.json'))['code_commit'][:8])")"
git stash push -q -m "s7 progress edit during packaging" -- $D/V3_PROGRESS.md && echo "stashed; tracked changes now: $(git status --porcelain --untracked-files=no | wc -l)"
bash /home/jin/v3d/pkg_s7.sh
git stash pop -q && echo "restored; tracked changes now: $(git status --porcelain --untracked-files=no | wc -l)"
