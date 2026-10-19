#!/bin/bash
# measure the download speed instance -> local with one package file (24 MB probe network); the copy is deleted afterwards. Host / port from the environment.
set -u
source /home/jin/s4n_ssh.sh
T=$(mktemp -d)
t0=$(date +%s.%N)
s4n_scp -q "root@$S4N_HOST:/root/autodl-tmp/s4m_cloud/networks/integrated_56_3h_probe_unsolved.nc" $T/ || echo "SCP_FAILED"
t1=$(date +%s.%N)
b=$(stat -c %s $T/integrated_56_3h_probe_unsolved.nc 2>/dev/null || echo 0)
awk -v b=$b -v a=$t0 -v c=$t1 'BEGIN {printf "DOWNLOAD %d bytes in %.1f s = %.2f MB/s\n", b, c-a, b/(c-a)/1e6}'
rm -rf $T
