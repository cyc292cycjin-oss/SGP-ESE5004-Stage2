#!/bin/bash
# B4P commits 1-3 (per sub-step): 1 split + A3.1; 2 A3.2 + A3.3; 3 batch-4 runner / plan / package / drill / tests. Run only after the tests pass.
set -u
cd /home/jin/wt_b4p_20261026 || exit 1
[ "$(git branch --show-current)" = codex/b4-prep-20261026 ] || { echo wrong branch; exit 2; }
git add scripts_project/s2_solve.py scripts_project/b4_split_solve.py tests/research/test_b4p_split.py
git commit -q -F /home/jin/b4p/msg1.txt && echo "C1 $(git rev-parse --short HEAD)"
git add research/06_scope_redesign/p1_m10p_20261022/cloud_package/run_batch3.sh research/06_scope_redesign/p1_m10p_20261022/cloud_package/env/install_env.sh tests/research/test_b4p_paths.py tests/research/test_b4p_install_env.py
git commit -q -F /home/jin/b4p/msg2.txt && echo "C2 $(git rev-parse --short HEAD)"
git add scripts_project/b4_batch4.py research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/run_batch4.sh research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/preflight.sh \
        research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/make_package.sh research/06_scope_redesign/p1_b4p_20261026/scripts/drill_b4.sh research/06_scope_redesign/p1_b4p_20261026/RUN_PLAN_B4.md \
        tests/research/fixtures/b4p_fake_pipeline.py tests/research/test_b4p_batch4.py
chmod 755 research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/*.sh research/06_scope_redesign/p1_b4p_20261026/scripts/drill_b4.sh; git add -u research/06_scope_redesign/p1_b4p_20261026
git commit -q -F /home/jin/b4p/msg3.txt && echo "C3 $(git rev-parse --short HEAD)"
git status --porcelain --untracked-files=no | wc -l; git log --oneline -4
