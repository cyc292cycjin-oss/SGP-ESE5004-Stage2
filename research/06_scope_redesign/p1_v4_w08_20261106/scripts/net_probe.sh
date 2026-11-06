#!/bin/bash
# W08: bare TCP connects from WSL (no data sent, no licence read)
for h in token.gurobi.com github.com 1.1.1.1; do
  if timeout 10 bash -c "exec 3<>/dev/tcp/$h/443" 2>/dev/null; then echo "$h OK"; else echo "$h FAIL"; fi
done
