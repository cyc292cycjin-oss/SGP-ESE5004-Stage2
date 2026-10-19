#!/bin/bash
# S4O-6 point 6 (local): pack the given finished runs on the instance (s4o_r_runpack.sh) and download each per-run full package ONE stream at a
# time (rsync --partial, never interrupted), sha256sum -c locally, licence scan of the unpacked text files. Host and port from the environment only.
# usage: S4O_HOST=.. S4O_PORT=.. bash s4o_get_runs.sh "<run> [<run> ...]"
set -u
source /home/jin/s4o_ssh.sh
RUNS=${1:?runs}
TS=$(s4o_ssh "basename \$(ls -d /root/autodl-tmp/s4o_cloud/runs/*/ | tail -1)")
L=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019/cloud_results/$TS; mkdir -p $L/full
s4o_ssh "RUNS='$RUNS' bash -s" < /home/jin/s4o_r_runpack.sh
for r in $RUNS; do
  t0=$(date +%s)
  s4o_rsync -a --partial "root@$S4O_HOST:/root/autodl-tmp/s4o_post/full_${r}_$TS.tar.gz" "root@$S4O_HOST:/root/autodl-tmp/s4o_post/full_${r}_$TS.tar.gz.sha256" $L/full/ \
    && echo "DOWNLOAD_${r}_SECONDS:$(( $(date +%s) - t0 ))" || echo "DOWNLOAD_${r}_FAILED"
  ( cd $L/full && sha256sum -c full_${r}_$TS.tar.gz.sha256 )
  mkdir -p $L/full/unpacked && tar xzf $L/full/full_${r}_$TS.tar.gz -C $L/full/unpacked
  H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $L/full/unpacked/$r); [ -z "$H" ] && echo "LICENCE_SCAN_$r: no hit" || { echo "LICENCE STRING FOUND:"; echo "$H"; }
done
