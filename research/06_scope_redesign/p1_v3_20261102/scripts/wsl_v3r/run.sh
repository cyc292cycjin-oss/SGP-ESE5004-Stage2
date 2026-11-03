#!/bin/bash
# V3 screening rerun (supplement 07): run one local script file on the instance. Usage: wsl env V3S_HOST=.. V3S_PORT=.. bash /home/jin/v3r/run.sh <remote_script> [args]
set -u
source /home/jin/v3r/ssh.sh
v3s_run "$@"
