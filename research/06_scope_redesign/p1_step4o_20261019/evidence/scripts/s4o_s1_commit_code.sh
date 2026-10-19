#!/bin/bash
# S4O supplement 01 (S4O-2'): stage and commit the decision-121 code / config / registry / tests / package-script changes
set -euo pipefail
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
D=research/06_scope_redesign/p1_step4o_20261019
chmod 755 $D/cloud_package/*.sh $D/evidence/s4o_4/*.sh
git add configs/research/baseline.yaml scripts_project/s4o_1_data.py scripts_project/s4o_c1_precision.py scripts_project/d1_registry.py \
  research_inputs/registry_v5/DATA_REGISTRY.csv research_inputs/registry_v5/D1_EVIDENCE.json tests/research/test_s4o_2.py tests/research/test_s4c_5.py \
  tests/research/test_s3_gates.py $D/cloud_package $D/S4O_SUPPLEMENT_01.md $D/S4O_SUPPLEMENT_01_SHA256.txt $D/evidence/s4o_4/test_s4o4_scripts.sh \
  $D/evidence/s4o_4/test_s4o4_probe.sh $D/evidence/s4o_4/fake_s2_solve_probe.py
git add -f research_inputs/registry_v5/fragments/s4o_1.csv
git diff --cached --stat | tail -25
git commit -q -F - <<'EOF'
S4O supplement 01 S4O-2' (decision 121): production profile back to profile A formal_barrier (default research.solver.profile; reasons in the config comment and registry fragment s4o_1: BarConvTol 1e-5 lands near 3e-5 = 0.015-0.02 bn, same order as the 0.01 bn decision unit, and depends on the thread path); pypsa_eur_default kept as a registered non-production profile; package scripts: run_365x24h.sh default profile formal_barrier, default runs disconnected,integrated_nze, TimeLimit / wall 21,600 / 22,500 s, pilot integrated as the C1 reference (PILOT_INTEGRATED / PILOT_PRECISION, re-grade on a copy, PILOT_CONSISTENCY.json), TRUNCATE hook for the local end-to-end check; speed_probe.sh cap base 21,600 s; preflight message; s4o_c1_precision.regrade accepts the S4N pilot format; tests updated (test_s4o_2.py 8 passed)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
