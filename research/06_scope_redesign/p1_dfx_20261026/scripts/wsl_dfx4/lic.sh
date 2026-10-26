#!/bin/bash
# DFX phase 4 (authorised in the user's message of 2026-10-27, RUN_PLAN_DFX section 7 step 4): scp the local licence to the instance
# /root/.gurobi/gurobi.lic and chmod 600. The licence is never read, printed, hashed or copied anywhere else; only existence, mode and byte size.
# Refused if the package check fails or a licence file is already present on the instance (never overwritten). Also copies the authorisation text.
set -u
source /home/jin/dfx4/ssh.sh
L=/home/jin/gurobi.lic; A=/home/jin/dfx4/auth.txt
[ -f "$L" ] || { echo "LOCAL LICENCE MISSING"; exit 2; }
[ -s "$A" ] || { echo "AUTH TEXT MISSING"; exit 2; }
err=$(mktemp)
dfx_ssh 'cd /root/autodl-tmp/dfx_v8 && sha256sum -c --quiet SHA256SUMS && echo "package OK"' 2>>"$err" | grep -q "package OK" || { dfx_scrub "REFUSED: package check failed $(cat "$err")"; rm -f "$err"; exit 2; }
dfx_ssh 'mkdir -p /root/.gurobi && chmod 700 /root/.gurobi && [ ! -e /root/.gurobi/gurobi.lic ] && echo "remote: no licence yet"' 2>>"$err" | grep -q "no licence yet" || { dfx_scrub "REFUSED: remote licence present or ssh failed $(cat "$err")"; rm -f "$err"; exit 2; }
dfx_scp -q "$L" "root@$DFX_HOST:/root/.gurobi/gurobi.lic" 2>>"$err"; rc2=$?
dfx_scp -q "$A" "root@$DFX_HOST:/root/autodl-tmp/dfx_v8_auth.txt" 2>>"$err"; rc3=$?
dfx_ssh "chmod 600 /root/.gurobi/gurobi.lic && stat -c 'remote licence: %A %s B %U' /root/.gurobi/gurobi.lic && stat -c 'remote /root/.gurobi: %A' /root/.gurobi && stat -c 'auth text: %s B' /root/autodl-tmp/dfx_v8_auth.txt" 2>>"$err"; rc4=$?
echo "local licence size: $(stat -c %s "$L") B; scp_licence_exit=$rc2 scp_auth_exit=$rc3 chmod_stat_exit=$rc4 at $(TZ=Asia/Singapore date "+%F %T") SGT"
[ -s "$err" ] && dfx_scrub "STDERR: $(cat "$err")"; rm -f "$err"
