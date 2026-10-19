#!/bin/bash
# copy the two instance-side launchers (no host / port / licence in them) to /root/autodl-tmp. Host and port from the calling command line environment.
set -u
source /home/jin/s4n_ssh.sh
s4n_scp -q /home/jin/s4n_r_probe_launch.sh /home/jin/s4n_r_pilot_launch.sh "root@$S4N_HOST:/root/autodl-tmp/" || { echo "SCP FAILED"; exit 1; }
s4n_ssh 'cd /root/autodl-tmp && mv s4n_r_probe_launch.sh s4n_probe_launch.sh && mv s4n_r_pilot_launch.sh s4n_pilot_launch.sh && chmod 755 s4n_probe_launch.sh s4n_pilot_launch.sh && bash -n s4n_probe_launch.sh && bash -n s4n_pilot_launch.sh && ls -la s4n_*launch.sh | awk "{print \$1, \$5, \$NF}"'
