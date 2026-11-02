#!/bin/bash
# V3 supplement 01 item 8: dry runs of the two runners with the BATCH_DEF files on the real v3 networks in package-like folders (symlinks, nothing packed or uploaded). No solver, no licence.
# AutoDL: BUILD_ONLY on the full 365x24h networks with the registered SHA256 enforced. HPC: the full 2920x3h LP does not fit this machine, so BUILD_ONLY truncated to 56 snapshots (ALLOW_UNREGISTERED=1), and
# the registered 2920x3h SHA256 / bytes and the receipt chain checked by a separate base-check.
set -u
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
B=$MAIN/results_project/v3/builds; O=$MAIN/results_project/v3/dry_runners; D=$W/research/06_scope_redesign
[ ! -e $O ] || { echo "REFUSED: $O exists"; exit 2; }
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[p]ytest')" = 0 ] || { echo "REFUSED: another solve or pytest is running"; exit 2; }
mk() {
  mkdir -p $1/networks
  ln -s $B/integrated/integrated_$2_unsolved.nc $B/integrated/integrated_BUILD_RECEIPT.json $B/no_new_xb/no_new_xb_$2_unsolved.nc $B/no_new_xb/no_new_xb_$2_VARIANT_RECEIPT.json $1/networks/
  ln -s $B/integrated/costs_active_research.csv $1/networks/integrated_costs_active_research.csv
  cp $D/p1_v3_20261102/batch_def/$3 $1/BATCH_DEF.json; cp $D/p1_m10p_20261022/cloud_package/pack_results.sh $1/; ln -s $W $1/repo
}
A=$O/autodl; mk $A 365_24h BATCH_DEF_365x24h.json; cp $D/p1_dfx_20261026/cloud_package_dfx/run_dfx.sh $D/p1_dfx_20261026/cloud_package_dfx/preflight_dfx.sh $A/
env -u GRB_LICENSE_FILE PY=$PY BUILD_ONLY=1 RUN_DIR=$A/out bash $A/run_dfx.sh > $A/run.log 2>&1
echo "AUTODL_BUILD_ONLY exit=$?"; grep -E "BASE_CHECK|BUILD_CHECK|STOP|SAFE|DONE" $A/out/STATUS.txt | cut -c1-200 | tail -8
H=$O/hpc; mk $H 2920_3h BATCH_DEF_2920x3h.json; cp $D/p1_b4p_20261026/cloud_package_b4/run_batch4.sh $D/p1_b4p_20261026/cloud_package_b4/preflight.sh $H/
( cd $W && BATCH_DEF=$H/BATCH_DEF.json env -u GRB_LICENSE_FILE $PY scripts_project/b4_batch4.py base-check --nets $H/networks --out $H/BASE_CHECK_REGISTERED.json ); echo "HPC_REGISTERED_BASE_CHECK exit=$?"
env -u GRB_LICENSE_FILE PY=$PY ALLOW_UNREGISTERED=1 BUILD_ONLY=1 TRUNCATE=56 RUN_DIR=$H/out bash $H/run_batch4.sh > $H/run.log 2>&1
echo "HPC_BUILD_ONLY_T56 exit=$?"; grep -E "BASE_CHECK|BUILD_CHECK|STOP|SAFE|DONE" $H/out/STATUS.txt | cut -c1-200 | tail -8
echo FINISHED
