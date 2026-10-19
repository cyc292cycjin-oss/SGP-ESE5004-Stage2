#!/bin/bash
# self-test of s4n_c2_compare.py: S4M-2 runs as reference AND calibration (all differences must be 0); read-only, no solve
set -u
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0; unset GRB_LICENSE_FILE
cd $RM
$PY /mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019/scripts/s4n_c2_compare.py --repo $RM --ref results_project/s4m/s4m2/solves --cal results_project/s4m/s4m2/solves \
   --cal-tag s4m_A_ --builds results_project/s4m/s4m1/builds --ref-duals-integrated results_project/s4m/s4ms2/solves/s4m_A_integrated_rerun \
   --out-json /tmp/c2_selftest.json --out-md /tmp/c2_selftest.md 2>&1 | grep -v "PROJ\|Warning\|warn"
grep -E "CO|biomass" /tmp/c2_selftest.md | cut -c1-400
