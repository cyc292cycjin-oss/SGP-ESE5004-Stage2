#!/bin/bash
# S4O-6: ssh helpers for the AutoDL instance (source this file). Host and port only from the calling command line environment (S4O_HOST, S4O_PORT;
# never written to a file); separate hashed known_hosts in this session's scratchpad; key by path (never copied).
: "${S4O_HOST:?}" "${S4O_PORT:?}"
[ ${#S4O_HOST} -gt 5 ] && [ ${#S4O_PORT} -gt 1 ] || { echo "empty host / port - refused"; exit 2; }
S4O_KEY=${S4O_KEY:-/home/jin/.ssh/id_ed25519}
KH=/mnt/c/Users/20122/AppData/Local/Temp/claude/D--ResearchWorkspaces/1388eed3-1835-43dd-95c3-52dc53c6afe3/scratchpad/s4o_known_hosts
S4O_OPTS=(-o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=30 -o ServerAliveCountMax=6 -o StrictHostKeyChecking=accept-new
          -o UserKnownHostsFile=$KH -o HashKnownHosts=yes -o LogLevel=ERROR -o IdentitiesOnly=yes -i "$S4O_KEY")
s4o_ssh() { ssh "${S4O_OPTS[@]}" -p "$S4O_PORT" "root@$S4O_HOST" "$@"; }
s4o_scp() { scp "${S4O_OPTS[@]}" -P "$S4O_PORT" "$@"; }
s4o_rsync() { rsync -e "ssh ${S4O_OPTS[*]} -p $S4O_PORT" "$@"; }
