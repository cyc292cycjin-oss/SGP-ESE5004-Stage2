#!/bin/bash
# DFX v3 phase 3: after the final chain - collect evidence (second dry run / package / full suite), evidence JSON, P6 rescan (new package + all commits), P9 recheck.
set -u
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026
echo "== full suite result"; grep -E "passed|failed" $MAIN/tests/full.log | tail -2; grep -E "^(FAILED|ERROR)" $MAIN/tests/full.log | head -20
D=/home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026
echo "== keep the first full-suite log"; [ -f $D/evidence/tests/full.log ] && [ ! -f $D/evidence/tests/full_first_f73f5c06.log ] && ( cd /home/jin/wt_dfx_v3_20261026 && git mv research/06_scope_redesign/p1_dfx_20261026/evidence/tests/full.log research/06_scope_redesign/p1_dfx_20261026/evidence/tests/full_first_f73f5c06.log && echo moved )
echo "== collect evidence"; bash /home/jin/dfx3/collect_evidence.sh dry_run_v8b > /dev/null; ls /home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026/evidence/
echo "== evidence json"; /home/jin/miniforge3/envs/pypsa-earth/bin/python /home/jin/dfx3/make_evidence.py $W/cloud_package_dfx $MAIN/tests/full.log
echo "== P6 rescan"; bash /home/jin/dfx3/p6_scan.sh | /home/jin/miniforge3/envs/pypsa-earth/bin/python -c "import json,sys; r=json.load(sys.stdin); print('clean', r['clean'], 'secret_values', r['n_secret_values']); [print(k, [(h[0], h[1], h[2]) for h in v['hits']], 'excluded', v['excluded']) for k, v in r['targets'].items()]; print('commits with hits:', r['commits'])"
cp $MAIN/leak_scan/P6_LEAK_SCAN.json /home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026/evidence/leak_scan/
echo "== P9 recheck"; stat -c "mode=%a owner=%U size=%s" /home/jin/gurobi.lic; echo "gurobi_or_solve_processes=$(ps -eo args= | grep -ciE '[g]urobi|[s]2_solve\.py')"
echo "== package"; cat $W/cloud_package_dfx/COMMIT; sha256sum $W/cloud_package_dfx/SHA256SUMS $W/cloud_package_dfx/PACKAGE_MANIFEST.json | cut -c1-80; du -sb $W/cloud_package_dfx | cut -f1
echo "== git"; cd /home/jin/wt_dfx_v3_20261026 && git log --format="%h %cI %s" -2 | cut -c1-100 && git status --short | head -5
