#!/bin/bash
# DFX phase 4: run one local script file on the instance. Usage: wsl env DFX_HOST=.. DFX_PORT=.. bash /home/jin/dfx4/run.sh <remote_script> [args]
set -u
source /home/jin/dfx4/ssh.sh
dfx_run "$@"
