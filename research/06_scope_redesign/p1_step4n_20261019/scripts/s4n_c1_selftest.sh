#!/bin/bash
# local self-test of the C1 tools on the S4N-1 56x3h solve (read-only, no solver call): l23_violation_analysis.py, then s4n_c1_precision.py
set -u
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; REPO=/home/jin/s4n_local/pkg/repo; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=$RM/results_project/s4n/s4n1/solve; NET=$RM/results_project/s4m/s4m1/builds/integrated/integrated_2920_3h_unsolved.nc; T=/tmp/s4n_c1_selftest; mkdir -p $T
export PYTHONHASHSEED=0; unset GRB_LICENSE_FILE
/usr/bin/time -v $PY $REPO/scripts_project/l23_violation_analysis.py --repo $REPO --solve-dir $D --network $NET --scenario integrated --truncate 56 --label SMOKE_TEST_ONLY --out $T/VIOLATIONS.json > $T/va.log 2> $T/va.err
echo "VA_EXIT:$? $(grep -h 'Elapsed' $T/va.err | tr -s ' \t' ' ')"; tail -c 600 $T/va.log; echo
/usr/bin/time -v $PY /home/jin/s4n_c1_precision.py --repo $REPO --solve-dir $D --network $NET --scenario integrated --truncate 56 --label SMOKE_TEST_ONLY --violations $T/VIOLATIONS.json --out-json $T/PP.json --out-md $T/PP.md > $T/c1.log 2> $T/c1.err
echo "C1_EXIT:$? $(grep -h 'Elapsed' $T/c1.err | tr -s ' \t' ' ') $(grep -h 'Maximum resident' $T/c1.err | tr -s ' \t' ' ')"; cat $T/c1.log; grep -v "PROJ\|warn\|Warning" $T/c1.err | tail -15
