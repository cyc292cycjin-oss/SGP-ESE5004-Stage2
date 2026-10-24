#!/bin/bash
# M10A tests: MODE=before  -> selected new tests against the v3 package scripts (M10P_PKG_DIR = cloud_package_dist: unfixed run_batch3.sh / preflight.sh)
#             MODE=m10p    -> tests/research/test_m10p_batch3.py against the fixed scripts (repo)
#             MODE=full    -> full tests/research (toy LP tests allowed by the instruction; no Gurobi: GRB_LICENSE_FILE removed)
#             MODE=chain   -> before, m10p, full one after the other (never in parallel: busy() of one test run would see the stand-ins of another)
set -u
WT=/home/jin/wt_m10p_20261022; E=/home/jin/m10a_evidence; mkdir -p $E
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
V3=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022/cloud_package_dist
MODE=${MODE:?before|m10p|full|chain}
cd $WT || exit 1
chmod 755 research/06_scope_redesign/p1_m10p_20261022/cloud_package/*.sh research/06_scope_redesign/p1_m10p_20261022/cloud_package/env/install_env.sh
for f in research/06_scope_redesign/p1_m10p_20261022/cloud_package/run_batch3.sh research/06_scope_redesign/p1_m10p_20261022/cloud_package/preflight.sh research/06_scope_redesign/p1_m10p_20261022/cloud_package/env/install_env.sh; do bash -n $f || { echo "SYNTAX ERROR $f"; exit 1; }; done
run_mode() {
  local M=$1 L=$E/TESTS_$1.log
  echo "HEAD $(git rev-parse HEAD) dirty_tracked $(git status --porcelain --untracked-files=no | wc -l) $(date -u +%FT%TZ) mode=$M" > $L
  case $M in
    before)
      for k in test_full_batch_pairing test_post_processing_crash_is_recorded test_solver_process_running test_formal_run_refuses test_preflight_guards; do
        echo "=== before (v3 scripts): $k ===" >> $L
        env -u GRB_LICENSE_FILE M10P_PKG_DIR=$V3 timeout 900 $PY -m pytest tests/research/test_m10p_batch3.py -q -p no:cacheprovider -ra -k "$k" >> $L 2>&1
        echo "EXIT $?" >> $L
      done;;
    m10p)
      env -u GRB_LICENSE_FILE timeout 2400 $PY -m pytest tests/research/test_m10p_batch3.py -q -p no:cacheprovider -ra >> $L 2>&1; echo "EXIT $?" >> $L;;
    full)
      env -u GRB_LICENSE_FILE timeout 3000 $PY -m pytest tests/research -q -p no:cacheprovider -ra >> $L 2>&1; echo "EXIT $?" >> $L;;
  esac
  echo "END $(date -u +%FT%TZ)" >> $L; echo DONE >> $L
  echo "----- $M -----"; grep -E "^(=== |EXIT|HEAD|END)|passed|failed|error" $L | tail -40
}
if [ "$MODE" = chain ]; then run_mode before; run_mode m10p; run_mode full; else run_mode $MODE; fi
echo CHAIN_DONE
