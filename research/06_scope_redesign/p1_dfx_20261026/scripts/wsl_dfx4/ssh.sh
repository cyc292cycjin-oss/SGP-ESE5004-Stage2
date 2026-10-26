#!/bin/bash
# DFX phase 4: ssh helpers (source this file). Host and port only from the calling command line environment (DFX_HOST, DFX_PORT; never written to a
# file); hashed known_hosts in ~/.ssh/dfx4_known_hosts (seeded from the hashed M10S1 record of the same instance <INSTANCE>; accept-new only for a new
# host / port pair); key by path (never copied). Every captured message is scrubbed of host / port before it is printed or logged.
: "${DFX_HOST:?}" "${DFX_PORT:?}"
[ ${#DFX_HOST} -gt 5 ] && [ ${#DFX_PORT} -gt 3 ] || { echo "empty host / port - refused"; exit 2; }
DFX_KEY=/home/jin/.ssh/id_ed25519
KH=/home/jin/.ssh/dfx4_known_hosts
[ -e "$KH" ] || { cp /home/jin/.ssh/m10s1_known_hosts_src "$KH" 2>/dev/null; chmod 600 "$KH" 2>/dev/null; }
DFX_OPTS=(-o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=30 -o ServerAliveCountMax=6 -o StrictHostKeyChecking=accept-new
          -o UserKnownHostsFile=$KH -o HashKnownHosts=yes -o LogLevel=ERROR -o IdentitiesOnly=yes -i "$DFX_KEY")
dfx_ssh() { ssh "${DFX_OPTS[@]}" -p "$DFX_PORT" "root@$DFX_HOST" "$@"; }
dfx_scp() { scp "${DFX_OPTS[@]}" -P "$DFX_PORT" "$@"; }
dfx_scrub() { local m="$1"; m=${m//"$DFX_HOST"/<HOST>}; m=${m//"$DFX_PORT"/<PORT>}; printf '%s\n' "$m"; }
# run a local script file on the instance (ssh bash -s < file); stdout scrubbed as well (defensive), stderr scrubbed
dfx_run() { local f="$1"; shift; local err out; err=$(mktemp); out=$(mktemp); dfx_ssh bash -s -- "$@" < "$f" > "$out" 2>"$err"; local rc=$?
  dfx_scrub "$(cat "$out")"; echo "SSH_EXIT:$rc"; [ -s "$err" ] && dfx_scrub "STDERR: $(cat "$err")"; rm -f "$err" "$out"; return $rc; }
