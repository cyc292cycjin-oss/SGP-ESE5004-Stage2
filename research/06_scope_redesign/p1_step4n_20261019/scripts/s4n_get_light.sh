#!/bin/bash
# S4N-4 light retrieval (user 2026-10-19 ~16:25 SGT): single scp of the light bundle + sha256 + POST_STATUS from the instance; local sha256sum -c,
# unpack, licence scan. The full results bundle stays on the instance data disk. Host / port from the calling environment only.
set -u
source /home/jin/s4n_ssh.sh
TS=20261019T072454Z_5125; T=/root/autodl-tmp/s4n_tools
DST=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019/cloud_results/$TS; mkdir -p $DST
s4n_ssh "grep -q '^POST_DONE' $T/POST_STATUS.txt" || { echo "POST NOT DONE"; exit 1; }
t0=$(date +%s)
s4n_scp -q "root@$S4N_HOST:$T/s4n_pilot_light_$TS.tar.gz" "root@$S4N_HOST:$T/s4n_pilot_light_$TS.tar.gz.sha256" "root@$S4N_HOST:$T/POST_STATUS.txt" $DST/ || { echo "SCP FAILED"; exit 1; }
echo "DOWNLOAD_SECONDS:$(( $(date +%s) - t0 )) bytes:$(stat -c %s $DST/s4n_pilot_light_$TS.tar.gz)"
cd $DST && sha256sum -c s4n_pilot_light_$TS.tar.gz.sha256 && echo "LOCAL_SHA256_OK"
rm -rf $DST/unpacked && mkdir -p $DST/unpacked && tar xzf $DST/s4n_pilot_light_$TS.tar.gz -C $DST/unpacked && echo "UNPACKED: $(find $DST/unpacked -type f | wc -l) files, $(du -sh $DST/unpacked | cut -f1)"
H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $DST/unpacked $DST/POST_STATUS.txt 2>/dev/null)
[ -z "$H" ] && echo "LICENCE_SCAN: no licence string in the light bundle" || { echo "LICENCE STRING FOUND - stop:"; echo "$H"; exit 3; }
cat $DST/POST_STATUS.txt
