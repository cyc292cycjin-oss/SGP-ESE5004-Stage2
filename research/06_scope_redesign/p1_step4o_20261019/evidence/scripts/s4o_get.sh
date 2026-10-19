#!/bin/bash
# S4O-6 point 6 (local): download, ONE stream at a time, the light package and then the full batch results tarball; sha256sum -c locally; unpack the
# light package; licence-string scan. Host and port from the calling command line environment only.
# usage: S4O_HOST=.. S4O_PORT=.. bash s4o_get.sh <run timestamp> [light|full|both]
set -u
source /home/jin/s4o_ssh.sh
TS=${1:?run timestamp}; WHAT=${2:-both}
L=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019/cloud_results/$TS; mkdir -p $L
if [ "$WHAT" != full ]; then
  t0=$(date +%s)
  s4o_rsync -a --partial "root@$S4O_HOST:/root/autodl-tmp/s4o_post/s4o_batch_light_$TS.tar.gz" "root@$S4O_HOST:/root/autodl-tmp/s4o_post/s4o_batch_light_$TS.tar.gz.sha256" \
    "root@$S4O_HOST:/root/autodl-tmp/s4o_post/BUNDLE_LISTING.txt" "root@$S4O_HOST:/root/autodl-tmp/s4o_post/results_$TS.tar.gz.sha256" $L/ && echo "LIGHT_DOWNLOAD_SECONDS:$(( $(date +%s) - t0 ))"
  ( cd $L && sha256sum -c s4o_batch_light_$TS.tar.gz.sha256 ) && mkdir -p $L/unpacked && tar xzf $L/s4o_batch_light_$TS.tar.gz -C $L/unpacked
  H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $L/unpacked); [ -z "$H" ] && echo "LICENCE_SCAN_LIGHT: no hit" || { echo "LICENCE STRING FOUND:"; echo "$H"; }
fi
if [ "$WHAT" != light ]; then
  t1=$(date +%s)
  s4o_rsync -a --partial "root@$S4O_HOST:/root/autodl-tmp/s4o_cloud/runs/$TS/results_$TS.tar.gz" $L/ && echo "FULL_DOWNLOAD_SECONDS:$(( $(date +%s) - t1 ))"
  ( cd $L && sha256sum -c results_$TS.tar.gz.sha256 && ls -l results_$TS.tar.gz | awk '{print "FULL_BYTES", $5}' )
  H=$(tar xzOf $L/results_$TS.tar.gz 2>/dev/null | grep -aciE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)"); echo "LICENCE_SCAN_FULL_STREAM_HITS: $H"
fi
