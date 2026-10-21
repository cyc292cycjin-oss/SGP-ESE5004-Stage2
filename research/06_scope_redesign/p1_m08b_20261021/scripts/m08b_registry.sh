#!/bin/bash
# M08b: registry rows (m08b_data.py) + reassembly (d1_registry.py); prints row count and SHA256
cd /home/jin/wt_m08b_20261021/scripts_project || exit 1
export PYTHONHASHSEED=0
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
$PY m08b_data.py 2>&1 | tail -5; echo "m08b_data exit=${PIPESTATUS[0]}"
$PY d1_registry.py > /tmp/m08b_reg.log 2>&1; echo "d1_registry exit=$?"
grep -E 'DATA_PENDING|Traceback|Error' /tmp/m08b_reg.log | tail -3
sha256sum ../research_inputs/registry_v5/DATA_REGISTRY.csv
grep -c '' ../research_inputs/registry_v5/DATA_REGISTRY.csv
