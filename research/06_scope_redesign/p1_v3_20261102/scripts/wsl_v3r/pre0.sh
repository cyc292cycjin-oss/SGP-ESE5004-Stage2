#!/bin/bash
# V3 supplement 07 section 2.2, before any cloud contact (local, read-only; V3_SCREEN_AUTODL_INSTRUCTION.md section 0 applied to the rerun):
# instruction hashes; the local part done (report, no open stop); package = registered values, sha256sum -c, COMMIT pushed; predictions committed before
# any solve of the new networks; no local Gurobi / solve process; local licence exists (stat only, never read); auth text without a single quote.
set -u
WORK=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102; W=/home/jin/wt_v3_20261102; P=$WORK/screen_package_v3_dmax
cd $WORK; sha256sum -c V3_SCREEN_INSTRUCTION_SHA256.txt V3_SCREEN_UNATTENDED_SHA256.txt; sha256sum V3_REVIEW_DECISIONS_EVDIAG.md | cut -c1-16
[ -f V3_REPORT_SUPPLEMENT07.md ] && echo "report of the local part present: $(grep -c '' V3_REPORT_SUPPLEMENT07.md) lines"
echo "== package"; cd $P
echo "SHA256SUMS $(sha256sum SHA256SUMS | cut -c1-64)"; echo "MANIFEST   $(sha256sum PACKAGE_MANIFEST.json | cut -c1-64)"
[ "$(sha256sum SHA256SUMS | cut -c1-64)" = cce1444c056e5b36fa39b7304d6c8bca834a3dfa3cd4dd5f49a9c713f821a24b ] && [ "$(sha256sum PACKAGE_MANIFEST.json | cut -c1-64)" = 4a46fba96d3b0c2e19870d536ed18bf717246dff7ec159cb253c258fad66b031 ] && echo "= report values" || echo "PACKAGE HASH MISMATCH"
sha256sum -c --quiet SHA256SUMS && echo "sha256sum -c: all $(wc -l < SHA256SUMS) OK" || echo "CHECKSUM MISMATCH"
C=$(cat COMMIT); echo "COMMIT $C"
cd $W; git fetch -q origin codex/v3-20261102 2>/dev/null; git merge-base --is-ancestor $C origin/codex/v3-20261102 && echo "COMMIT is on origin/codex/v3-20261102 ($(git rev-parse --short origin/codex/v3-20261102))" || echo "COMMIT NOT PUSHED"
echo "== predictions before any solve: section 23.3 in $(git log --format=%h -1 --diff-filter=AM -S '### 23.3' -- research/06_scope_redesign/p1_v3_20261102/RUN_PLAN_V3.md) ($(git log --format=%cI -1 -S '### 23.3' -- research/06_scope_redesign/p1_v3_20261102/RUN_PLAN_V3.md)); path check started $(head -1 /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/path_check7/STATUS.txt | cut -d: -f2-4)"
echo "== local processes: $(ps -eo args= | grep -cE '[s]2_solve\.py|[g]urobi|[p]ytest|[r]un_dfx')"
L=${GRB_LICENSE_FILE:-/home/jin/gurobi.lic}; echo "== local licence: GRB_LICENSE_FILE=${GRB_LICENSE_FILE:-unset in this shell}; $L $(stat -c '%A %s B' $L 2>/dev/null || echo MISSING)"
grep -q "'" /home/jin/v3r/auth.txt && echo "AUTH TEXT HOLDS A SINGLE QUOTE" || echo "auth text: $(wc -c < /home/jin/v3r/auth.txt) B, no single quote"
echo "== ssh key: $(stat -c '%A' /home/jin/.ssh/id_ed25519) $(ssh-keygen -lf /home/jin/.ssh/id_ed25519.pub | awk '{print $1, $3}' | cut -c1-30)"
