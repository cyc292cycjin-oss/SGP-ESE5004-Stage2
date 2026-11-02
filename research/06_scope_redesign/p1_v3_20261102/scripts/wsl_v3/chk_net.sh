#!/bin/bash
# read-only: name resolution and a bare TCP connect (no data sent, no licence read), nothing changed
T=token.gurobi.com
echo "hosts: $(getent hosts $T | head -2 | tr -s ' ' | tr '\n' ';')"
for h in $T github.com 1.1.1.1; do
  if timeout 12 bash -c "exec 3<>/dev/tcp/$h/443" 2>/dev/null; then echo "tcp $h:443 OPEN"; else echo "tcp $h:443 FAILED rc=$?"; fi
done
echo "route: $(ip route | head -2 | tr '\n' ';')"
echo "iface: $(ip -br addr | grep -v '^lo' | head -3 | tr -s ' ' | tr '\n' ';')"
echo "proxy vars: $(env | grep -ic proxy)"
uname -r; wslinfo --networking-mode 2>/dev/null
