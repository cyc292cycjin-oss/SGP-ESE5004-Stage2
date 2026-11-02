#!/bin/bash
# read-only: bare TCP connect from WSL to the Windows host (gateway) on the local proxy port; no data sent, nothing changed
G=$(ip route | awk '/^default/{print $3; exit}')
for p in 7897; do
  if timeout 6 bash -c "exec 3<>/dev/tcp/$G/$p" 2>/dev/null; then echo "tcp gateway:$p OPEN"; else echo "tcp gateway:$p FAILED rc=$?"; fi
done
ping -c 2 -W 2 "$G" 2>&1 | tail -2 | cut -c1-90
