#!/bin/bash
# S4O-6: unpack the NZE export from the downloaded batch tarball next to the per-run full packages; check that the disconnected / diagnostic files in the
# batch tarball are identical to the per-run full packages downloaded earlier; top-level batch files (BATCH_REFERENCE, PILOT_CONSISTENCY, STATUS) from
# the light package -> top/. Read only on the downloaded archives.
set -u
TS=${1:?run timestamp}
C=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019/cloud_results/$TS; T=/home/jin/s4o_tmp/batch_unpack; rm -rf $T; mkdir -p $T
tar xzf $C/results_$TS.tar.gz -C $T
ls $T/export | tr '\n' ' '; echo
rm -rf $C/full/unpacked/integrated_nze; cp -a $T/export/integrated_nze $C/full/unpacked/
for r in disconnected disconnected_gap; do
  d=$(diff -rq $T/export/$r $C/full/unpacked/$r | wc -l); echo "batch tarball vs per-run package, $r: $d differing files"
done
mkdir -p $C/top; L=$C/unpacked/s4o_batch_light_$TS
for f in BATCH_REFERENCE.json PILOT_CONSISTENCY.json STATUS.txt; do cp $T/export/$f $C/top/ 2>/dev/null || cp $L/$f $C/top/ 2>/dev/null; done
cp -a $T/export/pilot_integrated $C/top/ 2>/dev/null
ls $C/top
rm -rf $T
