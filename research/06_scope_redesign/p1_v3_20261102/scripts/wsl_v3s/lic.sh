#!/bin/bash
# V3 screening (instruction section 2 step 4; user authorisation item 3): scp the local licence to the instance /root/.gurobi/gurobi.lic and chmod 600.
# The licence is never read, printed, hashed or copied anywhere else; only existence, mode and byte size. Refused if the package check fails or a licence
# file is already present on the instance (never overwritten). Also copies the authorisation text (date, run count, specification only).
set -u
source /home/jin/v3s/ssh.sh
L=/home/jin/gurobi.lic; A=/home/jin/v3s/auth.txt; P=/root/autodl-tmp/v3_screen
[ -f "$L" ] || { echo "LOCAL LICENCE MISSING"; exit 2; }
[ -s "$A" ] || { echo "AUTH TEXT MISSING"; exit 2; }
grep -q "'" "$A" && { echo "AUTH TEXT HOLDS A SINGLE QUOTE"; exit 2; }
err=$(mktemp)
v3s_ssh "cd $P && sha256sum -c --quiet SHA256SUMS && echo 'package OK'" 2>>"$err" | grep -q "package OK" || { v3s_scrub "REFUSED: package check failed $(cat "$err")"; rm -f "$err"; exit 2; }
v3s_ssh 'mkdir -p /root/.gurobi && chmod 700 /root/.gurobi && [ ! -e /root/.gurobi/gurobi.lic ] && echo "remote: no licence yet"' 2>>"$err" | grep -q "no licence yet" || { v3s_scrub "REFUSED: remote licence present or ssh failed $(cat "$err")"; rm -f "$err"; exit 2; }
v3s_scp -q "$L" "root@$V3S_HOST:/root/.gurobi/gurobi.lic" 2>>"$err"; rc2=$?
v3s_scp -q "$A" "root@$V3S_HOST:/root/autodl-tmp/v3_screen_auth.txt" 2>>"$err"; rc3=$?
v3s_ssh "chmod 600 /root/.gurobi/gurobi.lic && stat -c 'remote licence: %A %s B %U' /root/.gurobi/gurobi.lic && stat -c 'remote /root/.gurobi: %A' /root/.gurobi && stat -c 'auth text: %s B' /root/autodl-tmp/v3_screen_auth.txt" 2>>"$err"; rc4=$?
echo "local licence size: $(stat -c %s "$L") B; scp_licence_exit=$rc2 scp_auth_exit=$rc3 chmod_stat_exit=$rc4 at $(TZ=Asia/Singapore date "+%F %T") SGT"
[ -s "$err" ] && v3s_scrub "STDERR: $(cat "$err")"; rm -f "$err"
