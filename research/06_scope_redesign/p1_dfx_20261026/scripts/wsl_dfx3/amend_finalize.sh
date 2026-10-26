#!/bin/bash
# DFX v3 amendment close-out: archive the previous evidence dirs (tracked: git mv), collect the third dry run / package evidence, evidence JSON, P6 rescan,
# commit, push (never force), sync the work folder, final facts.
set -u
WT=/home/jin/wt_dfx_v3_20261026; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026
D=$WT/research/06_scope_redesign/p1_dfx_20261026; R=research/06_scope_redesign/p1_dfx_20261026; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $WT || exit 1
[ -d $D/evidence/dry_run ] && [ ! -d $D/evidence/dry_run_f73f5c06 ] && git mv $R/evidence/dry_run $R/evidence/dry_run_f73f5c06 && echo "dry_run -> dry_run_f73f5c06"
[ -d $D/evidence/package ] && [ ! -d $D/evidence/package_superseded_f73f5c06 ] && git mv $R/evidence/package $R/evidence/package_superseded_f73f5c06 && echo "package -> package_superseded_f73f5c06"
cp $MAIN/results_project/dfx_v3/tests/amend.log $D/evidence/tests/ 2>/dev/null
bash /home/jin/dfx3/collect_evidence.sh dry_run_v8c > /dev/null; ls $D/evidence/dry_run $D/evidence/package | head -20
echo "== evidence json"; $PY /home/jin/dfx3/make_evidence.py $W/cloud_package_dfx $MAIN/results_project/dfx_v3/tests/full.log | head -3
echo "== P6 rescan"; bash /home/jin/dfx3/p6_scan.sh | $PY -c "import json,sys; r=json.load(sys.stdin); print('clean', r['clean'], 'secret_values', r['n_secret_values']); [print(k.split('/')[-1], 'files', v['files'], 'hits', [(h[0], h[1], h[2]) for h in v['hits']]) for k, v in r['targets'].items()]; print('commits with hits:', {k: (v['value_hits'], v['pattern_hits'], [f.split('/')[-1] for f in v['files']]) for k, v in r['commits'].items() if v['value_hits'] or v['pattern_hits']})"
cp $MAIN/results_project/dfx_v3/leak_scan/P6_LEAK_SCAN.json $D/evidence/leak_scan/
echo "== commit"; bash /home/jin/dfx3/commit.sh /home/jin/dfx3/msg_amend2.txt 2>&1 | tail -2
echo "== push"; bash /home/jin/dfx3/push.sh | tail -4
echo "== sync"; bash /home/jin/dfx3/sync_work.sh | tail -1
echo "== package"; cat $W/cloud_package_dfx/COMMIT; $PY -c "import json; m=json.load(open('$W/cloud_package_dfx/PACKAGE_MANIFEST.json')); print(len(m['files']), 'files', m['upload_total_bytes_excluding_this_manifest'], 'B', m['run']['time_limit_s'], m['run']['wall_cap_s'], m['upload']['hours_at'])"; ls -d $W/cloud_package_dfx*
echo "gurobi_or_solve_processes=$(ps -eo args= | grep -ciE '[g]urobi|[s]2_solve\.py')"
