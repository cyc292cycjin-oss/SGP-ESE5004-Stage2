#!/bin/bash
# The first F1_M01 build finished (SPLIT_BUILD.json, problem.lp) but its build.sh was edited while running: bash re-read the shifted file and
# re-executed a redirection that truncated p1.err / p1.log (time statistics lost). Kept as F1_M01_x1 with its receipt and RESOURCE.jsonl;
# its problem.lp (a duplicate of the rebuild) is removed; M01 is rebuilt by months.sh.
set -u
. "$(dirname "$0")/common.sh"
X=$RUNROOT/F1_M01_x1
mv "$RUNROOT/F1_M01" "$X" || exit 2
sha=$(sha256sum "$X/split/problem.lp" | cut -c1-64); sz=$(stat -c %s "$X/split/problem.lp")
pk=$("$PY" -c "import json; print(round(max(json.loads(l)['peak'] for l in open('$X/RESOURCE.jsonl'))/2**30, 2))")
rm -f "$X/split/problem.lp"
mkdir -p "$EV/runs/F1_M01_x1"; cp "$X/DIAG_WINDOW.json" "$X/split/SPLIT_BUILD.json" "$EV/runs/F1_M01_x1/"
log "SET_ASIDE:F1_M01 -> F1_M01_x1 (build complete; build.sh edited while running truncated p1.err / p1.log); lp_bytes=$sz lp_sha256=$sha sampler_peak_gib=$pk; problem.lp removed:$(now)"
