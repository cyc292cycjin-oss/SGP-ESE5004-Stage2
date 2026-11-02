#!/bin/bash
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
$PY /home/jin/v3/fix10.py && $PY /home/jin/v3/patch_p3.py || exit 1
cd /home/jin/wt_v3_20261102
grep -c "from v3_layers import ensure_liquid_bus" scripts_project/s2_layers.py
for f in s2_layers s3_layers s4c_layers s2_network m08a_layers m08a_variants s4d_ledger m12_allocation v3_layers v3_ev v5/v5_gates v5/gates_v6 scenario_network; do $PY -m py_compile scripts_project/$f.py || echo "SYNTAX $f"; done
cd scripts_project && $PY - <<'P'
import sys
from pathlib import Path
from phase4_static import config
for s in ("integrated","disconnected","no_new_xb"):
    c=config(Path(".."),s); R=c["research"]
    print(s,R["scenario"],R["cross_border"]["stock_mode"],R["liquids"]["structure"],R["bunkers"]["attribution"],R["s2"]["demand"]["ev_structure"],R["s2"]["industry"]["v3"]["case"])
P
cd .. ; ls -la /home/jin/wt_dfx_v3_20261026/results_project 2>/dev/null | head -8; git status --short | grep -v "^??" | cut -c1-70 | head -20
