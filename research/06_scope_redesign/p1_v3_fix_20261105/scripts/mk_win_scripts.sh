#!/bin/bash
# Copy the V3 DIAG window entry (instruction 1.1: diagnosis scripts may be copied) into scripts/win/ for the V3.1 window recheck (section 5.1).
# Changes: worktree /home/jin/wt_v3_fix, run root results_project/v3fix, evidence + Gurobi ledger of this session (limit 6), authorisation text.
set -eu
SRC=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_diag_20261105/scripts
DST=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105/scripts/win
mkdir -p "$DST"
for f in diag_build.py common.sh build.sh probe.sh; do cp "$SRC/$f" "$DST/$f"; done
/home/jin/miniforge3/envs/pypsa-earth/bin/python - "$DST" <<'P'
import sys
from pathlib import Path
d = Path(sys.argv[1])
rep = {
    "diag_build.py": [('REPO = Path("/home/jin/wt_v3_diag")', 'REPO = Path("/home/jin/wt_v3_fix")'),
                      ('script="work/p1_v3_diag_20261105/scripts/diag_build.py"', 'script="work/p1_v3_fix_20261105/scripts/win/diag_build.py (copy of the V3 DIAG entry)"')],
    "common.sh": [("REPO=/home/jin/wt_v3_diag", "REPO=/home/jin/wt_v3_fix"),
                  ("WORK=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_diag_20261105", "WORK=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105"),
                  ("S=$WORK/scripts", "S=$WORK/scripts/win"),
                  ("results_project/v3diag", "results_project/v3fix"),
                  ("STATUS=$EV/DIAG_STATUS.txt", "STATUS=$EV/FIX_STATUS.txt"),
                  ("MAXCALLS=40", "MAXCALLS=6")],
    "build.sh": [('"V3 DIAG decision 194 $ID $F window', '"V3.1 FIX decision 195 window recheck $ID $F window')],
}
for f, pairs in rep.items():
    p = d / f; t = p.read_text()
    for a, b in pairs:
        if a not in t:
            raise SystemExit(f"{f}: pattern not found: {a}")
        t = t.replace(a, b)
    p.write_text(t)
print("patched", ", ".join(rep))
P
chmod 755 "$DST"/*.sh
grep -n -E 'wt_v3|v3diag|v3fix|MAXCALLS|STATUS=|S=' "$DST/common.sh" "$DST/diag_build.py" | cut -c1-160
