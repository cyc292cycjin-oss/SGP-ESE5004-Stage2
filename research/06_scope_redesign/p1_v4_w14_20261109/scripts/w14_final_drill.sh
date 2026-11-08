#!/bin/bash
# W14 sections 2.1 / 3.2 on the DELIVERED package (package commit = HEAD): (1) network rebuild at the package commit in the same worktree path, byte comparison with the
# package networks; (2) dry run in an unpacked copy with bash and with bash 4.2 (no solver); (3) the smoke job drill in an unpacked copy (the 2 authorised solves;
# scripts/w14_smoke_drill.sh: token-server TCP check and licence-file mode check before, serial, no retry). Strictly one after the other (no solve beside a build).
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w14_20261109; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; L=$W/logs/final_drill.txt
C=$(git -C /home/jin/wt_v4_w14 rev-parse HEAD); [ "$C" = "$(cat $W/hpc_package_v4/COMMIT)" ] || { echo "REFUSED: worktree HEAD $C is not the package COMMIT" | tee $L; exit 2; }
echo "== rebuild at $C $(date -u +%FT%TZ)" > $L
bash $W/scripts/build_w14.sh rebuild_pkg_${C:0:8} > $W/logs/build_rebuild_pkg_${C:0:8}.txt 2>&1; echo "REBUILD_EXIT:$?" >> $L
for f in integrated/integrated_2920_3h_unsolved.nc no_new_xb/no_new_xb_2920_3h_unsolved.nc integrated/integrated_365_24h_unsolved.nc no_new_xb/no_new_xb_365_24h_unsolved.nc; do
  cmp -s $MAIN/results_project/v4w14/builds/main/$f $MAIN/results_project/v4w14/builds/rebuild_pkg_${C:0:8}/$f && s=BYTE_IDENTICAL || s=DIFFERENT
  echo "REBUILD_CMP:$f:$s:$(sha256sum $MAIN/results_project/v4w14/builds/rebuild_pkg_${C:0:8}/$f | cut -c1-64)" >> $L
done
cmp -s $MAIN/results_project/v4w14/builds/main/integrated/integrated_2920_3h_unsolved.nc $W/hpc_package_v4/networks/integrated_2920_3h_unsolved.nc && echo "PACKAGE_F1_NETWORK=BUILD_MAIN:BYTE_IDENTICAL" >> $L
echo "== dry run (bash) $(date -u +%FT%TZ)" >> $L
bash $W/scripts/w14_dry.sh $W/hpc_package_v4 > $W/logs/dry_bash.txt 2>&1; echo "DRY_BASH_EXIT:$?" >> $L
echo "== dry run (bash 4.2) $(date -u +%FT%TZ)" >> $L
BASH_BIN=/home/jin/v3h/bash42/src/bash bash $W/scripts/w14_dry.sh $W/hpc_package_v4 > $W/logs/dry_bash42.txt 2>&1; echo "DRY_BASH42_EXIT:$?" >> $L
echo "== smoke drill $(date -u +%FT%TZ)" >> $L
bash $W/scripts/w14_smoke_drill.sh $W/hpc_package_v4 --confirmed "$(date -u +%FT%TZ)" > $W/logs/smoke_drill.txt 2>&1; echo "SMOKE_DRILL_EXIT:$?" >> $L
echo "ALL_DONE $(date -u +%FT%TZ)" >> $L
