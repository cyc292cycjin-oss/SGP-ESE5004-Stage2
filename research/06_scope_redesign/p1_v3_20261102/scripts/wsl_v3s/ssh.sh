#!/bin/bash
# V3 screening: ssh helpers (source this file). Host and port only from the calling command line environment (V3S_HOST, V3S_PORT; never written to a
# file); hashed known_hosts in ~/.ssh/v3s_known_hosts (accept-new only for a new host / port pair; AutoDL images share a host key, so the instance is
# identified by its own checks, not by the key); key by path (never copied). Every captured message is scrubbed of host / port before it is printed.
: "${V3S_HOST:?}" "${V3S_PORT:?}"
[ ${#V3S_HOST} -gt 5 ] && [ ${#V3S_PORT} -gt 3 ] || { echo "empty host / port - refused"; exit 2; }
V3S_KEY=/home/jin/.ssh/id_ed25519
KH=/home/jin/.ssh/v3s_known_hosts
V3S_OPTS=(-o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=30 -o ServerAliveCountMax=6 -o StrictHostKeyChecking=accept-new
          -o UserKnownHostsFile=$KH -o HashKnownHosts=yes -o LogLevel=ERROR -o IdentitiesOnly=yes -i "$V3S_KEY")
v3s_ssh() { ssh "${V3S_OPTS[@]}" -p "$V3S_PORT" "root@$V3S_HOST" "$@"; }
v3s_scp() { scp "${V3S_OPTS[@]}" -P "$V3S_PORT" "$@"; }
v3s_scrub() { local m="$1"; m=${m//"$V3S_HOST"/<HOST>}; m=${m//"$V3S_PORT"/<PORT>}; printf '%s\n' "$m"; }
# run a local script file on the instance (ssh bash -s < file); stdout scrubbed as well (defensive), stderr scrubbed
v3s_run() { local f="$1"; shift; local err out; err=$(mktemp); out=$(mktemp); v3s_ssh bash -s -- "$@" < "$f" > "$out" 2>"$err"; local rc=$?
  v3s_scrub "$(cat "$out")"; echo "SSH_EXIT:$rc"; [ -s "$err" ] && v3s_scrub "STDERR: $(cat "$err")"; rm -f "$err" "$out"; return $rc; }
