#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W/scripts_project
grep -q '"v3"' d1_registry.py || $PY - <<'P'
from pathlib import Path
f=Path("d1_registry.py"); t=f.read_text()
i=t.index("FRAGMENTS = ["); j=t.index("]",t.index("potentials_",i))
t=t[:j]+', "v3"'+t[j:]
f.write_text(t)
P
sed -n "$(grep -n 'FRAGMENTS = ' d1_registry.py | head -1 | cut -d: -f1),+5p" d1_registry.py | grep -c '"v3"'
$PY v3_data.py 2>&1 | tail -3
cp ../research_inputs/registry_v5/DATA_REGISTRY.csv /tmp/reg_before.csv
$PY d1_registry.py 2>&1 | tail -4
wc -l /tmp/reg_before.csv ../research_inputs/registry_v5/DATA_REGISTRY.csv
sha256sum ../research_inputs/registry_v5/DATA_REGISTRY.csv
git -C .. status --short | cut -c1-100 | head -12
EOF
