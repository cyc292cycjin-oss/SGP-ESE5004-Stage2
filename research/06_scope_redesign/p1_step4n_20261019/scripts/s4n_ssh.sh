#!/bin/bash
# S4N: ssh to the AutoDL instance (source this file). Host and port only from the calling command line environment (S4N_HOST, S4N_PORT; never
# written to a file); separate hashed known_hosts in the session scratchpad; key by path (S4N_KEY, default ~/.ssh/id_ed25519; never copied).
: "${S4N_HOST:?}" "${S4N_PORT:?}"
[ ${#S4N_HOST} -gt 5 ] && [ ${#S4N_PORT} -gt 1 ] || { echo "empty host / port - refused"; exit 2; }
S4N_KEY=${S4N_KEY:-/home/jin/.ssh/id_ed25519}
KH=/mnt/c/Users/20122/AppData/Local/Temp/claude/D--ResearchWorkspaces/1fa8f672-a3bf-4ccd-aa5c-a7620da1e9a5/scratchpad/s4n_known_hosts
S4N_OPTS=(-o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=30 -o ServerAliveCountMax=6 -o StrictHostKeyChecking=accept-new
          -o UserKnownHostsFile=$KH -o HashKnownHosts=yes -o LogLevel=ERROR -o IdentitiesOnly=yes -i "$S4N_KEY")
s4n_ssh() { ssh "${S4N_OPTS[@]}" -p "$S4N_PORT" "root@$S4N_HOST" "$@"; }
s4n_scp() { scp "${S4N_OPTS[@]}" -P "$S4N_PORT" "$@"; }
s4n_rsync() { rsync -e "ssh ${S4N_OPTS[*]} -p $S4N_PORT" "$@"; }
