#!/bin/bash
# S4N-2 point 1: connect (key login) and run the read-only instance checks. Host and port from the calling command line environment only.
set -u
source /home/jin/s4n_ssh.sh
s4n_ssh 'echo CONNECTED_AS_$(whoami)' || { echo "SSH_LOGIN_FAILED (key /home/jin/.ssh/id_ed25519)"; exit 1; }
s4n_ssh bash -s < /home/jin/s4n_r_c1.sh
