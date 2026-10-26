#!/bin/bash
# DFX v3 P6 background: do the key-name literals already exist in the repository history before this branch? Counts only; the pattern comes from the
# pattern file outside the repository (line key=...).
cd /home/jin/wt_dfx_v3_20261026 || exit 1
PF=${LEAK_PATTERN_FILE:-/home/jin/.dfx_leak_patterns}; P=$(grep "^key=" "$PF" | cut -d= -f2-)
echo "tracked files at base 55ab07c0 containing a key-name literal: $(git grep -l -E "$P" 55ab07c0 -- . | wc -l)"
git grep -l -E "$P" 55ab07c0 -- . | sed "s/^55ab07c0://" | head -12
