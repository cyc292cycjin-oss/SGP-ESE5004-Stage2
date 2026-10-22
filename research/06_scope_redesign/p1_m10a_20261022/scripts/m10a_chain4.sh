#!/bin/bash
# M10A chain 4: evidence copy -> commit 1 (fixes + tests + RUN_PLAN v3) -> package v4 -> variants under the thread budget -> dry run pre -> dry run post
set -u
E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10a_20261022/evidence; mkdir -p $E/tests $E/b3b4
cp /home/jin/m10a_evidence/TESTS_*.log $E/tests/
cp /home/jin/m10a_b3/B3B4.log /home/jin/m10a_b3/B4_ARRAY_RANGES.json /home/jin/m10a_b3/alloc.err /home/jin/m10a_b3/v6.err /home/jin/m10a_b3/pack.err /home/jin/m10a_b3/owen.err /home/jin/m10a_b3/V6_ACCEPTANCE.json $E/b3b4/ 2>/dev/null
cp /home/jin/m10a_b3/owen/RHS_AUDIT.json $E/b3b4/OWEN_RHS_AUDIT_S4N_duals.json 2>/dev/null; cp /home/jin/m10a_b3/alloc/ALLOCATION.json $E/b3b4/ALLOCATION_S4N.json 2>/dev/null
for f in $E/b3b4/*.err; do grep -vE 'licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic' "$f" > "$f.scrubbed" && mv "$f.scrubbed" "$f"; done
echo "===== commit 1 ====="
bash /home/jin/m10a_commit.sh /home/jin/m10a_msg1.txt research/06_scope_redesign/p1_m10p_20261022/RUN_PLAN.md research/06_scope_redesign/p1_m10p_20261022/cloud_package scripts_project/m10_batch3_summary.py tests/research/fixtures/m10p_fake_pipeline.py tests/research/test_m10p_batch3.py || { echo "COMMIT1_FAILED"; exit 1; }
echo "===== package v4 ====="
bash /home/jin/m10a_package.sh || { echo "PACKAGE_FAILED"; exit 1; }
echo "===== variants under the thread budget ====="
bash /home/jin/m10a_varcheck.sh || { echo "VARCHECK_FAILED"; exit 1; }
echo "===== dry run pre ====="
STEP=pre bash /home/jin/m10a_dryrun.sh || { echo "DRY_PRE_FAILED"; exit 1; }
echo "===== dry run post ====="
STEP=post bash /home/jin/m10a_dryrun.sh || { echo "DRY_POST_FAILED"; exit 1; }
echo CHAIN4_DONE
