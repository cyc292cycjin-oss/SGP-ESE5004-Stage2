#!/bin/bash
# V3 screening rerun (supplement 07): copy the watchdog script to the instance (own folder, outside the package and the run folder); prints the SHA256 at both ends.
set -u
source /home/jin/v3r/ssh.sh
F=/home/jin/v3r/v3s_watchdog.sh; W=/root/autodl-tmp/v3_watchdog_dmax
err=$(mktemp)
v3s_ssh "mkdir -p $W" 2>>"$err"
v3s_scp -q "$F" "root@$V3S_HOST:$W/v3s_watchdog.sh" 2>>"$err"; echo "scp exit=$?"
echo "local  $(sha256sum "$F" | cut -c1-16)"
echo "remote $(v3s_ssh "sha256sum $W/v3s_watchdog.sh" 2>>"$err" | cut -c1-16)"
[ -s "$err" ] && v3s_scrub "STDERR: $(cat "$err")"; rm -f "$err"
