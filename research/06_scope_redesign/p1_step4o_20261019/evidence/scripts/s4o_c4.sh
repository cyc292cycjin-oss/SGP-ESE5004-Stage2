#!/bin/bash
# S4O-6 point 3 (user authorisation: licence handled as in L23): licence file to the instance by scp only (never read, printed or copied elsewhere);
# permission 600; integrity by hash comparison without printing the hash. Run only after the package checks are all OK.
# Host and port from the calling command line environment only.
set -u
source /home/jin/s4o_ssh.sh
LIC=/home/jin/gurobi.lic
[ -s "$LIC" ] || { echo "LOCAL LICENCE FILE MISSING"; exit 1; }
s4o_ssh 'mkdir -p /root/.gurobi && chmod 700 /root/.gurobi' || exit 1
s4o_scp -q "$LIC" "root@$S4O_HOST:/root/.gurobi/gurobi.lic" || { echo "SCP FAILED"; exit 1; }
s4o_ssh 'chmod 600 /root/.gurobi/gurobi.lic && stat -c "remote: mode %a owner %U size %s bytes" /root/.gurobi/gurobi.lic && stat -c "dir: mode %a" /root/.gurobi && ls /root/.gurobi | wc -l'
lh=$(sha256sum "$LIC" | cut -d' ' -f1); rh=$(s4o_ssh 'sha256sum /root/.gurobi/gurobi.lic | cut -d" " -f1')
[ -n "$lh" ] && [ "$lh" = "$rh" ] && echo "LICENCE_TRANSFER_INTEGRITY: local and remote identical (hash not printed)" || echo "LICENCE_TRANSFER_INTEGRITY: MISMATCH"
date '+LICENCE_UPLOADED_AT %F %T'
