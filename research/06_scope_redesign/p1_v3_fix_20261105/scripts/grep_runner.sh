#!/bin/bash
# Which python scripts does the formal runner call? Read-only.
set -u
cd /home/jin/wt_v3_fix
git ls-files | grep -E '(^|/)run_batch4\.sh$|hpc_v3/|(^|/)hpc/|preflight\.sh$|pack_results\.sh$' | head -40
R=$(git ls-files | grep -E '(^|/)run_batch4\.sh$' | head -1)
echo "RUNNER=$R"
grep -n -o -E '[A-Za-z0-9_/]+\.py[^"]{0,60}' "$R" | sort -t: -k2 -u | cut -c1-160 | head -80
