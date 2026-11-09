#!/bin/bash
# V4 W20: LP-level equivalence of the solve path on a pre-cut 56-snapshot file and on the 2920x3h file with --truncate 56 (s2_solve.py --stop-before-solve:
# the LP is built and exported, the solver is NOT called; no licence in the environment). Identity coalition (11 countries + bunker) vs the W14 network.
set -u
WT=/home/jin/wt_v4_w20; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
BASE=$MAIN/results_project/v4w14/builds/main/integrated/integrated_2920_3h_unsolved.nc; COSTS=$MAIN/results_project/v4w14/builds/main/integrated/costs_active_research.csv
D=/home/jin/v4w20/lpcheck; rm -rf $D/A $D/B; mkdir -p $D
cd $WT || exit 1
$PY scripts_project/v4_coalition.py build --base $BASE --members BN,ID,KH,LA,MM,MY,PH,SG,TH,TL,VN --include-bunker --name FULLB --out $D --truncate 56 > $D/FULLB_build.log 2>&1 || exit 1
for k in A B; do
  net=$BASE; [ $k = B ] && net=$D/FULLB_56_unsolved.nc
  env -u GRB_LICENSE_FILE $PY scripts_project/s2_solve.py --repo . --network $net --scenario integrated --output $D/$k --label SMOKE_TEST_ONLY --authorization "W20 LP check (stop before solve, no solver call)" \
     --solver gurobi --solver-profile formal_barrier_1e6_t16 --scaling on --time-limit 3000 --costs-table $COSTS --truncate 56 --stop-before-solve > $D/$k.log 2>&1
  echo "$k exit=$? net=$(sha256sum $net | cut -c1-16)"
done
for f in $(cd $D/A/lp && ls); do a=$(sha256sum $D/A/lp/$f | cut -c1-64); b=$(sha256sum $D/B/lp/$f | cut -c1-64); echo "$f $([ $a = $b ] && echo SAME || echo DIFF) $a"; done
$PY -c "import json,sys; a=json.load(open('$D/A/SOLVE_RECEIPT.json')); b=json.load(open('$D/B/SOLVE_RECEIPT.json')); print('lp', a['lp']['num_col'], a['lp']['num_row'], a['lp']['nnz'], '|', b['lp']['num_col'], b['lp']['num_row'], b['lp']['nnz'], '| hooks equal', a['lp']['research_constraints']==b['lp']['research_constraints'], '| params equal', a['solver_parameters']==b['solver_parameters'], '| decision', a.get('decision'), b.get('decision'), '| optimize_calls', a['optimize_calls'], b['optimize_calls'])"
