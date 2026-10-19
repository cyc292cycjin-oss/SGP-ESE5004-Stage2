#!/bin/bash
# S4O-6 point 1: key login and the read-only instance checks. Host and port from the calling command line environment only.
set -u
source /home/jin/s4o_ssh.sh
s4o_ssh 'echo CONNECTED_AS_$(whoami)' || { echo "SSH_LOGIN_FAILED (key /home/jin/.ssh/id_ed25519)"; exit 1; }
s4o_ssh bash -s < /home/jin/s4o_r_check.sh
