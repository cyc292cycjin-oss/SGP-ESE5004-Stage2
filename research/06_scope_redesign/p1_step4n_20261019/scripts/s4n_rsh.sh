#!/bin/bash
# run ONE read-only command (argv, no "$" needed) on the instance. Host and port from the calling command line environment only.
source /home/jin/s4n_ssh.sh
s4n_ssh "$*"
