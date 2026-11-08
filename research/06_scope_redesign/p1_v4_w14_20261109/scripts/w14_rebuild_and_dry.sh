#!/bin/bash
# W14 section 2.1 / 3.2 (no solver): (1) rebuild the two networks at the package commit in the same worktree path (scripts/build_w14.sh rebuild_pkg) and compare the
# 2920x3h files byte by byte with the package networks (built at 59b128ea); (2) the dry run of the package in an unpacked copy with the default bash and with bash 4.2.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w14_20261109; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
echo "== rebuild at $(git -C /home/jin/wt_v4_w14 rev-parse HEAD) $(date -u +%FT%TZ)"
bash $W/scripts/build_w14.sh rebuild_pkg > $W/logs/build_rebuild_pkg.txt 2>&1; echo "REBUILD_EXIT:$?"
for f in integrated/integrated_2920_3h_unsolved.nc no_new_xb/no_new_xb_2920_3h_unsolved.nc integrated/integrated_365_24h_unsolved.nc no_new_xb/no_new_xb_365_24h_unsolved.nc; do
  a=$(sha256sum $MAIN/results_project/v4w14/builds/main/$f | cut -c1-64); b=$(sha256sum $MAIN/results_project/v4w14/builds/rebuild_pkg/$f | cut -c1-64)
  cmp -s $MAIN/results_project/v4w14/builds/main/$f $MAIN/results_project/v4w14/builds/rebuild_pkg/$f && s=BYTE_IDENTICAL || s=DIFFERENT
  echo "REBUILD_CMP:$f:$s:main=$a:rebuild=$b"
done
python3 - <<'P'
import json
a = json.load(open("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w14/builds/main/integrated/integrated_BUILD_RECEIPT.json"))
b = json.load(open("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w14/builds/rebuild_pkg/integrated/integrated_BUILD_RECEIPT.json"))
diff = sorted(k for k in set(a) | set(b) if json.dumps(a.get(k), sort_keys=True) != json.dumps(b.get(k), sort_keys=True))
print("REBUILD_RECEIPT_KEYS_DIFFERING:", diff, "code_sha", a.get("code_sha", "")[:8], "->", b.get("code_sha", "")[:8])
P
echo "== dry run (bash) $(date -u +%FT%TZ)"
bash $W/scripts/w14_dry.sh $W/hpc_package_v4 > $W/logs/dry_bash.txt 2>&1; echo "DRY_BASH_EXIT:$?"
echo "== dry run (bash 4.2) $(date -u +%FT%TZ)"
BASH_BIN=/home/jin/v3h/bash42/src/bash bash $W/scripts/w14_dry.sh $W/hpc_package_v4 > $W/logs/dry_bash42.txt 2>&1; echo "DRY_BASH42_EXIT:$?"
echo "ALL_DONE $(date -u +%FT%TZ)"
