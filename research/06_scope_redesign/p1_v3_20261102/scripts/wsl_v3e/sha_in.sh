#!/bin/bash
# V3 supplement 06: SHA256 of the networks read by the diagnosis (to tie them to the registered values), size of the evidence folder
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3
X=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/cloud_results/final_20261103T063207Z/full_unpacked/export
sha256sum $R/builds_op/integrated/integrated_2920_3h_unsolved.nc $R/builds_op/no_new_xb/no_new_xb_2920_3h_unsolved.nc $R/builds_op/integrated/integrated_365_24h_unsolved.nc \
  $R/smoke_s5/integrated/integrated_SMOKE_TEST_ONLY_solved.nc $R/smoke_s5/no_new_xb/no_new_xb_SMOKE_TEST_ONLY_solved.nc $R/smoke_s1/integrated/integrated_SMOKE_TEST_ONLY_solved.nc \
  $X/V1/integrated_DFX_365X24H_solved.nc $X/V2/no_new_xb_DFX_365X24H_solved.nc $X/V3/disconnected_DFX_365X24H_solved.nc $X/V4/integrated_DFX_365X24H_solved.nc $X/V5/integrated_DFX_365X24H_solved.nc | sed "s#$R/##; s#$X/##"
grep -n -E "1bddacb7|b262f6aa|330e1d31" /home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/RUN_PLAN_V3.md | head -5 | cut -c1-200
grep -h -E "solved.nc" $X/V1/SOLVE_RECEIPT.json $X/V5/SOLVE_RECEIPT.json 2>/dev/null | head -4 | cut -c1-200
grep -c . /dev/null; du -sh /home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/evdiag
